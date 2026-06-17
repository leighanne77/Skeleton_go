# Northwind Energy — Substation "Alpha" Protection & Topology Reference
> ⚠️ SYNTHETIC / FICTIONAL demo data. Not real infrastructure. Marked CEII for the prototype.
> Classification: CEII · OT-ASSET · entitlement-gated (ceii_cleared, ot_cleared)

## Single-line diagram (summary)
The **single-line diagram** for **Substation Alpha** shows two 230/69 kV transformers
(T1, T2) feeding a ring-bus **substation layout** with feeders F-11…F-14.

## Protection scheme & relay settings
- **Protection scheme:** dual-primary line protection with breaker-failure backup.
- Relay R-401 (line F-12): **relay setting** — pickup 5.0 A, time-dial 0.30 (synthetic).
- Relay R-402 (bus B-2): **relay setpoint** 6.5 A, definite-time 0.20 s (synthetic).
- **Switchgear rating:** 2000 A, 40 kA interrupting (synthetic).

## OT network
- **Network topology:** flat **control network** segment VLAN 30; **SCADA** master polls
  **RTU**-Alpha-01 and two **PLC** controllers over the **IP scheme** 10.30.7.0/24 (synthetic).
- **Firmware version:** RTU 4.2.1 (synthetic).

## Physical security
- **Physical security plan** and **vulnerability assessment** on file (CIP-014); not reproduced here.
