bits 32
; Twin-stick profiles. No new input engine: the XInput tick in padxinput.asm
; is a bind -> condition -> lever-mask engine. The stock arcade profile keeps
; its original fixed LS/RS mapping. Controller Expansion adds a second set of
; stubs using an Xbox/Brook-style digital Twin Stick mapping.

%include "padtables.inc"
extern CUSTOM1, CUSTOM2
extern TICK                       ; the shared XInput tick
extern EXIT1P                     ; where the 1P profile switch resumes
extern EXIT2P                     ; and the 2P one
extern KBD1P                      ; stock keyboard handler, called by the tick
extern KBD2P
extern LEV1A                      ; 1P lever words, left then right
extern LEV1B
extern LEV2A
extern LEV2B
extern ACCEPT1                    ; key buffer slots the tick pokes for A
extern ACCEPT2
extern CAMERA1                    ; and for Back
extern CAMERA2
extern SCR1                       ; scratch the tick keeps per player
extern SCR2

; ---------------------------------------------------------------------------
; Upstream Twin-stick (XInput). Keep this path and its tables unchanged.
stub1p:
    push    block1
    call    TICK
    add     esp, 4
    jmp     EXIT1P

stub2p:
    push    block2
    call    TICK
    add     esp, 4
    jmp     EXIT2P

; ---------------------------------------------------------------------------
; Controller Expansion: Twin-Stick (Custom).
; The first version ships with the Xbox/Brook layout as its default. These
; stubs are intentionally separate so the original Twin-stick profile remains
; byte-for-byte equivalent in behaviour.
custom1p:
    push    customblock1
    call    TICK
    add     esp, 4
    jmp     EXIT1P

custom2p:
    push    customblock2
    call    TICK
    add     esp, 4
    jmp     EXIT2P

; One bind per slot, stride 2, matching the mask rows below. The codes are
; the condition table's, 0xe0 + index, the same ones the bound profile uses.
binds:
    db 0xe8, 0, 0xe9, 0, 0xea, 0, 0xeb, 0      ; LS up down left right
    db 0xec, 0, 0xed, 0, 0xee, 0, 0xef, 0      ; RS up down left right
    db 0xe6, 0, 0xe7, 0                        ; LT, RT   - the triggers
    db 0xe4, 0, 0xe5, 0                        ; LB, RB   - the turbo buttons

; Twin-Stick (Custom) default: Xbox/Brook layout from the controller matrix.
; D-pad ids are appended after the original sixteen XInput conditions so
; existing saved ids remain unchanged: f0 up, f1 down, f2 left, f3 right.
custombinds:
    custom_defaults

; Lever bits, active low: 0x20 up, 0x10 down, 0x80 left, 0x40 right,
; 0x01 trigger, 0x02 turbo. Taken from the game's own tables at 0x653690.
maska:
    db 0x20, 0x10, 0x80, 0x40                  ; left stick drives lever A
    db 0x00, 0x00, 0x00, 0x00
    db 0x01, 0x00, 0x02, 0x00
maskb:
    db 0x00, 0x00, 0x00, 0x00
    db 0x20, 0x10, 0x80, 0x40                  ; right stick drives lever B
    db 0x00, 0x01, 0x00, 0x02

block1:
    dd 0, binds, LEV1A, LEV1B, maska, maskb, ACCEPT1, SCR1, KBD1P, CAMERA1
block2:
    dd 1, binds, LEV2A, LEV2B, maska, maskb, ACCEPT2, SCR2, KBD2P, CAMERA2

customblock1:
    dd 0, CUSTOM1, LEV1A, LEV1B, maska, maskb, ACCEPT1, SCR1, KBD1P, CAMERA1
customblock2:
    dd 1, CUSTOM2, LEV2A, LEV2B, maska, maskb, ACCEPT2, SCR2, KBD2P, CAMERA2

; Native Tanita is converted to digital LS/RS and the existing trigger masks.
tanita1p:
    push block1
    call TICK
    add esp, 4
    jmp EXIT1P
tanita2p:
    push block2
    call TICK
    add esp, 4
    jmp EXIT2P
; HORI Twin Stick EX, Xbox 360: D-pad left lever, RS right lever.
hori1p:
    push horiblock1
    call TICK
    add esp, 4
    jmp EXIT1P
hori2p:
    push horiblock2
    call TICK
    add esp, 4
    jmp EXIT2P
horibinds:
    db 0xf0,0,0xf1,0,0xf2,0,0xf3,0
    db 0xec,0,0xed,0,0xee,0,0xef,0
    db 0xe6,0,0xe7,0,0xe4,0,0xe5,0
horiblock1:
    dd 0, horibinds, LEV1A, LEV1B, maska, maskb, ACCEPT1, SCR1, KBD1P, CAMERA1
horiblock2:
    dd 1, horibinds, LEV2A, LEV2B, maska, maskb, ACCEPT2, SCR2, KBD2P, CAMERA2
