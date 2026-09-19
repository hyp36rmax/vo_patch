bits 32
; Native semantic Twin-Stick integration. No XInput layout or bind ids.
extern DEVICES, EXIT1P, EXIT2P, TICK, TWIN_BLOCK1, TWIN_BLOCK2
extern RAPH_DISPATCH1, RAPH_DISPATCH2
extern CUSTOM_EDIT_DEVICE, HWND, POSTMSG, LOADLIB, GETPROC
extern PROFILE_0, PROFILE_1, PROFILE_2, PROFILE_3, PROFILE_4, PROFILE_5, PROFILE_6
extern RAPH_DC_NAME, RAPH_SATURN_NAME

; Original bounds are raised to eight only on the verified builds. Existing
; ids still take the original table (including the other profile patches).
dispatch1:
    cmp eax,7
    jae entry1
    jmp [RAPH_DISPATCH1+eax*4]
dispatch2:
    cmp eax,7
    jae entry2
    jmp [RAPH_DISPATCH2+eax*4]
entry1:
    push TWIN_BLOCK1
    call TICK
    add esp,4
    jmp EXIT1P
entry2:
    push TWIN_BLOCK2
    call TICK
    add esp,4
    jmp EXIT2P

; EAX player, EDX pointer to uint32 semantic controls. stdcall helper clears
; disconnected/unclaimed input; a missing helper fails closed.
poll:
    push ebx
    push esi
    mov ebx,eax
    mov esi,edx
    mov dword [esi],0
    cmp dword [nativefn],0
    jne .resolved
    push dllname
    call [LOADLIB]
    test eax,eax
    jz .missing
    push procname
    push eax
    call [GETPROC]
    mov [nativefn],eax
.resolved:
    cmp dword [nativefn],0
    je .missing
    push esi
    push dword [DEVICES+ebx*4]
    push ebx
    call [nativefn]
    jmp .out
.missing:
    mov eax,1
.out:
    pop esi
    pop ebx
    ret

; Message-pump path works while the game tick is paused and during the
; existing intro wait. Start accepts/skips; only native Pause posts F3.
pollkeys:
    cmp dword [enabled],4
    jne .out
    pushad
    xor esi,esi
.player:
    mov eax,[DEVICES+esi*4]
    sub eax,7
    cmp eax,1
    ja .clear
    mov eax,esi
    mov edx,pumpstate
    call poll
    test eax,eax
    jnz .clear
    mov ebx,[pumpstate]
    mov ebp,[previous+esi*4]
    mov [previous+esi*4],ebx
    not ebp
    and ebx,ebp
    test ebx,1<<13
    jz .start
    push 0
    push 0x72                   ; physical Pause -> F3
    push 0x100
    push dword [HWND]
    call [POSTMSG]
.start:
    test ebx,1<<12
    jz .next
    push 0
    push 0x20                   ; physical Start -> accept/intro skip
    push 0x100
    push dword [HWND]
    call [POSTMSG]
    jmp .next
.clear:
    mov dword [previous+esi*4],0
.next:
    inc esi
    cmp esi,2
    jb .player
    popad
.out:
    ret
align 4
profiles:
    dd PROFILE_0,PROFILE_1,PROFILE_2,PROFILE_3,PROFILE_4
    dd RAPH_DC_NAME,RAPH_SATURN_NAME,PROFILE_5,PROFILE_6,0
enabled: dd CUSTOM_EDIT_DEVICE
nativefn: dd 0
pumpstate: dd 0
previous: dd 0,0
dllname: db 'vontanita.dll',0
procname: db 'VonTwinGetState',0
