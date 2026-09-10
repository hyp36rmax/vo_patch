/* Explicit session ownership and modal press-to-bind for verified builds.
 * XInput exposes slots, not portable physical IDs. Users claim by Start on
 * each launch; disconnect invalidates the claim, never promotes another pad.
 * F7 can reselect without changing Windows' connection order.
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0600
#include <windows.h>
#include <xinput.h>
#include <stdio.h>
#include "controller_logic.h"
DWORD WINAPI TanitaGetState(DWORD index, XINPUT_STATE *state);
static VonOwner owners[2] = {{-1,0},{-1,0}};
static int owner_kind[2], suppress_start[2], busy;
static DWORD (WINAPI *get_state)(DWORD, XINPUT_STATE *);
static int resolved;

static DWORD raw_state(int source, XINPUT_STATE *state) {
    ZeroMemory(state, sizeof(*state));
    if (source >= 4 && source < 6) return TanitaGetState(source-4, state);
    if (source < 0 || source > 3) return ERROR_DEVICE_NOT_CONNECTED;
    if (!resolved) {
        static const char *names[] = {"xinput1_4.dll","xinput1_3.dll","xinput9_1_0.dll"};
        unsigned i;
        resolved=1;
        for (i=0;i<3 && !get_state;++i) {
            HMODULE module=LoadLibraryA(names[i]);
            if (module) get_state=(void *)GetProcAddress(module,"XInputGetState");
        }
    }
    return get_state ? get_state(source,state) : ERROR_DEVICE_NOT_CONNECTED;
}

typedef struct {
    unsigned player;
    int kind, capture, threshold;
    DWORD started;
    unsigned ready;
    VonCapture edge;
} Prompt;
static HWND child(HWND parent, const char *cls, const char *text, DWORD style,
                  int id, LONG left, LONG top, LONG right, LONG bottom) {
    RECT rect={left,top,right,bottom};
    MapDialogRect(parent,&rect);
    return CreateWindowExA(0,cls,text,WS_CHILD|WS_VISIBLE|style,
        rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top,
        parent,(HMENU)(INT_PTR)id,NULL,NULL);
}
static void label(HWND window, const char *text) {
    SetDlgItemTextA(window, 100, text);
}
static INT_PTR CALLBACK procedure(HWND window, UINT msg, WPARAM wp, LPARAM lp) {
    Prompt *p=(Prompt *)GetWindowLongPtrW(window,DWLP_USER);
    if (msg==WM_INITDIALOG) {
        char title[96];
        p=(Prompt *)lp;
        SetWindowLongPtrW(window,DWLP_USER,(LONG_PTR)p);
        snprintf(title,sizeof(title),"Player %u - %s",p->player+1,
                 p->capture ? "Press a control to bind" : "Choose controller");
        SetWindowTextA(window,title);
        HWND instructions=child(window,"STATIC",p->capture ?
            "Release all controls, then press ONE button or move ONE lever direction.\nEscape cancels; the current binding stays unchanged." :
            "Release Start / Options, then press it on this player's controller.\nSelecting the other player's controller swaps compatible assignments.",
            0,100,8,8,237,46);
        HWND cancel=child(window,"BUTTON","Cancel",WS_TABSTOP|BS_DEFPUSHBUTTON,
                          IDCANCEL,185,54,237,72);
        if (!instructions || !cancel) { EndDialog(window,0); return TRUE; }
        p->started=GetTickCount();
        if (!SetTimer(window,1,16,NULL)) EndDialog(window,0);
        return TRUE;
    }
    if (!p) return FALSE;
    if (msg==WM_CLOSE || (msg==WM_COMMAND && LOWORD(wp)==IDCANCEL)) {
        EndDialog(window,0); return TRUE;
    }
    if (msg==WM_DESTROY) { KillTimer(window,1); return TRUE; }
    if (msg!=WM_TIMER) return FALSE;
    if (GetTickCount()-p->started>30000) { EndDialog(window,0); return TRUE; }
    if (p->capture) {
        XINPUT_STATE state;
        int input;
        if (raw_state(owners[p->player].source,&state)) {
            owners[p->player].source=-1;
            EndDialog(window,0); return TRUE;
        }
        input=von_capture(&p->edge,von_inputs(state.Gamepad.wButtons,
            state.Gamepad.bLeftTrigger,state.Gamepad.bRightTrigger,
            state.Gamepad.sThumbLX,state.Gamepad.sThumbLY,
            state.Gamepad.sThumbRX,state.Gamepad.sThumbRY,p->threshold));
        if (input) EndDialog(window,input);
    } else {
        int first=p->kind==5?4:0, end=p->kind==5?6:4, i, candidate=-1;
        unsigned pressed=0;
        for (i=first;i<end;++i) {
            XINPUT_STATE state;
            unsigned bit=1u<<i;
            if (raw_state(i,&state)) { p->ready &= ~bit; continue; }
            if (!(state.Gamepad.wButtons & XINPUT_GAMEPAD_START)) p->ready |= bit;
            else {
                if (p->ready & bit) { candidate=i; ++pressed; }
                p->ready &= ~bit;
            }
        }
        if (pressed==1) {
            if (von_claim(owners,p->player,candidate)) {
                owner_kind[p->player]=p->kind;
                suppress_start[0]=suppress_start[1]=1;
                EndDialog(window,1);
            } else label(window,"That controller belongs to the other player.\nPress Start / Options on another controller, or cancel.");
        } else if (pressed>1) label(window,"Multiple controllers pressed Start. Release them and try ONE controller.");
    }
    return TRUE;
}
static int prompt(HWND parent, Prompt *p) {
    /* WORD-packed empty DLGTEMPLATE; child controls are created at init. */
    WORD storage[32]={0};
    DLGTEMPLATE *tpl=(DLGTEMPLATE *)storage;
    INT_PTR result;
    tpl->style=WS_POPUP|WS_CAPTION|WS_SYSMENU|DS_MODALFRAME|DS_CENTER;
    tpl->cx=245; tpl->cy=78;
    if (busy) return 0;
    busy=1;
    result=DialogBoxIndirectParamW(GetModuleHandleW(NULL),tpl,parent,procedure,(LPARAM)p);
    busy=0;
    return result>0?(int)result:0;
}
__declspec(dllexport) int WINAPI VonSelectController(HWND parent, DWORD player, DWORD kind) {
    Prompt p={0};
    if (player>1 || busy) return 0;
    if (kind!=1 && kind!=2 && kind!=4 && kind!=5 && kind!=6) {
        owners[player].source=-1; owners[player].attempted=0; owner_kind[player]=0;
        return 1;
    }
    p.player=player; p.kind=(int)kind;
    owners[player].attempted=1;
    /* Cancel retains an existing claim only when its device family matches. */
    if ((owner_kind[player]==5)!=(kind==5)) owners[player].source=-1;
    if (GetActiveWindow()) parent=GetActiveWindow();
    return prompt(parent,&p);
}
__declspec(dllexport) DWORD WINAPI VonGetState(DWORD player, DWORD kind, XINPUT_STATE *state) {
    DWORD result;
    if (!state) return ERROR_BAD_ARGUMENTS;
    ZeroMemory(state,sizeof(*state));
    if (player>1 || busy) return ERROR_DEVICE_NOT_CONNECTED;
    if (!owners[player].attempted) {
        /* Automatic first-use prompts never steal the only connected pad from
         * another player. An explicit F7 selection may still request a swap. */
        XINPUT_STATE probe;
        int i, available=0, first=kind==5?4:0, end=kind==5?6:4;
        for (i=first;i<end;++i)
            if (i!=owners[1-player].source && !raw_state(i,&probe)) available=1;
        if (!available) return ERROR_DEVICE_NOT_CONNECTED;
        VonSelectController(GetActiveWindow(),player,kind);
    }
    if (!von_owned_source(owners,player,kind)) return ERROR_DEVICE_NOT_CONNECTED;
    result=raw_state(owners[player].source,state);
    if (result) { owners[player].source=-1; ZeroMemory(state,sizeof(*state)); }
    else if (suppress_start[player]) {
        if (state->Gamepad.wButtons & XINPUT_GAMEPAD_START)
            ZeroMemory(state,sizeof(*state));
        else suppress_start[player]=0;
    }
    return result;
}
__declspec(dllexport) int WINAPI VonCaptureInput(HWND parent, DWORD player, DWORD kind, int threshold) {
    Prompt p={0};
    if (player>1 || busy) return 0;
    if (!von_owned_source(owners,player,kind) &&
        !VonSelectController(parent,player,kind)) return 0;
    p.player=player; p.kind=(int)kind; p.capture=1; p.threshold=threshold;
    return prompt(parent,&p);
}
