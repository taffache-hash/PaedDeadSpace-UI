# PaedDeadSpace-UI v1.0.0 release audit

## Scope

The v1.0.0 UI is a presentation layer over PaedDeadSpace-Core v1.0.0. Scientific equations are not duplicated in the UI. Release-only changes were limited to version display, About/Citation metadata, repository documentation, and packaging.

## Verified behavior — 18 September 2026

- Python compile check passed for `app.py` and `ui_logic.py`.
- UI-logic test suite passed: **21/21**.
- Final v1.0.0 `app.py` executed through Streamlit's application test runner without exceptions.
- The Pearsall 10-kg golden case reproduced the expected outputs through the final UI runtime: VT 80 mL; patient VD 24 mL; apparatus VD 30 mL; total VD 54 mL; total VD/VT 0.675; alveolar VT 26 mL; alveolar ventilation 520 mL/min; baseline alveolar ventilation 1120 mL/min; relative CO2 burden 2.154; RR required 43.08/min; RR multiplier 2.154.
- Explicit age-unit selection is retained.
- Patient and apparatus dead space remain separate.
- Source-domain warnings and provenance remain visible.
- Williams remains descriptive and is never auto-applied.
- Model-breakdown behavior remains non-prescriptive and suppresses misleading derived outputs.
- No absolute PaCO2 calculation, disease mode, clinical traffic-light interpretation, external API call, or OpenAI runtime dependency was added.

## Visual layer

The compact Matplotlib panels and Streamlit result hierarchy are presentation-only transformations of Core outputs. Screenshot assets for the public README must be captured from the actual tagged v1.0.0 runtime; pre-release images or mock-ups are not substituted.

## Release boundary

The UI is for educational/research use and is not patient-specific clinical decision support.
