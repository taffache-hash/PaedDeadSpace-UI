from __future__ import annotations

import inspect
from pathlib import Path

import paeddeadspace as pds
import pytest

import ui_logic


def case(**overrides):
    values = {
        "weight_kg": 10.0,
        "age_value": 1.0,
        "age_unit": "years",
        "vt_ml_kg": 8.0,
        "rr_bpm": 20.0,
        "model_key": "user_defined",
        "user_patient_vd_vt": 0.30,
    }
    values.update(overrides)
    return ui_logic.compute_case(**values)


def test_age_conversion_days_months_and_years():
    assert ui_logic.convert_age_to_years(365.25, "days") == pytest.approx(1.0)
    assert ui_logic.convert_age_to_years(18, "months") == pytest.approx(1.5)
    assert ui_logic.convert_age_to_years(2.25, "years") == pytest.approx(2.25)


def test_user_defined_hand_computable_case():
    result = case(apparatus_ds_ml=30.0)
    assert result["status"] == "ok"
    state = result["state"]
    comparison = result["comparison"]
    assert state["vt_ml"] == pytest.approx(80.0)
    assert state["patient_vd_ml"] == pytest.approx(24.0)
    assert state["total_vd_ml"] == pytest.approx(54.0)
    assert state["alveolar_vt_ml"] == pytest.approx(26.0)
    assert comparison["rr_required_bpm"] == pytest.approx(1120.0 / 26.0)
    assert comparison["relative_co2_burden"] == pytest.approx(
        comparison["rr_multiplier"]
    )


def test_numa_fletcher_components():
    result = case(model_key="numa_fletcher", user_patient_vd_vt=None)
    assert result["status"] == "ok"
    state = result["state"]
    assert state["patient_vd_ml"] == pytest.approx(17.27)
    assert state["patient_airway_dead_space_ml"] == pytest.approx(10.3)
    assert state["patient_alveolar_dead_space_ml"] == pytest.approx(6.97)
    assert state["patient_alveolar_tidal_volume_ml"] == pytest.approx(69.7)


def test_numa_extrapolation_warning_is_captured_and_deduplicated():
    result = case(
        model_key="numa_fletcher",
        user_patient_vd_vt=None,
        age_value=0,
        age_unit="days",
    )
    assert result["status"] == "ok"
    assert len(result["warnings"]) == 1
    assert "Numa intrathoracic component" in result["warnings"][0]


def test_pearsall_outside_domain_warning_is_captured():
    result = case(
        model_key="pearsall",
        user_patient_vd_vt=None,
        age_value=4,
        age_unit="years",
    )
    assert result["status"] == "ok"
    assert len(result["warnings"]) == 1
    assert "outside the Pearsall named benchmark context" in result["warnings"][0]


def test_zero_apparatus_has_unit_burden_and_multiplier():
    result = case(apparatus_ds_ml=0.0)
    assert result["status"] == "ok"
    assert result["comparison"]["relative_co2_burden"] == pytest.approx(1.0)
    assert result["comparison"]["rr_multiplier"] == pytest.approx(1.0)
    assert result["apparatus_components"] == ()


def test_nonphysical_case_returns_model_breakdown():
    result = case(apparatus_ds_ml=60.0)
    assert result["status"] == "model_breakdown"
    assert result["message"] == ui_logic.BREAKDOWN_MESSAGE
    assert result["partial"]["vt_ml"] == pytest.approx(80.0)
    assert result["partial"]["patient_vd_ml"] == pytest.approx(24.0)
    assert result["partial"]["apparatus_vd_ml"] == pytest.approx(60.0)
    assert result["partial"]["total_vd_ml"] == pytest.approx(84.0)
    assert "comparison" not in result


def test_missing_model_selection_is_clean_validation_error():
    result = case(model_key=None)
    assert result["status"] == "validation_error"
    assert "select a patient dead-space model" in result["error"]


def test_apparatus_provenance_and_qualification_are_retained():
    qualification = "Manufacturer internal/geometric volume"
    result = case(
        apparatus_ds_ml=12.0,
        apparatus_name="Connector",
        apparatus_qualification=qualification,
    )
    component = result["apparatus_components"][0]
    assert component.provenance.classification is pds.ParameterClassification.USER_DEFINED
    assert component.qualification == qualification
    assert result["apparatus"]["qualification"] == qualification
    assert "does not convert" in component.provenance.context


def test_williams_reference_is_descriptive_and_not_a_model():
    reference = ui_logic.get_williams_term_infant_reference()
    assert reference["accepted_as_computational_model"] is False
    assert reference["values"]["Physiologic dead space"] == {
        "median": 3.5,
        "iqr": (2.8, 4.3),
        "unit": "mL/kg",
    }
    result = case(model_key="williams")
    assert result["status"] == "validation_error"


def test_ui_logic_exposes_no_absolute_paco2_calculation():
    source = inspect.getsource(ui_logic).lower()
    assert "baseline_calibrated_paco2" not in source
    assert not any(
        "paco2" in name.lower()
        for name, value in vars(ui_logic).items()
        if callable(value)
    )


