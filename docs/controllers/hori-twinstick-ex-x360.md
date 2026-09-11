# HORI Twin Stick EX - Xbox 360

[Controller documentation](README.md) · [Testing methodology](profile-testing-methodology.md)

## Hardware and Windows presentation — OBSERVED

| Field | Value |
| --- | --- |
| Product / platform | HORI Twin Stick EX / Xbox 360 |
| VID / PID | `1BAD` / `FF00` |
| Hardware ID | `HID\VID_1BAD&PID_FF00&IG_00` |
| Usage | Generic Desktop / Game Pad |
| Presentations examined | XInput and legacy Windows controller presentation |
| Legacy device name | `Controller (TWINSTICKEX)` |
| Revision, exact model number, driver version | Not recorded |
| Windows and test utility versions | Not recorded |

These findings apply to the Xbox 360 unit, not the PlayStation HORI Twin Stick EX.
The legacy presentation is retained as a hardware record even though the profile
uses XInput. A Windows controller panel alone does not prove which API a utility
uses to obtain its values.

## XInput characterization — OBSERVED

| Physical control | Reported input |
| --- | --- |
| Left lever | D-pad |
| Right lever | Right Thumb X / Right Thumb Y |
| Left / right trigger | LT / RT |
| Left / right button | Left Shoulder (LB) / Right Shoulder (RB) |
| A / B / X / Y | A / B / X / Y |
| Back / Start | Back / Start |

| Right-lever axis | Direction at 0% | Neutral | Direction at 100% |
| --- | --- | --- | --- |
| Right Thumb X | Left | 50% | Right |
| Right Thumb Y | Up | 50% | Down |

These are utility percentages, not raw signed `XInputGetState` samples. Raw Y
polarity cannot be derived from the displayed percentage convention alone.

| Combination / return test | Result |
| --- | --- |
| Left-lever diagonal | PASS |
| Right-lever diagonal | PASS |
| Simultaneous LT + RT | PASS |
| Simultaneous LB + RB | PASS |
| Release right lever | Returns to centre |

The supplied results do not enumerate every diagonal direction separately.

## Legacy `Controller (TWINSTICKEX)` characterization — OBSERVED

Active stick/trigger axes were approximately 50% at neutral. Left-lever directions
use the Hat Switch.

| Physical input | Legacy axis | One extreme | Neutral | Other extreme |
| --- | --- | --- | --- | --- |
| Right lever horizontal | X Rotation | Left: 0% | 50% | Right: 100% |
| Right lever vertical | Y Rotation | Up: 0% | 50% | Down: 100% |
| Triggers | Shared Z Axis | Left Trigger: ~99% | ~50% | Right Trigger: ~1% |

| Logical button | Physical control |
| --- | --- |
| 0 | A |
| 1 | B |
| 2 | X |
| 3 | Y |
| 4 | Left Button |
| 5 | Right Button |
| 6 | Back |
| 7 | Start |
| 8 | Unassigned / unidentified |
| 9 | Unassigned / unidentified |

Buttons 8 and 9 are exposed, but no corresponding surface controls were identified.
No purpose is inferred. The result of pressing both triggers together on the
legacy shared Z axis was not supplied; it must not be inferred from the individual
extremes or the separate XInput simultaneous-trigger test.

## Profile decisions — IMPLEMENTED

| Input path property | XInput used by the profile | Legacy record |
| --- | --- | --- |
| Triggers | Independent LT/RT values | Shared Z axis |
| Dash controls | Normal LB/RB shoulder bits | Buttons 4/5 |
| Left lever | Direct D-pad bits | Hat Switch |
| Right lever | Direct right-thumb axes | X/Y Rotation |

XInput supplies the independent triggers and direct controls required by the
fixed profile without reconstructing them from the legacy representation.
[HORI bindings](../../asm/twinstick.asm) map D-pad to the left lever, right
thumbstick to the right lever, LT/RT to weapons and LB/RB to dash. Both triggers
and shoulders can contribute during the same game tick. Back retains camera/zoom;
Start pauses.

The profile treats raw signed XInput Y as positive-up; the utility's 0%-at-up
display is not evidence of a reversed raw axis. Current functional testing confirms
correct direction behavior, but raw signed endpoint measurements are not retained.

Selection is manual in F7; the code does not detect HORI by VID/PID through XInput.
[The ownership helper](../../input/controller.c) reads all four slots and uses a
released-then-pressed Start to claim the intended controller for P1 or P2.
Claims remain per session; detected disconnects require F7 reselection. Compatible
XInput assignments can be swapped without unplugging controllers.

## Validation and preservation status

| Test / configuration | Status | Scope |
| --- | --- | --- |
| Single-unit XInput and legacy characterization | Characterized | Measurements above |
| Movement, triggers, dash, buttons and menu behavior | Functionally Tested | Maintainer reports correct controls and behavior |
| Diagonals, paired triggers/shoulders, neutral return | Functionally Tested | Individual PASS results above |
| P1 operation | 1P Validated | Maintainer confirmation in the controller index |
| P2 operation | 2P Validated | HORI assigned to P2 with another controller connected |
| Mixed-controller connection | Functionally Tested | Other controller's model and simultaneous local VS result not recorded |
| Fixed-profile remapping | Not applicable | No remapping editor for this profile |
| Reconnect permutations / simultaneous local VS | Not recorded individually | General ownership confirmation does not enumerate these cases |
| Dual HORI | Pending / Not Yet Validated | Two units owned; only one available for initial characterization |

Ownership of a second unit is not evidence of a two-unit test. Record the second
unit's identity, both player positions, simultaneous input and reconnect ordering
using the [methodology](profile-testing-methodology.md) before changing dual-HORI status.
