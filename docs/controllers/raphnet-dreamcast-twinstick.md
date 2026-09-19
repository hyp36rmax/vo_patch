# Twin-Stick (Raphnet DC)

Sega Dreamcast HKT-7500 Twin-Stick through a Raphnet Dreamcast-to-USB adapter
**v1**. Measurements below were physically exercised in Fred's Controller Tester.
The Controller Expansion R1 implementation was subsequently reported successful
in-game. Both player positions and mixed local VS are validated. Reconnect and
identical-adapter results remain separate; see the [shared evidence definitions](raphnet-twinsticks.md#evidence-and-status).

## Observed identity

| Field | Observed value |
| --- | --- |
| Windows device name | Dreamcast to USB |
| VID / PID | `289B` / `0008` |
| Revision | `0100` |
| Usage page / usage | `0001` Generic Desktop / `0005` Game Pad |

The implemented profile matches VID/PID and collection usage. Revision `0100`
is recorded evidence, not a mandatory filter.

## Physical mapping

`B` numbers are Fred's zero-based indices. Windows' conventional human-facing
button number is one higher: B3 is Button 4 and B11 is Button 12. This is a
numbering difference, not a different mapping.

| Semantic control | Fred's index | Windows button |
| --- | --- | --- |
| Left up | B4 | 5 |
| Left down | B5 | 6 |
| Left left | B6 | 7 |
| Left right | B7 | 8 |
| Left trigger | B10 | 11 |
| Left top / turbo | B9 | 10 |
| Right up | B12 | 13 |
| Right down | B13 | 14 |
| Right left | B14 | 15 |
| Right right | B15 | 16 |
| Right trigger | B2 | 3 |
| Right top / turbo | B1 | 2 |
| Start | B3 | 4 |
| Pause | B11 | 12 |

Both physical levers report discrete buttons. Start participates in controller
selection/ownership; Pause is a separate physical control.

## Hardware characterization

All rows below are **physically validated at the HID/test-utility level**.
No rollover or input collision was observed in the tested combinations.

| Test | Result |
| --- | --- |
| All four directions on each lever | PASS |
| Left- and right-lever diagonals | PASS |
| Simultaneous levers and cross-stick directions | PASS |
| Left trigger + left top: B10 + B9 | PASS |
| Right trigger + right top: B2 + B1 | PASS |
| Both triggers: B10 + B2 | PASS |
| Both top controls: B9 + B1 | PASS |
| Pause combined with gameplay inputs | PASS |
| Start B3 and Pause B11 individually | PASS |

## Implemented behavior and game validation

The DC v1 decoder converts the observed buttons directly to semantic lever,
trigger, top, Start and Pause controls. Physical Start B3 claims the intended
player's unit after a release/new-press sequence. The claim press is suppressed
until release; afterward Start drives accept/intro skip. Pause B11 posts the
existing F3 pause/resume action independently, including while the game tick is
paused. The [shared implementation record](raphnet-twinsticks.md#implementation)
describes HID transport, ownership and the fixed-profile remapping policy.

| Area | Status |
| --- | --- |
| Identity, individual inputs, diagonals and simultaneous inputs | Characterized — physically validated |
| Start and Pause at HID level | Characterized — physically validated |
| Controller Expansion decoder, ownership and game routing | Implemented |
| R1 in-game operation | Functionally Tested — maintainer success report |
| P1 operation | 1P Validated — maintainer confirmation |
| P2 operation | 2P Validated — maintainer confirmation |
| Saved-profile persistence details | Not separately recorded |
| Separate in-game Pause/resume result | Not separately recorded |
| Mixed Raphnet DC/Saturn local VS | Functionally Tested — maintainer report |
| Reconnect test details | Pending |
| Two identical DC adapters | Not Tested |

## Dreamcast adapter v2

**Manufacturer-documented HKT-7500 support / physical validation pending.**
Raphnet's official v2 compatibility list includes HKT-7500, with directions and
controls presented as buttons; that listing attributes the result to a user.
It is not a Controller Expansion test result. The exact v2 HID identity and
button numbering have not been characterized here, and the v1 decoder does not
establish v2 compatibility. [Official Dreamcast v2 product documentation](https://www.raphnet-tech.com/products/dreamcast_usb_adapter/index.php).

The [official Dreamcast adapter technical project](https://www.raphnet.net/electronique/dreamcast_usb/index.php)
is retained as hardware-preservation reference; it does not replace measured
identity or mapping evidence for a particular adapter variant.
