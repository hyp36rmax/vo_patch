# Raphnet Twin-Stick Profiles

The tested adapters expose different representations of the same two-lever
controller. A brand-level Raphnet button map cannot describe both configurations.
Each device-specific HID decoder resolves its inputs to common Twin-Stick semantics.

| Hardware record | Left lever | Right lever | Implementation | In-game evidence |
| --- | --- | --- | --- | --- |
| [Dreamcast HKT-7500 / DC adapter v1](raphnet-dreamcast-twinstick.md) | Buttons | Buttons | Implemented | Functionally Tested — R1 |
| [Saturn HSS-0151 / Saturn adapter v2](raphnet-saturn-twinstick.md) | X/Y axes | Buttons | Implemented | Functionally Tested — R1 |

Mixed Raphnet DC/Saturn local VS is **Functionally Tested**: both adapters operated
as expected in the same match. Both profiles are also **1P Validated** and
**2P Validated**, as confirmed by the maintainer.
Two identical DC adapters and two identical Saturn adapters remain **Not Tested**.

## Evidence and status

- **Physically validated:** the listed hardware inputs were exercised on the
  actual controller/adapter in the test utility; this does not itself establish
  in-game behavior.
- **Implemented:** the current Controller Expansion code decodes and routes the
  input as described; code inspection or software tests alone are not physical
  validation.
- **In-game validated:** exercised against a Controller Expansion test build.
  Both Raphnet profiles are **Functionally Tested** from the R1 success report;
  both profiles are **1P Validated** and **2P Validated**, and mixed local VS is
  **Functionally Tested**. Reconnect and persistence details remain unrecorded.
- **Manufacturer-documented only:** official compatibility information without
  a corresponding local hardware test; Dreamcast v2 physical validation is
  **Pending**, and its identity and mapping are not established here.

Measurements use Fred's Controller Tester. Utility/Windows versions, raw HID
descriptors and measurement dates were not supplied. The R1 functional result
covers the tested configurations; R2 changes F7 ordering without changing their
decoders, helper DLL or saved profile IDs.

## Implementation

`input/raphnet_map.h` contains separate DC v1 and Saturn v2 decoders. They produce
`VonTwinState`, a semantic bitmask defined in `input/twinstick_state.h`, rather
than XInput buttons or axes. `VonTwinGetState` reads the claimed physical device;
`asm/raphnet.asm` and the shared lever-mask tick deliver its twelve gameplay
controls to Virtual-On's active-low digital lever words. The existing jump/guard
normalization and game-state slot gates remain in effect.

The HID transport in `input/tanita.c` retains Tanita's decoder and shares its
attribute inspection, preparsed descriptors, nonblocking reads and error cleanup.
For these new profiles, the current accepted descriptor layout requires:

| Profile | Required input values | Required button usages |
| --- | --- | --- |
| DC v1 | None; lever directions are buttons | One range starting at usage 1 and covering at least 16 buttons |
| Saturn v2 | Generic Desktop X/Y with valid logical ranges | One range starting at usage 1 and covering at least 9 buttons |

Saturn X/Y and buttons must belong to the same input report. Decoding uses HID
usages and descriptor ranges, not guessed byte offsets. Axis samples below 25%
or above 75% become digital directions; the inclusive middle half is neutral.
Invalid or ambiguous required values are rejected and clear input. Successful
R1 operation confirms acceptance of the tested units; their raw descriptors have
not been archived. Other layouts require diagnostic evidence before broadening
the decoder.

Each family reserves up to two physical paths for the process lifetime.
Disconnects clear that controller's claim without promoting another unit.
Reconnect requires F7 selection; moving to new USB paths after both reservations
are occupied requires restarting the game. Slots are an internal transport
index, never a player assignment.

## Start claim and Pause

F7 and first-use selection read DC B3 or Saturn B8 directly from native semantic
state. Release Start, then press it on the intended player's controller. Held
Start on entry and simultaneous Start edges from multiple candidates cannot
claim by enumeration order. Claims can swap within a compatible family; an
incompatible prior assignment is cleared. The claim press is suppressed until
release before any gameplay or menu input is returned.

After claiming, Start drives accept and the existing intro-skip path. DC Pause
posts F3 on a fresh edge from the message pump, including while the game input
tick is paused. Saturn emits no Pause bit. No Pause binding is manufactured from
Saturn Start. Fixed Raphnet profiles have no remapping editor; Custom remains an
optional, independently remappable Xbox/Brook profile.

## Software checks and repeatable acceptance

Identity filters, exhaustive input mappings, Start-edge rules, family ownership
and emitted retail/JPRE lever code are software checked. API calls are mocked;
physical results remain those recorded in the individual hardware pages and the
mixed local-VS report above.

Use a separate game test folder. For **each** adapter:

1. Select its Raphnet profile in F7, release Start, then press physical Start.
   **Stop if the intended device does not claim successfully.**
2. Exercise both levers' cardinals and diagonals, both triggers, both top buttons,
   cross-stick combinations and trigger + top in active gameplay.
3. Check Start/menu behavior. On DC, test physical Pause and resume separately
   from Start. No Pause functionality is expected from Saturn.
4. Repeat as P2 and in mixed-controller local versus. Verify player isolation,
   reassignment and disconnect/reconnect without changing Windows index order.
5. Restart and verify saved profile selection, followed by a fresh physical claim.
6. Recheck Tanita, HORI, Custom defaults/remapping, original XInput and keyboard
   profiles. Identical dual-device tests remain separate evidence.

Record the package hash, edition, Windows version, adapter identity and results
using the [testing methodology](profile-testing-methodology.md). Record new
player-position and identical-adapter tests separately from the mixed VS result.
