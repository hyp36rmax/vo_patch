# Controller Hardware Documentation

Controller profiles are developed from physical hardware characterization. These
records preserve what each device presents to Windows independently of the input
path used by `vo_patch`; the [root README](../../README.md) provides the project overview.

| Evidence class | Meaning |
| --- | --- |
| **OBSERVED** | What the physical controller or Windows reports, including the interface and measurement scale |
| **IMPLEMENTED** | How the inspected code consumes, translates or assigns those inputs |
| **VALIDATED** | Behavior exercised on hardware against the reported test build |

The maintainer confirms every implemented controller profile is **1P Validated**,
**2P Validated**, and **Functionally Tested** in mixed-controller local VS. This
includes the original XInput/keyboard profiles and all dedicated Twin-Stick
profiles. Identical multi-unit configurations are recorded separately.
Windows and utility versions were not supplied. Raphnet R1 testing and the R2
F7 ordering update extend baseline `e4a2a501dd0f6dd5ca4cf5ac843875199c07662a`.

| Record | Characterized | Implemented | Functionally Tested | 1P Validated | 2P Validated | Mixed local VS |
| --- | --- | --- | --- | --- | --- | --- |
| [Twin-Stick (Custom)](custom-twinstick.md) | Brook/XInput reference layout | Yes | Yes | Yes | Yes | Yes |
| [Tanita Twin-Stick](tanita-twinstick.md) | Single-unit measurements; dual-unit game test | Yes | Yes | Yes | Yes | Yes |
| [HORI Twin Stick EX — Xbox 360](hori-twinstick-ex-x360.md) | Single unit; XInput and legacy presentation | Yes | Yes | Yes | Yes | Yes |
| [Raphnet DC v1](raphnet-dreamcast-twinstick.md) | HKT-7500; buttons on both levers | Yes | Yes | Yes | Yes | Yes |
| [Raphnet Saturn v2](raphnet-saturn-twinstick.md) | HSS-0151; X/Y left, buttons right | Yes | Yes | Yes | Yes | Yes |
| [Controller Profile Testing Methodology](profile-testing-methodology.md) | Working procedure | — | — | — | — | — |

**Not recorded** identifies a missing specific result, not a failure. Dual-Tanita
local VS is **Functionally Tested**. Dual-HORI testing remains **Pending**;
dual identical DC and dual identical Saturn adapters remain **Not Tested**.
Mixed Raphnet DC/Saturn local VS is **Functionally Tested**, with both profiles
also confirmed in each player position. Dreamcast adapter v2 has manufacturer-
documented HKT-7500 support only; local physical validation is **Pending**.

The profile records separate measurements, implementation decisions and acceptance
results. [Controller internals](../CONTROLLERS.md) contains executable dispatch
addresses and automated-test coverage; the [methodology](profile-testing-methodology.md)
defines the evidence needed for additional hardware and future community reports.
