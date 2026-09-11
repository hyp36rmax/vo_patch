# Twin-Stick Controller Profile Testing Methodology

[Controller documentation](README.md)

This working procedure derives from the Tanita and Xbox 360 HORI characterization
records and will inform future community profile requests. Preserve the hardware
record even when the implementation selects only one Windows interface.

Keep **OBSERVED** measurements, **IMPLEMENTED** translation rules and **VALIDATED**
game behavior distinct. Record the interface, units, button-numbering convention
and test configuration with each result; do not turn missing results into passes.

## 1. Hardware identification

Record manufacturer, product, exact platform/version, known model number,
connection type and any adapter/PCB. Include firmware where known. For two units,
label them A and B and record each identity separately. Mark absent fields Unknown;
do not substitute a similar product's specifications.

## 2. Windows device identification

Use Device Manager to retain the following fields when available:

| Field | Required detail |
| --- | --- |
| Device Description | Exact displayed text |
| Hardware IDs | VID, PID, revision and collection/interface identifier |
| Usage Page / Usage | Numeric values and names |
| Driver | Provider; version where available |
| Bus-reported description | Exact useful value, or Not exposed |

Keep collection/interface identifiers such as Col01 or IG_00 distinct from device
instances. Redact instance-specific paths before publishing evidence.

## 3. API and controller presentation

Identify XInput, HID and DirectInput/legacy Windows presentations separately,
including the utility and API where known. A device appearing in `joy.cpl` does
not prove one specific API. When multiple views exist, characterize each rather
than assuming equivalent axes, trigger handling or button numbering.

## 4. Neutral axes

Release all controls and record **every exposed axis**, its neutral value and
any visible variation. Record native behavior before calibration unless calibration
is known to be required; if used, retain both the reason and calibration state.
Distinguish raw integers, signed values and normalized percentages.

## 5. Cardinal directions

Move each lever independently left, right, up and down, returning to neutral
between movements. Record the affected axis, minimum, maximum, polarity and
neutral. Note exposed axes that do not respond, without assigning them a purpose.

| Lever / direction | Interface / axis | Minimum | Neutral | Maximum | Unit / polarity |
| --- | --- | --- | --- | --- | --- |
| Record each tested direction | Record | Record | Record | Record | Raw or display scale |

## 6. Diagonals

Test Up+Right on each lever at minimum; preferably add Up+Left, Down+Right and
Down+Left. Verify that both relevant axes report simultaneously and record their
values, variation and return to neutral. Name the tested diagonal rather than
claiming coverage of all combinations from one result.

## 7. Buttons

Press every physical control individually and record the exact logical input.
State whether numbering begins at zero or one; keep HID usages distinct from a
utility's button labels. Use an annotated photograph when surface names are
ambiguous. Explicitly record multiple physical buttons sharing one logical report.
For exposed buttons without an identified surface control, write
**Unassigned / unidentified**; do not invent a function.

## 8. Simultaneous inputs

| Test | Check |
| --- | --- |
| Both levers | Independent simultaneous directions |
| Both triggers | Both inputs remain available; compare API views if one uses a shared axis |
| Both dash/turbo buttons | Both inputs report together |
| Trigger + lever | Neither input suppresses the other |
| Dash + lever | Direction remains available with dash |
| Simultaneous P1/P2, when available | Inputs remain isolated to their assigned players |

Record actual combinations and results; single-input measurements cannot establish
simultaneous behavior.

## 9. POV/hat

Record Up, Down, Left, Right and neutral, including the numeric values and scale.
Test diagonals where supported and distinguish a POV/hat from XInput D-pad bits.

## 10. Multiple devices

When two identical controllers are available:

1. Connect both and verify two independent device instances, not merely two HID collections.
2. Operate A alone, B alone and both simultaneously.
3. Assign each to P1 and P2, then reverse the assignments.
4. Disconnect/reconnect in different orders and record whether device ordering changes.
5. Check whether held input clears, ownership changes or a different controller takes over.

Record connection order, ports, adapters and profile pair. Keep dual-unit status
**Pending** when only one device has been tested, even if two are owned or software
supports two sources. Test mixed-controller configurations separately.

## 11. Game validation

Record the game edition/executable identity and exact patch build or commit when
available. Run on the implemented profile and retain distinct results for:

| Area | Checks |
| --- | --- |
| Selection | Profile detection or manual selection; intended physical controller |
| Player positions | P1 operation and P2 operation as separate tests |
| Levers | Cardinals, diagonals and neutral |
| Combat | Triggers, dash/turbo and relevant simultaneous combinations |
| Menus | Pause, accept, navigation and camera behavior |
| Remapping, if provided | Manual and physical capture, save/relaunch, Cancel and defaults |
| Multiple controllers | Mixed profiles, independent ownership and simultaneous local VS |
| Reconnection | Input release and assignment after reconnect in different orders |

For fixed profiles, mark remapping **Not applicable**, not failed. Repeat relevant
game tests after input-path changes; record which older measurements remain
hardware characterization rather than current-build acceptance.

## 12. Validation status

Statuses describe different kinds of evidence, not a single pass ladder.

| Status | Use |
| --- | --- |
| Observed | Direct device/Windows report with its measurement context |
| Characterized | A documented set of hardware measurements; name incomplete areas |
| Implemented | A code path exists; does not imply a hardware pass |
| Functionally Tested | Named behavior exercised on hardware in the game or relevant input test |
| 1P Validated | Explicit successful P1 operation |
| 2P Validated | Explicit successful P2 operation |
| Community Tested | External result with contributor, configuration and evidence; retain the actual outcomes |
| Pending | Identified acceptance test awaiting execution |
| Not Tested | Test has not been performed |
| Not recorded | Available evidence does not establish whether the specific test occurred |
| Not applicable | Feature or interface is outside this profile |

Use **VALIDATED** only for behavior physically exercised against the reported
build. Software tests, specifications and a general “works” report do not establish
every player position or reconnect permutation. Keep functional confirmation while
marking those detailed results independently.

## 13. Evidence retention

Retain enough evidence to reproduce nontrivial findings; screenshots are not
required for every result.

| Evidence | Context to retain |
| --- | --- |
| Device Manager screenshots | Identity, collection/interface, driver provider |
| Controller utility screenshots or logs | Utility/version, API, units, neutral and activated control |
| Annotated hardware photographs | Exact surface control and duplicate-report relationships |
| Test record | Windows version, date, game edition, patch commit, player position and connected devices |
| Discrepancy note | Both conflicting records, what is unknown, and the specific follow-up measurement |

Do not overwrite measurements to match code. If a utility scale, physical label or
implementation conflicts with another record, retain both and flag the discrepancy
for review before changing a profile or broadening its compatibility claim.
