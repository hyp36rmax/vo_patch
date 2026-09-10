bits 32
; Independent twelve-input Custom editor. Modal scratch is committed only
; by OK; neither other profiles nor the other player's live table is touched.
extern CURPLAYER, HWND, LOADLIB, GETPROC, ENDDIALOG
extern PADLIST, CUSTOM_DEFAULTS, CUSTOM_TEMPLATE, CUSTOM_PAGE_END
extern FINDLINE, PARSE12, WRITELINE, HEXCHAR
%include "padtables.inc"

page:
    pushad
    call resolve
    test eax,eax
    jz .failed
    call [activefn]          ; own the F7 window, not just its disabled game
    test eax,eax
    jnz .owner
    mov eax,[HWND]
.owner:
    push dword [CURPLAYER]
    push procedure
    push eax
    push CUSTOM_TEMPLATE
    push 0
    call [dialogfn]
    cmp eax,1
    sete al
    movzx eax,al
    mov [esp+28],eax
    jmp .result
.failed:
    mov dword [esp+28],0
.result:
    popad
    mov [ebp-0x14],eax        ; verified retail and JPRE page result
    jmp CUSTOM_PAGE_END

resolve:
    cmp dword [dialogfn],0
    jne .ready
    push ebx
    push user32
    call [LOADLIB]
    test eax,eax
    jz .fail
    mov ebx,eax
    push sendname
    push ebx
    call [GETPROC]
    mov [sendfn],eax
    test eax,eax
    jz .fail
    push titlename
    push ebx
    call [GETPROC]
    mov [titlefn],eax
    test eax,eax
    jz .fail
    push activename
    push ebx
    call [GETPROC]
    mov [activefn],eax
    test eax,eax
    jz .fail
    push dialogname
    push ebx
    call [GETPROC]
    mov [dialogfn],eax
.fail:
    pop ebx
    ret
.ready:
    mov eax,1
    ret

; WINAPI dialog procedure(hwnd,msg,wParam,lParam).
procedure:
    push ebp
    mov ebp,esp
    push ebx
    push esi
    push edi
    mov ebx,[ebp+8]
    mov eax,[ebp+12]
    cmp eax,0x110           ; WM_INITDIALOG
    je .init
    cmp eax,0x10            ; WM_CLOSE
    je .cancel
    cmp eax,0x111           ; WM_COMMAND
    jne .unhandled
    movzx eax,word [ebp+16]
    cmp eax,1
    je .ok
    cmp eax,2
    je .cancel
    cmp eax,3
    je .default
.unhandled:
    xor eax,eax
    jmp .out
.init:
    mov eax,[ebp+20]
    and eax,1
    mov [player],eax
    mov edx,title1
    test eax,eax
    jz .title
    mov edx,title2
.title:
    push edx
    push ebx
    call [titlefn]
    imul esi,[player],24
    add esi,binds1
    mov edi,pending
    mov ecx,6
    rep movsd
    xor edi,edi
.fill:
    push none
    push 0
    push 0x143             ; CB_ADDSTRING; deliberately no CBS_SORT
    lea eax,[edi+100]
    push eax
    push ebx
    call [sendfn]
    xor esi,esi
.input:
    push dword [PADLIST+esi*8]
    push 0
    push 0x143
    lea eax,[edi+100]
    push eax
    push ebx
    call [sendfn]
    inc esi
    cmp esi,20
    jb .input
    inc edi
    cmp edi,12
    jb .fill
    call refresh
    jmp .handled
.default:
    mov esi,CUSTOM_DEFAULTS
    mov edi,pending
    mov ecx,6
    rep movsd
    call refresh
    jmp .handled
.ok:
    xor edi,edi
.read:
    push 0
    push 0
    push 0x147             ; CB_GETCURSEL: 0 None, 1..20 pad inputs
    lea eax,[edi+100]
    push eax
    push ebx
    call [sendfn]
    dec eax
    cmp eax,20
    jae .none
    add eax,0xe0
    jmp .store
