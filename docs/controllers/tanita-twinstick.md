# Tanita Twin-Stick

[Controller documentation](README.md) · [Testing methodology](profile-testing-methodology.md)

## Hardware and Windows identity — OBSERVED

| Field | Value |
| --- | --- |
| VID / PID / revision | `1F4F` / `9001` / `0200` |
| Hardware ID | `HID\VID_1F4F&PID_9001&REV_0200&Col01` |
| Additional HID identity | `HID\VID_1F4F&UP:0001_U:0005` |
| Device description | HID-compliant game controller |
| Driver stack | Standard Microsoft HID stack |
| Usage page / usage | `0x01` Generic Desktop / `0x05` Game Pad |
| Bus-reported device description | No useful description exposed during testing |
| Exact model number, Windows version, utility/version | Not recorded |

The retained diagnostic `controller-diagnostic-20260910-075347.txt` identifies
Col01 and Col02, with one usable native unit. Device-instance paths are omitted
from this record. Collection enumeration alone does not establish two controllers.

## Axes and diagonals — OBSERVED

Percentages are test-utility display values. The diagnostic separately records
raw axis neutral `128` and endpoints `0`/`255`; these scales are not interchangeable.

| Lever | Axis | Negative direction | Neutral | Positive direction |
| --- | --- | --- | --- | --- |
| Left | X Axis | Left: 0% | 50% | Right: 100% |
| Left | Y Axis | Up: 0% | 50% | Down: 100% |
| Right | Z Axis | Left: 0% | 50% | Right: 100% |
| Right | Z Rotation | Up: 0% | 50% | Down: 100% |

X Rotation and Y Rotation were exposed by the utility but did not correspond to
lever controls in this characterization; they are unused/not required for the
current profile.

| Diagonal test | Simultaneous values | Result |
| --- | --- | --- |
| Left lever Up+Right | X 100%, Y 0% | PASS; no unwanted percentage movement/wiggle in the tested condition |
| Right lever Up+Right | Z 100%, Z Rotation 0% | PASS; no unwanted percentage movement/wiggle in the tested condition |
| Other diagonal combinations | Individual results not supplied | Not recorded |

The tested diagonals establish that both axes of each lever can report
simultaneously; they do not establish an unmeasured noise tolerance or deadzone.

## Buttons and POV — OBSERVED

Numbers use the characterization's **zero-based** convention. HID usages are
one-based; the reader subtracts one when constructing its button mask.

| Button | Physical control |
| --- | --- |
| 0 | Square |
| 1 | Cross |
| 2 | Circle |
| 3 | Triangle |
| 4 | Left Trigger |
| 5 | Right Trigger |
| 6 | Left Stick Press |
| 7 | Right Stick Press |
| 8 | Share |
| 9 | Options |
| 10 | Left lever auxiliary/top controls |
| 11 | Right lever auxiliary/top controls |
| 12 | PS |

**Two physical auxiliary/top controls on the left lever both report Button 10;
two on the right lever both report Button 11.** This is a hardware observation,
not a choice made by the patch. A shared logical report cannot identify which
physical control produced it.

| POV direction | Diagnostic value |
| --- | --- |
| Up | 0 |
| Right | 2 |
| Down | 4 |
| Left | 6 |
| Neutral | 8 |

### Button identity review

The physical characterization above assigns top/auxiliary controls to 10/11 and
stick presses to 6/7. The September 10 diagnostic contains presses of 6 and 7
during the top-control investigation, but no 10/11 presses. It does not label
which physical surface was pressed for each sample.

The current source comment calls 6/7 “top switches,” which conflicts with the
characterization's physical labels. Preserve both records: do not relabel 10/11
or infer that the duplicated auxiliary controls changed identity. An annotated
per-surface capture would resolve the attribution; the current implementation
accepts both button pairs for dash. This documentation task does not change code.

## Native input path — IMPLEMENTED

Native HID axes/buttons → profile normalization → existing Virtual-On digital
Twin-Stick lever semantics. Analog reports are input sources; game movement is
not converted to analog movement.

[The reader](../../input/tanita.c) requires the exact VID/PID/revision and Game Pad
collection, then locates X, Y, Z, Rz and hat values by HID usage. It accepts a
button range beginning at usage 1 through at least 13 in the same report and
rejects incomplete or ambiguous layouts. It does not require a particular Col01
path string or install a virtual XInput driver.

| Input | Translation in `tanita_map.h` |
| --- | --- |
| X / Z | Left / right normalized horizontal axis |
| Y / Rz | Inverted to the positive-up convention used by the lever engine |
| Axis range | Below 25% → one full direction; above 75% → the opposite; inclusive middle half → neutral |
| Buttons 4 / 5 | Left / right trigger, normalized to 255 while pressed |
| Buttons 6 / 7 | Left / right shoulder (dash), plus the original normalized stick-click bits |
| Buttons 10 / 11 | Left / right shoulder (dash) aliases |
| Buttons 0 / 1 / 2 / 3 | X / A / B / Y normalized face-button bits |
| Buttons 8 / 9 | Back/camera / Start-pause (Share / Options) |
| Button 12 | No gameplay mapping |
| POV | D-pad bits, including supported diagonal combinations and neutral |

The fixed profile uses normalized left/right levers, triggers and shoulders in
[the shared lever routine](../../asm/twinstick.asm); dash clears the corresponding
active-low `0x02` lever bit. The profile does not expose Custom's remapping editor.

Each of up to two native device paths owns its descriptor, report buffer,
overlapped read and cached state. Paths are reserved for the process; disconnecting
one does not promote the other. Explicit Options selection assigns a native
source to P1 or P2 independently of XInput slots. After a detected disconnect,
reselect in F7; changing ports after both native path reservations are occupied
requires restarting. Two-source implementation is not a dual-unit hardware result.

## Validation record

The maintainer confirms lever movement, diagonals and top controls functioning in
the latest internal build. Detailed player-position results were not supplied.

| Test | Status | Retained evidence / scope |
| --- | --- | --- |
| Device recognition | Functionally Tested | Exact native unit recognized; one usable unit in diagnostic |
| Neutral axes | Observed / Functionally Tested | 50% display, raw 128; neutral returns in diagnostic |
| Full axis range | Characterized | 0–100% endpoints; raw 0/255 samples, not a continuous precision sweep |
| Left cardinal directions | Functionally Tested | Characterization and game movement confirmation |
| Right cardinal directions | Functionally Tested | Characterization and game movement confirmation |
| Left diagonal | Functionally Tested | Up+Right characterization; game diagonal confirmation |
| Right diagonal | Functionally Tested | Up+Right characterization; game diagonal confirmation |
| Trigger inputs | Functionally Tested | Both triggers reported working |
| Auxiliary/top controls | Functionally Tested | Latest game confirmation; per-surface report attribution flagged above |
| Remapping | Not applicable | Fixed profile; no remapping UI |
| P1 assignment | Not recorded | Implemented; no explicit P1 test result retained |
| P2 assignment | Not recorded | Implemented; no explicit P2 test result retained |
| Dual Tanita | Pending / Not Yet Validated | No two-physical-unit test supplied |
| Mixed-controller configuration | Not recorded for Tanita specifically | General ownership confirmation does not identify this combination |

[Mapping source](../../input/tanita_map.h), [ownership](../../input/controller.c)
and [software checks](../../tools/tanitatest.py) provide implementation evidence;
they do not replace the hardware results above.
