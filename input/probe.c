/* Standalone field diagnostic. Reuses the shipped Tanita reader unchanged.
 * Does not patch the game, install a driver or change controller settings. */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0600
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <conio.h>
#include "tanita_map.h"

static unsigned probe_index;
static unsigned raw_buttons[2];
static int32_t raw_axes[2][5];
static TanitaState capture_map(const int32_t *v, unsigned b,
    int32_t xl, int32_t xh, int32_t yl, int32_t yh,
    int32_t zl, int32_t zh, int32_t rl, int32_t rh,
    int32_t hl, int32_t hh) {
    unsigned i;
    raw_buttons[probe_index] = b;
    for (i=0;i<5;++i) raw_axes[probe_index][i]=v[i];
    return tanita_map(v,b,xl,xh,yl,yh,zl,zh,rl,rh,hl,hh);
}
/* Capture the raw arguments at the reader's mapping boundary, without
 * reading its pending OVERLAPPED report buffer from a second consumer. */
#define tanita_map capture_map
#include "tanita.c"
#undef tanita_map

static FILE *logfile;
static DWORD started;
static void say(const char *fmt, ...) {
    va_list a;
    va_start(a,fmt); vprintf(fmt,a); va_end(a);
    if (logfile) { va_start(a,fmt); vfprintf(logfile,fmt,a); va_end(a); fflush(logfile); }
}
static void hid_identity(void) {
    GUID guid;
    HDEVINFO set;
    SP_DEVICE_INTERFACE_DATA iface;
    DWORD i;
    HidD_GetHidGuid(&guid);
    set=SetupDiGetClassDevsW(&guid,NULL,NULL,DIGCF_PRESENT|DIGCF_DEVICEINTERFACE);
    if(set==INVALID_HANDLE_VALUE) return;
    ZeroMemory(&iface,sizeof(iface)); iface.cbSize=sizeof(iface);
    for(i=0;SetupDiEnumDeviceInterfaces(set,NULL,&guid,i,&iface);++i) {
        DWORD bytes=0;
        PSP_DEVICE_INTERFACE_DETAIL_DATA_W detail;
        HIDD_ATTRIBUTES a;
        HANDLE h;
        SetupDiGetDeviceInterfaceDetailW(set,&iface,NULL,0,&bytes,NULL);
        if(!bytes || bytes>16384) continue;
        detail=(PSP_DEVICE_INTERFACE_DETAIL_DATA_W)malloc(bytes);
        if(!detail) break;
        detail->cbSize=sizeof(*detail);
        if(SetupDiGetDeviceInterfaceDetailW(set,&iface,detail,bytes,NULL,NULL)) {
            h=CreateFileW(detail->DevicePath,0,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,0,NULL);
            if(h!=INVALID_HANDLE_VALUE) {
                ZeroMemory(&a,sizeof(a)); a.Size=sizeof(a);
                if(HidD_GetAttributes(h,&a) &&
                    ((a.VendorID==0x1f4f && a.ProductID==0x9001) ||
                     (a.VendorID==0x1bad && a.ProductID==0xff00))) {
                    char path[4096];
                    WideCharToMultiByte(CP_UTF8,0,detail->DevicePath,-1,path,sizeof(path),NULL,NULL);
                    say("HID VID=%04x PID=%04x REV=%04x path=%s\n",
                        a.VendorID,a.ProductID,a.VersionNumber,path);
                }
                CloseHandle(h);
            }
        }
        free(detail);
    }
    SetupDiDestroyDeviceInfoList(set);
}