def test_no_openai_import_or_runtime_dependency():
    root = Path(__file__).resolve().parents[1]
    for relative in ("app.py", "ui_logic.py"):
        source = (root / relative).read_text(encoding="utf-8").lower()
        assert "import openai" not in source
        assert "from openai" not in source
    requirements = (root / "requirements-ui.txt").read_text(encoding="utf-8")
    assert "openai" not in requirements.lower()


def test_age_unit_requires_explicit_selection():
    result = case(age_unit=ui_logic.AGE_UNIT_PLACEHOLDER)
    assert result["status"] == "validation_error"
    assert "select an age unit" in result["error"]


def test_pearsall_ui_provenance_does_not_imply_brody_vco2_is_used():
    result = case(
        model_key="pearsall",
        user_patient_vd_vt=None,
        weight_kg=10.0,
        age_value=2.0,
        age_unit="years",
        vt_ml_kg=8.0,
        rr_bpm=20.0,
    )
    provenance = result["provenance"]["model"]
    assert provenance["doi"] == "10.1213/ANE.0000000000000148"
    assert "patient physiologic VD/VT benchmark assumption of 0.30" in provenance["context"]
    assert "does not use the Brody VCO2 equation" in provenance["context"]


def test_vd_vt_fraction_percentage_conversion():
    assert ui_logic.vd_vt_fraction_to_percent(0.675) == pytest.approx(67.5)


def test_alveolar_ventilation_percentage_change():
    assert ui_logic.alveolar_ventilation_percent_change(
        current=750.0,
        baseline=1000.0,
    ) == pytest.approx(-25.0)


def test_vt_composition_chart_data_uses_core_outputs_and_sums_to_vt():
    result = case(apparatus_ds_ml=30.0)
    state = result["state"]
    data = ui_logic.build_vt_composition_chart_data(state)

    assert dict(data) == {
        "Patient-only VD": state["patient_vd_ml"],
        "Apparatus VD": state["apparatus_vd_ml"],
        "Alveolar VT": state["alveolar_vt_ml"],
    }
    assert sum(value for _, value in data) == state["vt_ml"]


def test_vt_composition_rejects_nonphysical_chart_data():
    with pytest.raises(ValueError):
        ui_logic.build_vt_composition_chart_data(
            {
                "vt_ml": 80.0,
                "patient_vd_ml": 24.0,
                "apparatus_vd_ml": 60.0,
                "alveolar_vt_ml": -4.0,
            }
        )


def test_alveolar_ventilation_chart_data_preserves_baseline_and_current():
    result = case(apparatus_ds_ml=30.0)
    data = ui_logic.build_alveolar_ventilation_chart_data(
        result["comparison"]["baseline_alveolar_ve_ml_min"],
        result["state"]["alveolar_ve_ml_min"],
    )
    assert data == (
        (
            "No added apparatus",
            result["comparison"]["baseline_alveolar_ve_ml_min"],
        ),
        ("Current", result["state"]["alveolar_ve_ml_min"]),
    )


def test_presentation_helpers_do_not_call_or_reimplement_core_calculators():
    helpers = (
        ui_logic.vd_vt_fraction_to_percent,
        ui_logic.alveolar_ventilation_percent_change,
        ui_logic.build_vt_composition_chart_data,
        ui_logic.build_alveolar_ventilation_chart_data,
    )
    source = "\n".join(inspect.getsource(helper) for helper in helpers)
    assert "pds." not in source
    for core_call in (
        "calculate_ventilation(",
        "calculate_tidal_volume_ml(",
        "patient_dead_space_excluding_apparatus_ml(",
        "total_dead_space_ml(",
        "alveolar_tidal_volume_ml(",
        "alveolar_minute_ventilation_ml_min(",
        "relative_co2_burden(",
        "rr_required_to_preserve_alveolar_ventilation(",
    ):
        assert core_call not in source


def test_pearsall_10kg_golden_case_regression():
    result = ui_logic.compute_case(
        weight_kg=10.0,
        age_value=2.0,
        age_unit="years",
        vt_ml_kg=8.0,
        rr_bpm=20.0,
        model_key="pearsall",
        user_patient_vd_vt=None,
        apparatus_ds_ml=30.0,
        apparatus_name="User-entered apparatus",
        apparatus_qualification="User estimate / uncertain",
    )
    assert result["status"] == "ok"
    state = result["state"]
    comparison = result["comparison"]
    assert state["vt_ml"] == pytest.approx(80.0)
    assert state["patient_vd_ml"] == pytest.approx(24.0)
    assert state["apparatus_vd_ml"] == pytest.approx(30.0)
    assert state["total_vd_ml"] == pytest.approx(54.0)
    assert state["total_vd_vt"] == pytest.approx(0.675)
    assert state["alveolar_vt_ml"] == pytest.approx(26.0)
    assert state["alveolar_ve_ml_min"] == pytest.approx(520.0)
    assert comparison["baseline_alveolar_ve_ml_min"] == pytest.approx(1120.0)
    assert comparison["current_to_baseline_alveolar_ve_ratio"] == pytest.approx(520.0 / 1120.0)
    assert comparison["relative_co2_burden"] == pytest.approx(1120.0 / 520.0)
    assert comparison["rr_required_bpm"] == pytest.approx(1120.0 / 26.0)
    assert comparison["rr_multiplier"] == pytest.approx((1120.0 / 26.0) / 20.0)
