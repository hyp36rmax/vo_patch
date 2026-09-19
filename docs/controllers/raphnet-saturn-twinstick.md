# Twin-Stick (Raphnet Saturn)

Sega Saturn HSS-0151 Twin-Stick through a Raphnet Saturn-to-USB adapter **v2**.
Measurements below were physically exercised in Fred's Controller Tester.
The Controller Expansion R1 implementation was subsequently reported successful
in-game. Both player positions and mixed local VS are validated. Reconnect and
identical-adapter results remain separate; see the [shared evidence definitions](raphnet-twinsticks.md#evidence-and-status).

## Observed identity

| Field | Observed value |
| --- | --- |
| VID / PID | `289B` / `0043` |
| Revision / interface | `0300` / `00` |
| Usage page / usage | `0001` Generic Desktop / `0005` Game Pad |

The implemented profile matches VID/PID and collection usage. Revision `0300`
and interface `00` are recorded evidence, not mandatory filters.

## Physical mapping

`B` numbers are Fred's zero-based indices; conventional Windows button numbers
are one higher. Axis percentages describe the test utility's presentation.

| Semantic control | Observed input |
| --- | --- |
| Left neutral | X 50%, Y 50% |
| Left up | Y 0% |
| Left down | Y 100% |
| Left left | X 0% |
| Left right | X 100% |
| Left trigger | B6 |
| Left top / turbo | B7 |
| Right up | B3 |
| Right down | B2 |
| Right left | B0 |
| Right right | B4 |
| Right trigger | B1 |
| Right top / turbo | B5 |
| Start | B8 — Windows Button 9 |
| Pause | N/A — no physical control |

The left lever exposes X/Y axes; the right lever exposes discrete buttons.
Start participates in controller selection/ownership. No Saturn Pause mapping
is created.

## Hardware characterization

Neutral/range, individual inputs and every combination below are **physically
validated at the HID/test-utility level**. No rollover or input collision was
observed in these tests.

| Diagonal | Left lever | Right lever | Result |
| --- | --- | --- | --- |
| Up + right | Y 0% + X 100% | B3 + B4 | PASS, each lever independently |
| Up + left | Y 0% + X 0% | B3 + B0 | PASS, each lever independently |
| Down + right | Y 100% + X 100% | B2 + B4 | PASS, each lever independently |
| Down + left | Y 100% + X 0% | B2 + B0 | PASS, each lever independently |

| Simultaneous controls | Observed inputs | Result |
| --- | --- | --- |
| Left trigger + left top | B6 + B7 | PASS |
| Right trigger + right top | B1 + B5 | PASS |
| Both triggers | B6 + B1 | PASS |
| Both top controls | B7 + B5 | PASS |
| Left up + right up | Y 0% + B3 | PASS |
| Left left + right right | X 0% + B4 | PASS |
| Start + left trigger | B8 + B6 | PASS |
| Start + right trigger | B8 + B1 | PASS |

## Implemented behavior and game validation

The Saturn v2 decoder thresholds X/Y into digital left-lever directions and
maps the observed buttons to the remaining semantic controls. Physical Start
B8 claims the intended player's unit after a release/new-press sequence. The
claim press is suppressed until release; afterward Start drives accept/intro
skip. The decoder never emits Pause. The [shared implementation record](raphnet-twinsticks.md#implementation)
describes HID transport, ownership and the fixed-profile remapping policy.

| Area | Status |
| --- | --- |
| Identity, axis neutral/range and individual inputs | Characterized — physically validated |
| All left/right diagonals and listed simultaneous inputs | Characterized — physically validated |
| Start at HID level | Characterized — physically validated |
| Pause | N/A — not present |
| Controller Expansion decoder, ownership and game routing | Implemented |
| R1 in-game operation | Functionally Tested — maintainer success report |
| P1 operation | 1P Validated — maintainer confirmation |
| P2 operation | 2P Validated — maintainer confirmation |
| Saved-profile persistence details | Not separately recorded |
| Mixed Raphnet DC/Saturn local VS | Functionally Tested — maintainer report |
| Reconnect test details | Pending |
| Two identical Saturn adapters | Not Tested |

## Official references

The [official Saturn v2 product documentation](https://www.raphnet-tech.com/products/saturn_to_usb_adapter_v2/index.php)
lists HSS-0151 support and right-stick button presentation. The observed mapping
above remains the evidence for the tested configuration; configurable adapter
settings must not be assumed to have identical behavior.

The [official Saturn adapter technical project](https://www.raphnet.net/electronique/saturn_usb/index.php)
is retained as a hardware-preservation reference.
