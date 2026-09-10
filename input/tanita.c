/* Native reader for Tanita 1f4f:9001 revision 0200, Game Pad collection.
 * Polling is nonblocking. Each physical device owns its handle, report,
 * preparsed descriptor and state. Paths are sorted once, then reserved for
 * the lifetime of the process: disconnecting P1 never promotes P2.
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0600
#include <windows.h>
#include <setupapi.h>
#include <hidsdi.h>
#include <hidpi.h>
#include <xinput.h>
#include <stdlib.h>
#include <string.h>
#include "tanita_map.h"

#define PATHLEN 1024
#define REPORTLEN 1024
#define MAXCAPS 64

typedef struct {
    WCHAR path[PATHLEN];
    HANDLE file;
    PHIDP_PREPARSED_DATA pp;
    HIDP_CAPS caps;
    HIDP_VALUE_CAPS axes[5]; /* X, Y, Z, Rz, POV */
    HIDP_BUTTON_CAPS buttons;
    OVERLAPPED io;
    char report[REPORTLEN];
    int pending, valid;
    XINPUT_STATE state;
} Device;
static Device devices[2];
static DWORD retry;
static int enumerated;
static const USAGE usages[5] = {0x30, 0x31, 0x32, 0x35, 0x39};

static void close_device(Device *d) {
    if (d->file && d->file != INVALID_HANDLE_VALUE) {
        CancelIo(d->file);
        /* Complete cancellation before reusing the OVERLAPPED or buffer. */
        if (d->pending) {
            DWORD bytes;
            GetOverlappedResult(d->file, &d->io, &bytes, TRUE);
        }
        CloseHandle(d->file);
    }
    if (d->io.hEvent) CloseHandle(d->io.hEvent);
    if (d->pp) HidD_FreePreparsedData(d->pp);
    d->file = NULL; d->pp = NULL;
    ZeroMemory(&d->io, sizeof(d->io));
    ZeroMemory(&d->state, sizeof(d->state));
    d->pending = d->valid = 0;
}

static int open_device(Device *d, const WCHAR *path) {
    HIDD_ATTRIBUTES a;
    HIDP_VALUE_CAPS vc[MAXCAPS];
    HIDP_BUTTON_CAPS bc[MAXCAPS];
    USHORT count;
    unsigned i, j, found = 0;
    HANDLE h = CreateFileW(path, 0, FILE_SHARE_READ | FILE_SHARE_WRITE,
                           NULL, OPEN_EXISTING, 0, NULL);
    if (h == INVALID_HANDLE_VALUE) return 0;
    ZeroMemory(&a, sizeof(a)); a.Size = sizeof(a);
    if (!HidD_GetAttributes(h, &a) || a.VendorID != 0x1f4f ||
        a.ProductID != 0x9001 || a.VersionNumber != 0x0200 ||
        !HidD_GetPreparsedData(h, &d->pp)) goto fail;
    if (HidP_GetCaps(d->pp, &d->caps) != HIDP_STATUS_SUCCESS ||
        d->caps.UsagePage != 1 || d->caps.Usage != 5 ||
        d->caps.InputReportByteLength > REPORTLEN ||
        d->caps.InputReportByteLength < 2 ||
        d->caps.NumberInputValueCaps > MAXCAPS ||
        d->caps.NumberInputButtonCaps > MAXCAPS) goto fail;
    count = MAXCAPS;
    if (HidP_GetValueCaps(HidP_Input, vc, &count, d->pp) != HIDP_STATUS_SUCCESS) goto fail;
    for (i = 0; i < count; ++i) {
        if (vc[i].UsagePage != 1 || (!vc[i].IsRange && vc[i].ReportCount != 1) ||
            vc[i].BitSize == 0 || vc[i].BitSize > 32 ||
            vc[i].LogicalMax <= vc[i].LogicalMin) continue;
        for (j = 0; j < 5; ++j) {
            if ((!vc[i].IsRange && vc[i].NotRange.Usage == usages[j]) ||
                (vc[i].IsRange && vc[i].Range.UsageMin <= usages[j] &&
                 vc[i].Range.UsageMax >= usages[j])) {
                if (found & (1u << j)) goto fail; /* ambiguous descriptor */
                d->axes[j] = vc[i]; found |= 1u << j;
            }
        }
    }
    if (found != 31) goto fail;
    count = MAXCAPS;
    if (HidP_GetButtonCaps(HidP_Input, bc, &count, d->pp) != HIDP_STATUS_SUCCESS) goto fail;
    found = 0;
    for (i = 0; i < count; ++i) {
        if (bc[i].UsagePage == 9 && bc[i].IsRange &&
            bc[i].Range.UsageMin == 1 && bc[i].Range.UsageMax >= 13) {
            if (found++) goto fail;
            d->buttons = bc[i];
        }
    }
    if (!found) goto fail;
    /* This hardware profile accepts a single complete report. Reject other
     * layouts instead of combining partial reports into stale lever state. */
    for (i = 0; i < 5; ++i)
        if (d->axes[i].ReportID != d->buttons.ReportID) goto fail;
    CloseHandle(h);
    d->file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
                         NULL, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, NULL);
    if (d->file == INVALID_HANDLE_VALUE) { d->file = NULL; close_device(d); return 0; }
    d->io.hEvent = CreateEventW(NULL, TRUE, FALSE, NULL);
    if (!d->io.hEvent) { close_device(d); return 0; }
    return 1;
