# Twin-Stick (Custom)

[Controller documentation](README.md) · [Testing methodology](profile-testing-methodology.md)

## Reference environment — OBSERVED

The reference profile was developed around the maintainer's Brook/XInput
Twin-Stick. It provides configurable lever inputs for custom builds and adapters;
the reference mapping is not a universal Twin-Stick standard.

| Property | Record |
| --- | --- |
| Controller presentation | XInput / Xbox-compatible |
| PCB or adapter family | Brook; exact model and firmware not recorded |
| VID/PID | May vary with PCB or adapter; not the identity of this profile |
| Windows and test utility versions | Not recorded |

## Default mapping — IMPLEMENTED

The defaults match the supplied reference layout. Left and right in the table
refer to physical levers, triggers and dash buttons.

| Physical control / game input | Default XInput binding |
| --- | --- |
| Left lever up | D-pad Up |
| Left lever down | D-pad Down |
| Left lever left | D-pad Left |
| Left lever right | D-pad Right |
| Left trigger | LT |
| Left dash | LB |
| Right lever up | Y |
| Right lever down | A |
| Right lever left | X |
| Right lever right | B |
| Right trigger | RT |
| Right dash | RB |
| Pause | Start; fixed rather than a gameplay binding |

## Remapping and ownership — IMPLEMENTED

On English retail and Japanese rerelease, **F7 → Twin-Stick (Custom) → Next**
opens a twelve-slot editor. Focusing an action starts direct physical capture:
release all recognized inputs, then press one button or move one direction on
that player's selected XInput controller. This path exists in the current code;
it is not a planned feature.

| Operation | Code behavior |
| --- | --- |
| Capture | Wait for neutral, then accept one active input; held entry inputs, chords and diagonals require a retry |
| Bindable inputs | A/B/X/Y, LB/RB, LT/RT, four directions per thumbstick, four D-pad directions; 20 total |
| Capture thresholds | Triggers must exceed `64` on the XInput byte scale; sticks use the player's deadzone threshold |
| Escape / 30-second timeout / disconnect | Preserve the current binding; Escape makes manual dropdown selection available |
| None | Clear the selected gameplay binding |
| OK / Cancel | Save / discard pending binding edits |
| Default, then OK | Restore the reference defaults for that player |
| Persistence | Separate `1P Custom Assign` and `2P Custom Assign` entries in `v_on.ini`; missing or malformed layouts use defaults |

Start/pause and Back/camera remain fixed. D-pad remapping affects gameplay while
fixed D-pad menu navigation remains available. Dropdown editing and captured
inputs update the same pending layout; capture alone does not save it.

Controller selection is distinct from binding selection. On first eligible use,
F7 confirmation, or **Choose controller**, release and press Start on the intended
controller. The helper checks all four XInput slots and routes the claimed source
to the selected player. Choosing the other player's XInput controller swaps
compatible assignments; it does not share one source between players.

Claims are session-scoped. A detected disconnect clears input and invalidates the
claim; reconnecting requires F7 selection. Profiles and bindings persist across
launches, but physical ownership must be re-established. No VID/PID matching or
persistent physical identity is inferred from an XInput slot. A Custom capture
requires an XInput source even when switching from a previously selected Tanita.

## Validation — VALIDATED

| Test | Result | Evidence boundary |
| --- | --- | --- |
| Reference hardware operation | Functionally Tested | Maintainer confirmation |
| Controller reassignment and remapping | Functionally Tested | Latest internal build confirmation |
| Direct physical input capture | Functionally Tested | Maintainer confirmation, also reflected in the branch README update |
| Separate P1 / P2 runs | Not recorded | Functional confirmation does not identify the player positions |
| Save/relaunch and cancel/timeout edge cases | Not recorded individually | Automated coverage exists; separate hardware results were not supplied |
| Simultaneous local VS / multiple Brook adapters | Not Tested in the retained record | No configuration-specific result supplied |

## Source references and limits

- [Default tables](../../asm/padtables.py) and [lever bindings](../../asm/twinstick.asm).
- [F7 editor and INI storage](../../asm/custombind.asm).
- [Physical capture and selection](../../input/controller.c), [capture/ownership rules](../../input/controller_logic.h), and [game input routing](../../asm/padxinput.asm).

Custom consumes XInput inputs, not arbitrary HID buttons or axes. The native
Tanita path belongs to its own fixed profile. Input IDs and the twelve game slots
bound the editor; additional exposed adapter controls are not automatically
available for binding.
