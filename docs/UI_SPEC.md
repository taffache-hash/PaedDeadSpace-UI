# PaedDeadSpace Streamlit UI v1.0.0 — specification

## Purpose

The UI is a local educational/exploratory interface around the installed, audited `paeddeadspace` core. It is not patient-specific clinical decision support and does not provide recommendations or define clinical thresholds.

The wrapper contains presentation and orchestration only. Scientific equations, model semantics, provenance classifications, source-domain logic, warnings, and scientific validation remain in the read-only core.

## Visual hierarchy

1. A compact top area presents the product title and the educational and local-runtime notices.
2. Inputs are grouped in a clearly titled **Case inputs** expander.
3. The input workflow remains explicit and uses a Streamlit form with a **Calculate** action.
4. After calculation, **RESULTS** are visually dominant. Successful results begin with:
   - the selected patient dead-space model and its status;
   - a compact case summary containing weight, age, absolute VT, entered VT/kg, RR, selected model, and apparatus dead space.
5. Warnings and provenance are never suppressed. Core source-domain warnings appear above result metrics, and full source context remains available in **Sources & provenance**.
6. No traffic-light colors, risk bands, target zones, or safe/unsafe/normal/recommended labels are added.

## Input workflow

- Weight is required and initially blank.
- Age value is required and initially blank.
- Age unit requires explicit selection; no age unit is preselected.
- VT in mL/kg is required and initially blank.
- RR is required and initially blank.
- The patient dead-space model requires explicit selection.
- User-defined patient VD/VT is shown and required only in user-defined mode.
- User-defined patient VD/VT explicitly excludes apparatus.
- Apparatus dead space may default to 0 mL.
- Apparatus name and qualification remain visible.
- Manufacturer internal/geometric volume is not converted to functional dead space.
- No golden-test patient values are auto-filled.

## Model-specific presentation

### User-defined

The entry is patient physiologic VD/VT only. ETT, connector, sensor, filter, circuit, and other apparatus dead space must be excluded and entered separately.

### Numa–Fletcher

The mode is labeled as a **reference / sensitivity construction**, not a healthy or clinical default. When available, the UI displays the core-provided intrathoracic component, alveolar tidal volume used by the construction, alveolar component, and patient-only total.

### Pearsall

The mode is labeled **benchmark only**. The displayed patient VD/VT assumption is 0.30 and excludes apparatus. Provenance display is scoped to those benchmark semantics; no VCO2 calculation is activated.

### Williams

Williams term-infant values remain in a collapsed descriptive-reference expander. They are never offered as a model and are never auto-applied.

## Results structure

For a physical state, output is separated into three sections.

### VOLUMES

- Absolute VT, mL
- Patient-only VD, mL
- Apparatus VD, mL
- Total VD, mL
- Alveolar VT, mL

### VENTILATION

- Total VD/VT as a fraction
- Total VD/VT as a percentage
- Alveolar minute ventilation, mL/min
- Baseline alveolar minute ventilation, mL/min
- Current / baseline alveolar ventilation
- Descriptive percentage change versus the no-added-apparatus baseline

The VD/VT fraction and percentage are explicitly identified as the same output in two forms.

### APPARATUS EFFECT

- Apparatus DS / VT, %
- Relative CO2 burden
- RR required to preserve baseline alveolar ventilation
- RR multiplier

The UI states that, under fixed-VCO2 one-compartment assumptions, relative CO2 burden and RR multiplier are algebraically identical and are not independent evidence. No absolute PaCO2 is calculated.

## Visualizations

### Current tidal-volume composition

A horizontal stacked bar displays the current core outputs for:

- patient-only VD;
- apparatus VD;
- alveolar VT.

The supplied segments are verified to sum to absolute VT. Values in mL are shown nearby. The caption identifies the segments as model-derived outputs rather than independently measured quantities. The chart is omitted for model-breakdown states.

### Alveolar ventilation comparison

A compact default-style bar chart compares:

- the same model with no added apparatus;
- the current state.

The numerical percentage change is labeled **Change vs no-added-apparatus baseline**. The chart is descriptive and is not a target graph.

Both charts are visualizations of the **same scientific-core outputs already shown numerically**. They are not extra evidence, independent observations, additional physiological models, or new calculations of patient state.

## Warnings and model boundaries

- Core `SourceDomainWarning` messages are captured, deduplicated, and displayed even when calculation succeeds.
- Core validation failures are shown without a traceback.
- `NonPhysicalStateError` produces a prominent model-breakdown message.
- No preservation-RR estimate is displayed after model breakdown.
- Available partial volumes are retained for transparency.
- Composition and alveolar-ventilation charts are not drawn in a nonphysical state.
- The `VD >= VT` boundary is described as a mathematical one-compartment boundary, not a clinical threshold.

## Sources, provenance, and reproducibility

- **Sources & provenance** retains the selected mode, model type, classification, citation, source context, DOI, component evidence, and apparatus provenance where available.
- Apparatus provenance remains `USER_DEFINED`.
- A software expander shows the installed `paeddeadspace` distribution version using package metadata when available.
- Failed metadata lookup is displayed as `version unavailable`; no core version is invented.
- The UI label is `PaedDeadSpace UI v1.0.0`.
- The UI states that calculations are local and no external API is used.

## Scientific and software boundaries

- No duplicated physiological equations in `app.py` or presentation helpers.
- No hidden patient weight, age, VT, RR, or physiologic VD/VT default.
- No disease mode.
- No absolute PaCO2 output.
- No patient-identifying fields, persistence, database, or session export.
- No network calls, external APIs, OpenAI runtime dependency, telemetry code, or cloud deployment code.
- No modelling of dynamic rebreathing, leaks, capnogram shape, flow-dependent washout, compressible volume, compliance, valve timing, or heterogeneous gas exchange.
- No conversion between apparatus geometric volume and functional dead space.
- No recommendation engine or clinical interpretation layer.

## Intended three-product architecture

1. **`PaedDeadSpace-Core`** — scientific Python engine, provenance, tests, and validation.
2. **`PaedDeadSpace-UI`** — Streamlit presentation depending on a released Core version.
3. **`PaedDeadSpace-Windows`** — separately packaged Windows executable distribution built from released Core and UI versions.

The UI repository must not duplicate Core equations. The Windows executable is not built in this revision.

## Architecture and testing

- `app.py` is the Streamlit presentation layer.
- `ui_logic.py` retains audited validation, age conversion, core object construction, core calls, baseline comparison, warning capture, structured status results, and provenance extraction.
- Small presentation helpers convert display units and package existing core outputs for charts.
- Tests import `ui_logic.py` directly and do not require browser rendering.
- The installed `paeddeadspace` package remains the sole scientific source of truth.
