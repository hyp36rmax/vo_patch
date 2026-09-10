# Controller Expansion: hardware profiles

Status: retail and Japanese rerelease. The user reports that Tanita levers,
triggers, D-pad and ordinary buttons work. The September 10 diagnostic shows
top buttons 6/7 reaching the reader but mapped only to stick-click bits. They
now additionally map to left/right dash; 10/11 aliases remain. HORI EX buttons and behavior were confirmed working after
selecting the assigned player (it was P2 with another controller connected).
Back's camera/zoom behavior is intentional and remains unchanged. Dual-unit
and disconnect/reconnect acceptance testing is still pending. The previous
Custom editor is confirmed to bind controls, with gameplay testing pending.
New press-to-bind capture and ownership selection also need Windows acceptance.

## Architecture

Custom retains Xbox/Brook defaults and has no hardware-specific binds. Its
independent F7 editor remaps all twelve gameplay slots, with separate live tables
and `1P Custom Assign` / `2P Custom Assign` INI lines. Cancel never commits pending
edits; Default requires OK to save. Missing or malformed lines keep the defaults.
Start and Back retain their fixed menu/camera behavior. A remapped D-pad no longer
also invokes its old gameplay direction, while fixed D-pad menu navigation stays.
Focusing a Custom action opens a 30-second physical capture prompt. It requires
neutral before one input; held inputs, chords and diagonals cannot bind by scan
priority. Escape/disconnect/timeout preserve the current dropdown selection.
Manual dropdown assignment remains available after cancelling capture.
The modal editor owns the active F7 window to prevent nested edits.
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
The first user test confirms that the reader accepts that unit. No other HID
profile is added.

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
Both axes of a lever can be active. Zero-based buttons 6/7 now produce shoulder
bits 0x100/0x200 as well as their prior stick-click bits. Buttons 10/11 retain
shoulder aliases. The shared lever engine clears left/right dash mask 0x02.

HORI EX uses the existing XInput poller with a dedicated D-pad/right-stick
bind table. It is manually selected and does not attempt VID/PID discovery
through XInput. Native Tanita players consume no XInput slots. XInput players
use explicit Start selection on first use each session and on F7 confirmation.
The helper queries all four slots (or both native units) and claims the one
whose Start/Options is newly pressed after release. Simultaneous claims are
rejected. Selecting the other player's controller swaps same-family assignments,
or clears the other claim when the old controller is incompatible. The claim
button is suppressed until release so it cannot immediately pause gameplay.
Captured inputs only poll the selected player's owned source.

XInput offers no universally usable persistent hardware ID. Ownership is therefore
session-scoped and reselected each launch; no slot number is persisted as an
identity. Detected disconnects clear state and invalidate that claim without
reassigning another connected controller. Reconnect requires F7 selection.
The two unverified executable builds retain their legacy ordinal allocator.
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
to overwrite an unknown vontanita.dll; a SHA allowlist permits upgrading the
previous helper shipped by this project. Restoring the original game
executable leaves this inert helper beside it; the original does not load it.

## Software checks

- Existing and new profile names, order and build gates.
- Assembly execution of all 49 profile pairs, including mixed APIs and both
  keyboard profiles; verified builds pass player/profile to the ownership helper,
  while the legacy allocator is separately regression-tested.
- Custom's 12 inputs and neutral state, both players, unchanged defaults.
- Custom editor input list, per-slot edits, None, Cancel after Default, per-player
  save/reload, malformed INI lines, Default + OK, F7 return values and D-pad
  remapping versus menu navigation. The editor's Win32 messages are mocked;
  the actual game dialog needs Windows visual/input acceptance testing.
- Upstream Twin-stick, native Tanita and HORI direction/diagonal masks, simultaneous
  triggers/dashes, neutral state and isolation of the other player's lever words.
- C ownership tests cover all distinct sparse/reversed source pairs, compatible
  swaps and incompatible transfer. Capture tests cover every input, neutral
  arming, held input rejection, chord rejection and threshold boundaries.
- Native C mapping across all 256 byte-axis values, threshold boundaries,
  signed ranges, diagonals, hat/null and the specified buttons.
- Helper source/binary fingerprint, PE32 architecture, export and safe installation.
- Pristine retail/JPRE patch bytes and the project's patch-combination tests.

These checks mock controller API calls; they do not validate Windows HID delivery,
physical identity enumeration, unplug/replug timing or an actual two-unit setup.

## Windows acceptance run

Use a separate game test folder. Apply XInput support, then select profiles in
F7 independently for P1 and P2, then press Start/Options on the intended units.
Verify profile/bind persistence and repeat explicit controller selection after restart.

1. Confirm all 12 actions and neutral on Custom; verify its original menu controls.
2. Select Tanita and check both lever directions and diagonals, simultaneous
   triggers and dash buttons, Options pause/resume, Cross accept and POV menus.
3. Run P1 Custom/P2 Tanita, reverse them, then Gamepad/Tanita and HORI/Tanita.
   Moving either unit must never move the other player.
4. With two Tanitas attached before launch, verify separate players, then unplug
   one during an input. Its controls must release; the other keeps its player.
   Reconnect to the same USB port, reselect through F7 and repeat with the opposite unit.
5. On Xbox 360 HORI EX, verify right-lever up/down in particular, all diagonals,
   both triggers together, both shoulders together and Start pause/resume.
6. Repeat with two HORIs when the second unit is available. Check both player
   assignments and saved profile selection after restarting.

7. With two controllers connected in reversed/sparse XInput slots, choose P1
   explicitly, then P2. Confirm both gameplay and Custom capture follow ownership.
   Reassign P1 to P2's controller and verify the compatible swap without unplugging.
8. Capture all twelve actions, cancel a capture, reject a diagonal/chord, save,
   restart and verify the bindings in a fight. Back must still zoom.

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
