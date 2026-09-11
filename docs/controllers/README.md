# Controller Hardware Documentation

Controller profiles are developed from physical hardware characterization. These
records preserve what each device presents to Windows independently of the input
path used by `vo_patch`; the [root README](../../README.md) provides the project overview.

| Evidence class | Meaning |
| --- | --- |
| **OBSERVED** | What the physical controller or Windows reports, including the interface and measurement scale |
| **IMPLEMENTED** | How the inspected code consumes, translates or assigns those inputs |
| **VALIDATED** | Behavior exercised on hardware against the reported test build |

The maintainer reports functional hardware testing on the latest internal build,
including Custom remapping/reassignment and corrected Tanita top controls. Its
exact tested commit, Windows version and utility versions were not supplied.
Implementation references were inspected at `ed2b861`; controller code is unchanged
from `ff75c05`. A functional confirmation does not establish an undocumented
player position or a two-identical-controller result.

| Record | Characterized | Implemented | Functionally Tested | 1P Validated | 2P Validated |
| --- | --- | --- | --- | --- | --- |
| [Twin-Stick (Custom)](custom-twinstick.md) | Brook/XInput reference layout | Yes | Yes | Yes | Yes |
| [Tanita Twin-Stick](tanita-twinstick.md) | Single-unit measurements; dual-unit game test | Yes | Yes | Yes | Yes |
| [HORI Twin Stick EX — Xbox 360](hori-twinstick-ex-x360.md) | Single unit; XInput and legacy presentation | Yes | Yes | Yes | Yes |
| [Controller Profile Testing Methodology](profile-testing-methodology.md) | Working procedure | — | — | — | — |

**Not recorded** identifies a missing specific result, not a failure of the tested
hardware. Dual-Tanita local versus is **Functionally Tested**, with both player
positions validated. Dual-HORI testing remains **Pending**. The HORI P2 result
includes another connected controller; its model and a simultaneous local VS test
were not recorded.

The profile records separate measurements, implementation decisions and acceptance
results. [Controller internals](../CONTROLLERS.md) contains executable dispatch
addresses and automated-test coverage; the [methodology](profile-testing-methodology.md)
defines the evidence needed for additional hardware and future community reports.