.none:
    xor eax,eax
.store:
    mov [pending+edi*2],ax
    inc edi
    cmp edi,12
    jb .read
    imul edi,[player],24
    add edi,binds1
    mov esi,pending
    mov ecx,6
    rep movsd
    mov eax,[player]
    call save
    push 1
    jmp .close
.cancel:
    push 0
.close:
    push ebx
    call [ENDDIALOG]
.handled:
    mov eax,1
.out:
    pop edi
    pop esi
    pop ebx
    leave
    ret 16

; ebx = dialog hwnd; selects the 12 pending values without changing them.
refresh:
    xor edi,edi
.loop:
    movzx eax,byte [pending+edi*2]
    sub eax,0xe0
    cmp eax,20
    jae .none
    inc eax
    jmp .select
.none:
    xor eax,eax
.select:
    push 0
    push eax
    push 0x14e             ; CB_SETCURSEL
    lea eax,[edi+100]
    push eax
    push ebx
    call [sendfn]
    inc edi
    cmp edi,12
    jb .loop
    ret

; eax = player. Uses the game's INI writer; no second config file/API.
save:
    pushad
    mov ebx,eax
    imul esi,eax,24
    add esi,binds1
    mov edi,line
    xor ecx,ecx
.byte:
    mov al,[esi+ecx]
    mov dl,al
    shr al,4
    call HEXCHAR
    mov al,dl
    call HEXCHAR
    inc ecx
    cmp ecx,24
    jb .byte
    mov byte [edi],0
    imul eax,ebx,17
    add eax,keys
    push line
    push eax
    call WRITELINE
    add esp,8
    popad
    ret

; Startup only, after stock INI parsing. Missing/malformed lines retain the
; Xbox/Brook defaults. Validate the complete line before PARSE12 can read it.
load:
    pushad
    xor ebx,ebx
.player:
    imul edi,ebx,24
    add edi,binds1
    mov esi,CUSTOM_DEFAULTS
    mov ecx,6
    rep movsd
    imul eax,ebx,17
    add eax,keys
    push eax
    call FINDLINE
    add esp,4
    test eax,eax
    jz .next
    mov esi,eax
    xor ecx,ecx
.hex:
    mov al,[esi+ecx]
    cmp al,'0'
    jb .next
    cmp al,'9'
    jbe .digit
    or al,0x20
    sub al,'a'
    cmp al,5
    ja .next
.digit:
    inc ecx
    cmp ecx,48
    jb .hex
    imul eax,ebx,17
    add eax,keys
    mov edi,pending
    call PARSE12
    xor ecx,ecx
.validate:
    cmp byte [pending+ecx*2+1],0
    jne .next
    mov al,[pending+ecx*2]
    test al,al
    jz .valid
    sub al,0xe0
    cmp al,20
    jae .next
.valid:
    inc ecx
    cmp ecx,12
    jb .validate
    imul edi,ebx,24
    add edi,binds1
    mov esi,pending
    mov ecx,6
    rep movsd
.next:
    inc ebx
    cmp ebx,2
    jb .player
    popad
    ret

align 4
binds1: custom_defaults
binds2: custom_defaults
pending: times 24 db 0
player: dd 0
dialogfn: dd 0
sendfn: dd 0
titlefn: dd 0
activefn: dd 0
line: times 49 db 0
keys: db '1P Custom Assign',0,'2P Custom Assign',0
none: db 'None',0
title1: db 'Twin-Stick (Custom) - Player 1',0
title2: db 'Twin-Stick (Custom) - Player 2',0
user32: db 'USER32.DLL',0
dialogname: db 'DialogBoxIndirectParamA',0
sendname: db 'SendDlgItemMessageA',0
titlename: db 'SetWindowTextA',0
activename: db 'GetActiveWindow',0