typedef DWORD (WINAPI *GetStateFn)(DWORD,XINPUT_STATE*);
int main(void) {
    const char *names[3]={"xinput1_4.dll","xinput1_3.dll","xinput9_1_0.dll"};
    GetStateFn get[3]={0};
    XINPUT_GAMEPAD previous[3][4]={{{0}}};
    DWORD status[3][4];
    XINPUT_GAMEPAD last_tanita[2]={{0}};
    unsigned last_raw[2]={0};
    DWORD tanita_status[2]={~0u,~0u};
    char filename[MAX_PATH];
    SYSTEMTIME now;
    unsigned dll,slot;
    GetLocalTime(&now);
    snprintf(filename,sizeof(filename),"controller-diagnostic-%04u%02u%02u-%02u%02u%02u.txt",
        now.wYear,now.wMonth,now.wDay,now.wHour,now.wMinute,now.wSecond);
    logfile=fopen(filename,"w");
    if(!logfile) { printf("Cannot create log in this folder. Move the tester to a writable folder.\nPress any key.\n"); _getch(); return 1; }
    say("Virtual-On controller diagnostic 1; base reader: commit 4963f51\n");
    say("Log: %s\nRun beside v_on.exe with the game closed.\n",filename);
    say("For 60 seconds: move each lever; press each top button separately;\nthen each trigger, D-pad, Start/Options. Press Escape to finish early.\n");
    say("Tanita raw-buttons are ZERO-BASED; XInput buttons are hexadecimal masks.\n");
    hid_identity();
    memset(status,0xff,sizeof(status));
    for(dll=0;dll<3;++dll) {
        HMODULE module=LoadLibraryA(names[dll]);
        if(module) {
            char path[MAX_PATH]={0};
            GetModuleFileNameA(module,path,sizeof(path));
            get[dll]=(GetStateFn)(void*)GetProcAddress(module,"XInputGetState");
            say("XInput %s loaded from %s; GetState=%s\n",names[dll],path,get[dll]?"available":"missing");
        } else say("XInput %s unavailable, error=%lu\n",names[dll],GetLastError());
    }
    started=GetTickCount();
    while((DWORD)(GetTickCount()-started)<60000) {
        if(_kbhit() && _getch()==27) break;
        for(dll=0;dll<3;++dll) if(get[dll]) for(slot=0;slot<4;++slot) {
            XINPUT_STATE state;
            DWORD result;
            ZeroMemory(&state,sizeof(state)); result=get[dll](slot,&state);
            if(result!=status[dll][slot] || (!result && memcmp(&previous[dll][slot],&state.Gamepad,sizeof(state.Gamepad)))) {
                XINPUT_GAMEPAD *p=&state.Gamepad;
                say("%6lu ms %s slot=%u status=%lu buttons=%04x LT=%u RT=%u LX=%d LY=%d RX=%d RY=%d\n",
                    GetTickCount()-started,names[dll],slot,result,p->wButtons,p->bLeftTrigger,p->bRightTrigger,
                    p->sThumbLX,p->sThumbLY,p->sThumbRX,p->sThumbRY);
                status[dll][slot]=result; previous[dll][slot]=*p;
            }
        }
        for(slot=0;slot<2;++slot) {
            XINPUT_STATE state;
            DWORD result;
            probe_index=slot; result=TanitaGetState(slot,&state);
            if(result!=tanita_status[slot] || (!result &&
                (last_raw[slot]!=raw_buttons[slot] || memcmp(&last_tanita[slot],&state.Gamepad,sizeof(state.Gamepad))))) {
                unsigned button;
                say("%6lu ms Tanita unit=%u status=%lu raw-buttons=[",GetTickCount()-started,slot,result);
                if(!result) for(button=0;button<13;++button) if(raw_buttons[slot]&(1u<<button)) say(" %u",button);
                say(" ]");
                if(!result) say(" X=%ld Y=%ld Z=%ld Rz=%ld hat=%ld mapped-buttons=%04x\n",
                    (long)raw_axes[slot][0],(long)raw_axes[slot][1],(long)raw_axes[slot][2],
                    (long)raw_axes[slot][3],(long)raw_axes[slot][4],state.Gamepad.wButtons);
                else say("\n");
                tanita_status[slot]=result; last_raw[slot]=raw_buttons[slot]; last_tanita[slot]=state.Gamepad;
            }
        }
        Sleep(8);
    }
    say("Finished. Send the log and identify which top buttons you pressed.\n");
    fclose(logfile);
    for(slot=0;slot<2;++slot) close_device(&devices[slot]);
    printf("Saved %s\nPress any key to close.\n",filename); _getch();
    return 0;
}
