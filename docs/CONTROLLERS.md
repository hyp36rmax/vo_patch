# Controller Expansion: hardware profiles

Status: software implementation for retail and Japanese rerelease. Physical
Windows validation is pending. This is not a claim that the device reader has
been tested on a connected Tanita or HORI.

## Architecture

Custom retains its Xbox/Brook fixed table and has no hardware-specific binds.
The upstream Gamepad, Twin-stick, Simple and Real paths retain their mappings.
Profile IDs stay 0 Real, 1 Gamepad, 2 Twin-stick, 3 Simple, 4 Custom; this change
adds 5 Tanita and 6 HORI EX. F7 lists Gamepad, Twin-stick, Custom, Tanita, HORI,
Simple, Real. Every player selects independently.

Tanita uses a narrowly scoped 32-bit HID helper. The game's DirectInput path is
built around its legacy joystick profiles and device counts. Reusing that path
would require changing those profiles and does not directly supply the requested
revision/collection identity. Raw Input would require window message handling.
HID supports exact attributes, collection usage, descriptor-based values and a
separate handle for each physical path, without a new game window hook.

The helper accepts only VID 1F4F, PID 9001, revision 0200, usage page 1 / usage 5.
It reads X/Y/Z/Rz and the hat by usage, rather than guessing raw byte offsets.
It expects these values and a button range starting at HID usage 1 through at
least 13 in one report. Ambiguous or incomplete descriptors are rejected.
The reported hardware observations do not establish that descriptor layout;
this must be checked on the first physical unit. No other HID profile is added.

Overlapped reads keep the normal polling path nonblocking. Each handle owns its
preparsed descriptor, report buffer, pending read and cached state. A bounded
report drain avoids an unbounded busy loop. Completed malformed reports clear
state; read failures close the handle and return disconnected. An incomplete
read retains the last complete state. Cancellation completes before a buffer
is reused. Up to two exact device paths are sorted and reserved for the process
lifetime; a disconnected path does not shift the other player to a new unit.
New USB paths after both reservations are filled require a game restart.

Axes are thresholded at 25% and 75% of each descriptor's logical range, then
converted to full digital XInput-shaped directions for the existing active-low
lever engine. This is an internal state format, not a virtual XInput device.
Both axes of a lever can be active. Logical buttons 10 and 11 are each mapped
once; the hardware's duplicate physical controls cannot be distinguished.

HORI EX uses the existing XInput poller with a dedicated D-pad/right-stick
bind table. It is manually selected and does not attempt VID/PID discovery
through XInput. Native Tanita players consume no XInput slots. XInput players
keep ascending connected-slot assignment, P1 first; no activity-based claiming.
Raw XInput Y uses positive-up. Fred's percentage display must be checked against
actual raw XInput values on the device before declaring hardware validation.

## Binary dispatch evidence

Both pristine executables bound the gameplay switch at ID 7. Retail slots 5/6
are 0x422b8/0x422bc (P1) and 0x1bc14b/0x1bc14f (P2); JPRE equivalents are
0x41978/0x4197c and 0x1b6abb/0x1b6abf. The repeated original pointers require
explicit translations in tools/votrans.py rather than ambiguous pattern matches.

Startup joystick-validation and F7 joystick-spending entries for IDs 5/6 bypass
legacy joystick checks. F7's bind-dialog table is only 0..5: ID 5 points to the
success/no-dialog case, while ID 6 already takes that same default branch.
No nonexistent seventh table entry is written. The INI route bytes for 5/6
use the existing no-legacy-bind branch; INIALL still loads both keyboard bind
blocks. Apply/serialize entries 5/6 skip legacy joystick serialization and
resume at the common device-number writer. The JPRE save-table entries were
verified against its switch bound and repeated pointer targets.

Generated assembly and site maps must be regenerated through project tools.
The DLL is built with input/build.py, which records source and binary hashes;
VON_INPUT_CC can select an i686 Windows compiler. The committed first build uses
LLVM-MinGW 20260908 UCRT, with warnings treated as errors. Windows 10+ supplies
that runtime. The patcher verifies the helper before installing it and refuses
to overwrite an existing different vontanita.dll. Restoring the original game
executable leaves this inert helper beside it; the original does not load it.

## Software checks

- Existing and new profile names, order and build gates.
- Assembly execution of all 49 profile pairs, including mixed APIs and both
  keyboard profiles; independent ascending ordinal allocation.
- Custom's 12 inputs and neutral state, both players, unchanged defaults.
- Upstream Twin-stick, native Tanita and HORI direction/diagonal masks, simultaneous
  triggers/dashes, neutral state and isolation of the other player's lever words.
- Native C mapping across all 256 byte-axis values, threshold boundaries,
  signed ranges, diagonals, hat/null and the specified buttons.
- Helper source/binary fingerprint, PE32 architecture, export and safe installation.
- Pristine retail/JPRE patch bytes and the project's patch-combination tests.

These checks mock controller API calls; they do not validate Windows HID delivery,
physical identity enumeration, unplug/replug timing or an actual two-unit setup.

## Windows acceptance run

Use a separate game test folder. Apply XInput support, then select profiles in
F7 independently for P1 and P2. Verify that saving and restarting preserves both.

1. Confirm all 12 actions and neutral on Custom; verify its original menu controls.
2. Select Tanita and check both lever directions and diagonals, simultaneous
   triggers and dash buttons, Options pause/resume, Cross accept and POV menus.
3. Run P1 Custom/P2 Tanita, reverse them, then Gamepad/Tanita and HORI/Tanita.
   Moving either unit must never move the other player.
4. With two Tanitas attached before launch, verify separate players, then unplug
   one during an input. Its controls must release; the other keeps its player.
   Reconnect to the same USB port and repeat with the opposite unit.
5. On Xbox 360 HORI EX, verify right-lever up/down in particular, all diagonals,
   both triggers together, both shoulders together and Start pause/resume.
6. Repeat with two HORIs when the second unit is available. Check both player
   assignments and saved profile selection after restarting.

If Tanita is not detected, capture its actual HID report descriptor and Windows
identity before broadening the accepted layout. Do not substitute guessed report
byte offsets or advertise another controller as validated.

## API references

- [Microsoft HID client sample](https://github.com/microsoft/Windows-driver-samples/blob/main/hid/hclient/pnp.c):
  attributes, collection capabilities and overlapped handle setup.
- [HID value capabilities](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/hidpi/ns-hidpi-_hidp_value_caps):
  usage, report ID, logical range and bit width.
- [XINPUT_GAMEPAD](https://learn.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_gamepad):
  button masks and signed axis polarity.