fail:
    CloseHandle(h); close_device(d); return 0;
}

static int path_compare(const void *a, const void *b) {
    return _wcsicmp((const WCHAR *)a, (const WCHAR *)b);
}

static void discover(void) {
    GUID guid;
    HDEVINFO set;
    SP_DEVICE_INTERFACE_DATA iface;
    WCHAR paths[2][PATHLEN] = {{0}};
    unsigned count = 0, i, j;
    DWORD now = GetTickCount();
    if (enumerated && (DWORD)(now - retry) < 1000) return;
    enumerated = 1; retry = now;
    /* Reserved disconnected paths reopen in place. */
    for (i = 0; i < 2; ++i)
        if (devices[i].path[0] && !devices[i].file)
            open_device(&devices[i], devices[i].path);
    if (devices[0].path[0] && devices[1].path[0]) return;
    HidD_GetHidGuid(&guid);
    set = SetupDiGetClassDevsW(&guid, NULL, NULL, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
    if (set == INVALID_HANDLE_VALUE) return;
    ZeroMemory(&iface, sizeof(iface)); iface.cbSize = sizeof(iface);
    for (i = 0; SetupDiEnumDeviceInterfaces(set, NULL, &guid, i, &iface); ++i) {
        DWORD size = 0;
        PSP_DEVICE_INTERFACE_DETAIL_DATA_W detail;
        Device probe;
        SetupDiGetDeviceInterfaceDetailW(set, &iface, NULL, 0, &size, NULL);
        if (!size || size > 16384) continue;
        detail = (PSP_DEVICE_INTERFACE_DETAIL_DATA_W)malloc(size);
        if (!detail) break;
        detail->cbSize = sizeof(*detail);
        if (SetupDiGetDeviceInterfaceDetailW(set, &iface, detail, size, NULL, NULL) &&
            wcslen(detail->DevicePath) < PATHLEN) {
            int known = 0;
            for (j = 0; j < 2; ++j)
                if (!_wcsicmp(devices[j].path, detail->DevicePath)) known = 1;
            ZeroMemory(&probe, sizeof(probe));
            if (!known && open_device(&probe, detail->DevicePath)) {
                close_device(&probe);
                /* Keep the lexically first two regardless of enumeration order. */
                if (count < 2) wcscpy(paths[count++], detail->DevicePath);
                else if (_wcsicmp(detail->DevicePath, paths[1]) < 0)
                    wcscpy(paths[1], detail->DevicePath);
                qsort(paths, count, sizeof(paths[0]), path_compare);
            }
        }
        free(detail);
    }
    SetupDiDestroyDeviceInfoList(set);
    j = 0;
    for (i = 0; i < 2 && j < count; ++i) {
        if (devices[i].path[0]) continue;
        wcscpy(devices[i].path, paths[j++]);
        open_device(&devices[i], devices[i].path);
    }
}

static int decode(Device *d) {
    int32_t value[5];
    ULONG raw, n = 32;
    USAGE pressed[32];
    unsigned i;
    unsigned buttons = 0;
    TanitaState mapped;
    if ((BYTE)d->report[0] != d->buttons.ReportID) return 0;
    for (i = 0; i < 5; ++i) {
        HIDP_VALUE_CAPS *c = &d->axes[i];
        if (HidP_GetUsageValue(HidP_Input, 1, c->LinkCollection, usages[i],
              &raw, d->pp, d->report, d->caps.InputReportByteLength) != HIDP_STATUS_SUCCESS) return 0;
        value[i] = (LONG)raw;
        if (c->LogicalMin < 0 && c->BitSize < 32)
            value[i] = (LONG)(raw << (32 - c->BitSize)) >> (32 - c->BitSize);
    }
    if (HidP_GetUsages(HidP_Input, 9, d->buttons.LinkCollection, pressed, &n,
          d->pp, d->report, d->caps.InputReportByteLength) != HIDP_STATUS_SUCCESS) return 0;
    for (i = 0; i < n; ++i)
        if (pressed[i] >= 1 && pressed[i] <= 13) buttons |= 1u << (pressed[i] - 1);
    for (i = 0; i < 4; ++i)
        if (value[i] < d->axes[i].LogicalMin || value[i] > d->axes[i].LogicalMax) return 0;
    mapped = tanita_map(value, buttons, d->axes[0].LogicalMin, d->axes[0].LogicalMax,
                        d->axes[1].LogicalMin, d->axes[1].LogicalMax,
                        d->axes[2].LogicalMin, d->axes[2].LogicalMax,
                        d->axes[3].LogicalMin, d->axes[3].LogicalMax,
                        d->axes[4].LogicalMin, d->axes[4].LogicalMax);
    ++d->state.dwPacketNumber;
    d->state.Gamepad.wButtons = mapped.buttons;
    d->state.Gamepad.bLeftTrigger = mapped.lt;
    d->state.Gamepad.bRightTrigger = mapped.rt;
    d->state.Gamepad.sThumbLX = mapped.x;
    d->state.Gamepad.sThumbLY = mapped.y;
    d->state.Gamepad.sThumbRX = mapped.z;
    d->state.Gamepad.sThumbRY = mapped.rz;
    d->valid = 1;
    return 1;
}

DWORD WINAPI TanitaGetState(DWORD index, XINPUT_STATE *state) {
    Device *d;
    DWORD bytes;
    unsigned drain;
    if (!state || index >= 2) return ERROR_BAD_ARGUMENTS;
    ZeroMemory(state, sizeof(*state));
    if (!devices[index].file) discover();
    d = &devices[index];
    if (!d->file) return ERROR_DEVICE_NOT_CONNECTED;
    /* Bounded drain: one chatty device cannot stall the game loop. */
    for (drain = 0; drain < 64; ++drain) {
        if (d->pending) {
            if (!GetOverlappedResult(d->file, &d->io, &bytes, FALSE)) {
                if (GetLastError() == ERROR_IO_INCOMPLETE) break;
                close_device(d); return ERROR_DEVICE_NOT_CONNECTED;
            }
            d->pending = 0;
        } else {
            ResetEvent(d->io.hEvent);
            if (!ReadFile(d->file, d->report, d->caps.InputReportByteLength, &bytes, &d->io)) {
                if (GetLastError() == ERROR_IO_PENDING) { d->pending = 1; break; }
                close_device(d); return ERROR_DEVICE_NOT_CONNECTED;
            }
        }
        if (bytes != d->caps.InputReportByteLength || !decode(d)) {
            d->valid = 0; ZeroMemory(&d->state, sizeof(d->state));
        }
    }
    if (!d->valid) return ERROR_DEVICE_NOT_CONNECTED;
    *state = d->state;
    return ERROR_SUCCESS;
}
