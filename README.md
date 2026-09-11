# Virtual-On PC Controller Expansion

Controller profiles, per-player device selection and remapping for *Cyber Troopers
Virtual-On* (PC, 1997), built on Pairomaniac's [V-On Patcher](https://github.com/pairomaniac/v-on-patcher).

## Overview

The `Controller-Expansion` branch extends the patcher's twin-stick support to
Custom XInput layouts, native Tanita HID and the Xbox 360 HORI Twin Stick EX.
Profiles define how device inputs drive the game's two digital levers; P1 and
P2 select their profiles and controllers independently.

- Preserve upstream control mappings and game behavior, including Back/camera zoom.
- Keep fixed device layouts separate from Custom remapping.
- Assign controllers explicitly rather than deriving player numbers from Windows connection order.
- Restrict new executable patches to builds with verified dispatch sites.

| Executable | Controller Expansion |
| --- | --- |
| English retail / US–Global | Supported |
| Japanese rerelease | Supported |
| USA OEM / Japanese original | Upstream profiles and assignment only |

**Install:** download the Windows ZIP from a successful [Build action](https://github.com/hyp36rmax/vo_patch/actions/workflows/build.yml),
keep its `_internal` directory beside the patcher, and apply **XInput gamepad support**
to a pristine game executable. The patcher installs the supplied 32-bit
`vontanita.dll` beside the game; Python packages must retain their `input` directory.
The helper requires the Windows Universal C Runtime. Back up `v_on.ini` before
restoring or repatching an existing installation.

See the [patcher guide](docs/PATCHER.md) for disc installation, other patches,
restoration and Python usage, or the [developer documentation](docs/README.md)
for building and contributing.

## Controller Profiles

Gamepad (XInput), Keyboard (Simple) and Keyboard (Real) remain available alongside
the four twin-stick profiles below. Fixed profiles do not expose gameplay rebinding;
Custom provides twelve independent action slots.

### Twin-Stick

F7 label: **Twin-stick (XInput)**. The upstream layout maps each thumbstick to
one arcade lever.

| Game input | XInput control |
| --- | --- |
| Left lever | Left thumbstick |
| Right lever | Right thumbstick |
| Left / right trigger | LT / RT |
| Left / right dash | LB / RB |

Lever combinations retain the game's movement, turning, jump and guard behavior;
pressing both triggers fires the centre weapon.

### Twin-Stick (Custom)

[Reference hardware and implementation record](docs/controllers/custom-twinstick.md).

A remappable XInput profile with Xbox/Brook-style defaults:

| Game input | Default XInput control |
| --- | --- |
| Left lever up / down / left / right | D-pad up / down / left / right |
| Right lever up / down / left / right | Y / A / X / B |
| Left / right trigger | LT / RT |
| Left / right dash | LB / RB |

### Twin-Stick (Tanita)

Native HID support for VID `1F4F`, PID `9001`, revision `0200`, Generic Desktop /
Game Pad. See the [Tanita hardware record](docs/controllers/tanita-twinstick.md)
for measured axes, duplicated auxiliary controls and button-report attribution.
Button numbers below are zero-based.

| Game input | HID mapping |
| --- | --- |
| Left / right lever | X–Y / Z–Rz, converted to digital directions |
| Left / right trigger | Buttons `4` / `5` |
| Left / right dash | Buttons `6` / `7`; `10` / `11` retained as aliases |
| Menu navigation | POV hat |
| Accept / pause / camera | Cross / Options / Share |

The profile translates HID axes to the existing digital lever semantics; it does
not add analog game movement.

### Twin-Stick (HORI EX)

Xbox 360 HORI Twin Stick EX, VID `1BAD` / PID `FF00`, selected manually through
XInput. The [hardware record](docs/controllers/hori-twinstick-ex-x360.md) preserves
both XInput and legacy Windows measurements.

| Game input | XInput control |
| --- | --- |
| Left lever | D-pad |
| Right lever | Right thumbstick |
| Left / right trigger | LT / RT |
| Left / right dash | LB / RB |

The PlayStation model is outside the current compatibility claim.

## Player Assignment & Remapping

Select P1 and P2 profiles independently in **F7**; mixed XInput, native Tanita and
keyboard configurations are supported by the routing code. When prompted,
release **Start / Options**, then press it on the controller intended for the
displayed player. Selection considers all four XInput slots or both native
Tanita units, so controllers can remain connected in any initial slot order.

| Assignment event | Behavior |
| --- | --- |
| First use in a game session | Prompt when an eligible, unowned controller is available |
| F7 confirmation / Custom's **Choose controller** | Explicit selection or reassignment |
| Choose the other player's controller | Swap assignments within the same input family; otherwise clear the other claim |
| Detected disconnect | Clear input and invalidate that claim; reselect through F7 after reconnecting |
| Restart | Keep profiles and saved bindings; establish controller ownership again |

Ownership is deterministic **within the session**, not a persistent hardware-ID
mapping across launches. XInput slot numbers are not saved as physical identities.
Native Tanita paths remain reserved for the process; changing USB ports after
both reservations are occupied requires a restart.

For Custom, choose **Next** in F7, focus an action with the mouse or Tab, release
all controls, then press one button or move one lever direction. Capture reads
only that player's selected XInput controller.

| Editor operation | Result |
| --- | --- |
| Capture or dropdown selection | Assign one of 20 inputs: face buttons, shoulders, triggers, thumbstick directions or D-pad directions |
| **None** | Unbind the action |
| Escape, 30-second timeout or disconnect during capture | Retain the current binding; Escape also leaves manual dropdown selection available |
| Held input on entry, chord or diagonal | Require release and a single-input retry |
| **OK** / **Cancel** | Save / discard pending binding edits |
| **Default**, then **OK** | Restore the Custom defaults for that player |

Custom layouts persist separately as `1P Custom Assign` and `2P Custom Assign`
in `v_on.ini`. D-pad gameplay directions can be reassigned while menu navigation
remains available; Start/pause and Back/camera are fixed controls outside the editor.

## Hardware Validation

Compatibility evidence combines device diagnostics, in-game control checks and
software regression tests. Hardware checks cover neutral state, each lever
direction, triggers, dash, simultaneous inputs and menu controls; two-player
checks add isolation, reassignment and reconnect behavior. This records how
original hardware behaves without treating API emulation as a substitute for a
working controller.

The maintainer confirms functional hardware operation, Custom remapping/capture
and controller reassignment in the latest internal build. Detailed player-position
and multi-unit results are tracked separately from that functional confirmation.

| Area | Status |
| --- | --- |
| Tanita movement, triggers and top controls | Functionally Tested |
| Xbox 360 HORI EX controls and P2 operation | Functionally Tested; 2P Validated |
| Custom remapping/capture and controller reassignment | Functionally Tested |
| Dual Tanita / dual HORI | Pending |
| Retail / Japanese rerelease patching | Software checked: 812 patch combinations |

The [controller documentation index](docs/controllers/README.md) separates observed
measurements, implementation decisions and hardware results. See
[controller internals](docs/CONTROLLERS.md) for dispatch evidence and automated checks.

## Additional Hardware

Use the [testing methodology](docs/controllers/profile-testing-methodology.md)
for future community records. Compatibility reports should identify the exact model, platform,
VID/PID/revision and input mode; include neutral and per-control diagnostics,
then check the proposed mapping in-game for both players. Distinguish measured
reports from inferred mappings, and redact device-instance paths before posting
logs. A report does not establish support for other revisions or platform variants.

## Credits

[Pairomaniac](https://github.com/pairomaniac/v-on-patcher) created the upstream
V-On Patcher and its patching, XInput and twin-stick foundation.
[hyp36rmax](https://github.com/hyp36rmax/vo_patch) maintains this Controller Expansion
fork and supplies hardware testing. The project retains the upstream
[MIT license](LICENSE).
