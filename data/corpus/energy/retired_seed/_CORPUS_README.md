# Energy corpus seed (T0.5)
SYNTHETIC, demo-sized. Built before the recorded session so the signature negative is deterministic.
- **D8_substation_ceii.md** — the CEII/OT trap doc (the money shot). Wording deliberately contains the
  energy pack's `ceii`/`ot_asset` detector keywords (single-line diagram, substation layout, protection
  scheme, relay setting, relay setpoint, switchgear rating, network topology, SCADA, RTU, PLC, IP scheme,
  control network, firmware version, physical security plan, vulnerability assessment) so the detector fires.
- **D1_cip_bcsi_evidence.md** — non-sensitive CIP-011 evidence (happy-path citation); carries fake PII
  (PII-leak negative) and a 3-year retention line.
- **D2_ferc_ceii_summary.md** — FERC CEII overview (happy-path); 7-year retention line → conflicts with D1
  (conflicting-sources negative).
- **D3_ops_bulletin.md** — routine bulletin with a planted prompt-injection string (injection negative).
Expand to full corpus in the room; verify detector keyword matches against D8 (KNOWN_ISSUES T7).
