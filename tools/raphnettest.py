#!/usr/bin/env python3
"""Raphnet identity/decoder/claim rules and emitted x86 integration.

Synthetic HID values and mocked Windows calls are not physical validation.
Run the acceptance checklist on Windows before committing this milestone.
"""
import os
import itertools
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from controllertest import load

ROOT = Path(__file__).resolve().parent.parent


def native_rules():
    cc = shutil.which(os.environ.get('CC', 'cc'))
    if not cc:
        raise SystemExit('C compiler required for Raphnet checks')
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'test.c'
        source.write_text(r'''
#include <assert.h>
#include "raphnet_map.h"
#include "controller_logic.h"
int main(void) {
    for(unsigned rev=0;rev<65536;++rev) {
        assert(von_hid_identity(0x289b,8,rev)==VON_HID_DC_V1);
        assert(von_hid_identity(0x289b,0x43,rev)==VON_HID_SATURN_V2);
        assert(von_hid_identity(0x1f4f,0x9001,rev)==(rev==0x200?0:-1));
    }
    assert(von_hid_identity(0x289b,0x9001,0x200)==-1);
    assert(von_hid_identity(0x1f4f,8,0x100)==-1);
    assert(von_hid_identity(0x289b,0xffff,0)==-1);
    /* Independent physical-source expectations, including unmapped B0/B8. */
    const unsigned dc[16]={0,VON_RIGHT_TOP,VON_RIGHT_TRIGGER,VON_START,
        VON_LEFT_UP,VON_LEFT_DOWN,VON_LEFT_LEFT,VON_LEFT_RIGHT,0,
        VON_LEFT_TOP,VON_LEFT_TRIGGER,VON_PAUSE,VON_RIGHT_UP,VON_RIGHT_DOWN,
        VON_RIGHT_LEFT,VON_RIGHT_RIGHT};
    for(unsigned b=0;b<65536;++b) {
        unsigned expected=0;
        for(unsigned i=0;i<16;++i) if(b&(1u<<i)) expected|=dc[i];
        assert(raphnet_dc_v1(b)==expected);
    }
    const unsigned saturn[9]={VON_RIGHT_LEFT,VON_RIGHT_TRIGGER,VON_RIGHT_DOWN,
        VON_RIGHT_UP,VON_RIGHT_RIGHT,VON_RIGHT_TOP,VON_LEFT_TRIGGER,VON_LEFT_TOP,VON_START};
    const int values[3]={0,128,255};
    for(unsigned b=0;b<512;++b) for(unsigned x=0;x<3;++x) for(unsigned y=0;y<3;++y) {
        unsigned expected=0;
        for(unsigned i=0;i<9;++i) if(b&(1u<<i)) expected|=saturn[i];
        if(x==0) expected|=VON_LEFT_LEFT;
        if(x==2) expected|=VON_LEFT_RIGHT;
        if(y==0) expected|=VON_LEFT_UP;
        if(y==2) expected|=VON_LEFT_DOWN;
        unsigned actual=raphnet_saturn_v2(b,values[x],values[y],0,255,0,255);
        assert(actual==expected && !(actual&VON_PAUSE));
    }
    for(int v=0;v<256;++v) assert(raphnet_axis(v,0,255)==(v<=63?-1:v>=192?1:0));
    assert(raphnet_axis(-50,-100,100)==0 && raphnet_axis(50,-100,100)==0);
    assert(raphnet_axis(INT32_MIN,INT32_MIN,INT32_MAX)==-1);
    assert(raphnet_axis(INT32_MAX,INT32_MIN,INT32_MAX)==1);
    assert(raphnet_axis(-1,0,255)==0 && raphnet_axis(256,0,255)==0);
    assert(raphnet_axis(0,0,0)==0);
    for(int a=0;a<10;++a) for(int b=0;b<10;++b) {
        if(a==b) continue;
        VonOwner owners[2]={{-1,0},{-1,0}};
        unsigned ready=0, connected=(1u<<a)|(1u<<b);
        assert(von_start_edge(&ready,connected,connected)==-1); /* held on entry */
        assert(von_start_edge(&ready,connected,0)==-1);
        assert(von_start_edge(&ready,connected,connected)==-2); /* ambiguous */
        assert(von_start_edge(&ready,connected,0)==-1);
        assert(von_start_edge(&ready,connected,1u<<a)==a);
        assert(von_start_edge(&ready,connected,1u<<a)==-1); /* held */
        assert(von_claim(owners,0,a) && von_claim(owners,1,b));
        for(unsigned kind=0;kind<10;++kind) {
            int family=von_kind_family(kind);
            assert(von_owned_source(owners,0,kind)==(family==von_source_family(a)));
            if(family>=0) assert(von_source_first(kind)<=a && a<von_source_end(kind)
                                ? family==von_source_family(a) : family!=von_source_family(a));
        }
        assert(von_claim(owners,0,b));
        assert(owners[0].source==b);
        assert(owners[1].source==(von_source_family(a)==von_source_family(b)?a:-1));
        ready=1u<<a;
        assert(von_start_edge(&ready,0,0)==-1 && ready==0); /* disconnect */
        assert(von_start_edge(&ready,1u<<a,1u<<a)==-1); /* reconnect held */
    }
    VonOwner owners[2]={{-1,0},{-1,0}};
    assert(!von_claim(owners,0,10) && !von_claim(owners,2,0));
    /* Existing capture rules still use their original Xbox input ids. */
    VonCapture capture={0};
    assert(!von_capture(&capture,0));
    assert(von_capture(&capture,von_inputs(1,0,0,0,0,0,0,13000))==0xf0);
    return 0;
}
''')
        binary = Path(folder) / 'test'
        subprocess.run([cc, '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-I', str(ROOT / 'input'), str(source), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


def integration(vp, build):
    import unicorn as u
    from unicorn import x86_const as r
    uc = u.Uc(u.UC_ARCH_X86, u.UC_MODE_32)
    uc.mem_map(0x400000, 0x4000000)
    uc.mem_map(0x10000000, 0x3000)
    stack, stop, helper, post, select = 0x10001000, 0x10002000, 0x10002100, 0x10002200, 0x10002300
    sym = lambda name: vp.symbol_va(name, build)
    for name in ('RAPH', 'PADX', 'TWIN', 'LEVERS', 'COMMITDEV'):
        uc.mem_write(vp.cave_va(name, build), vp.link(name, build))
    ep = sym(('PADX', 'epilogue'))
    uc.mem_write(ep, b'\xe9' + struct.pack('<i', vp.cave_va('LEVERS', build) - ep - 5))
    for name in ('KBD1P', 'KBD2P', 'CAMSKIP'):
        uc.mem_write(sym(name), b'\xc3')
    uc.mem_write(helper, bytes.fromhex('31c0c20c00'))
    uc.mem_write(post, bytes.fromhex('31c0c21000'))
    uc.mem_write(select, bytes.fromhex('b801000000c20c00'))
    controls, failed, events, claims, reads = [0, 0], [False, False], [], [], []

    def word(name, value):
        uc.mem_write(sym(name), struct.pack('<I', value))

    def callback(_uc, address, _size, _data):
        sp = uc.reg_read(r.UC_X86_REG_ESP)
        if address == helper:
            player, kind, target = struct.unpack('<3I', uc.mem_read(sp+4, 12))
            assert player < 2 and kind in (7, 8)
            reads.append((player, kind))
            uc.mem_write(target, struct.pack('<I', 0 if failed[player] else controls[player]))
            # Skip xor eax,eax, preserving the stdcall return and failure code.
            uc.reg_write(r.UC_X86_REG_EAX, 1167 if failed[player] else 0)
            uc.reg_write(r.UC_X86_REG_EIP, helper+2)
        elif address == post:
            events.append(struct.unpack('<4I', uc.mem_read(sp+4, 16)))
        elif address == select:
            claims.append(struct.unpack('<3I', uc.mem_read(sp+4, 12)))
    uc.hook_add(u.UC_HOOK_CODE, callback)
    word(('RAPH', 'nativefn'), helper)
    word(('PADX', 'ownedfn'), helper)  # avoid resolving for the F7 claim test
    word(('PADX', 'selectfn'), select)
    word('POSTMSG', post)
    word('XIFN', 1)  # Native controllers must not require XInput to load.
    word('MODE', 4)
    word('SUBMODE', 8)

    def run(entry, end=stop):
        uc.reg_write(r.UC_X86_REG_ESP, stack)
        uc.mem_write(stack, struct.pack('<I', stop))
        uc.emu_start(sym(entry), end, count=10000)
        assert uc.reg_read(r.UC_X86_REG_EIP) == end, (build.short, entry)
        assert uc.reg_read(r.UC_X86_REG_ESP) == stack + (4 if end == stop else 0)

    left = [0x20, 0x10, 0x80, 0x40, 0, 0, 0, 0, 1, 0, 2, 0]
    right = [0, 0, 0, 0, 0x20, 0x10, 0x80, 0x40, 0, 1, 0, 2]
    cases = [0] + [1 << i for i in range(14)] + [0xf00, 0x999, 0x555, 0xaaa]
    for devices in itertools.product(range(9), repeat=2):
        uc.mem_write(sym('DEVICES'), struct.pack('<2I', *devices))
        for player in (0, 1):
            if devices[player] not in (7, 8):
                continue
            uc.reg_write(r.UC_X86_REG_EAX, devices[player])
            uc.reg_write(r.UC_X86_REG_ECX, player)
            run(('COMMITDEV', 'commitdev'))
            assert claims[-1][1:] == (player, devices[player])
            for value in cases:
                controls[player] = value
                for side in (1, 2):
                    for lever in ('A', 'B'):
                        uc.mem_write(sym('LEV%d%s' % (side, lever)), b'\xff\xff')
                    uc.mem_write(sym('ACCEPT%d' % side), b'\0')
                uc.reg_write(r.UC_X86_REG_EAX, devices[player])
                run(('RAPH', 'dispatch%d' % (player+1)), sym('EXIT%dP' % (player+1)))
                assert reads[-1] == (player, devices[player])
                masks = [0, 0]
                for i in range(12):
                    if value & (1 << i):
                        masks[0] |= left[i]
                        masks[1] |= right[i]
                # Existing jump/guard normalization is intentionally shared.
                if masks[0] & 0x80 and masks[1] & 0x40:
                    masks[0] &= ~0x70
                    masks[1] &= ~0xb0
                elif masks[0] & 0x40 and masks[1] & 0x80:
                    masks[0] &= ~0xb0
                    masks[1] &= ~0x70
                for side in (1, 2):
                    for lever, mask in zip(('A', 'B'), masks):
                        actual = struct.unpack('<H', uc.mem_read(sym('LEV%d%s' % (side, lever)), 2))[0]
                        assert actual == (0xffff ^ mask if side == player+1 else 0xffff)
                assert uc.mem_read(sym('ACCEPT%d' % (player+1)), 1)[0] == (128 if value & 0x1000 else 0)
    # Start/Pause use separate window-message paths, work without the input
    # tick, and only fire on an edge. A Saturn decoder never emits Pause.
    uc.mem_write(sym('DEVICES'), struct.pack('<2I', 7, 8))
    controls[:] = [0, 0]
    run(('PADX', 'pollpads'))
    for player, bit, key in ((0, 0x1000, 0x20), (0, 0x2000, 0x72), (1, 0x1000, 0x20)):
        events.clear()
        controls[player] = bit
        run(('PADX', 'pollpads'))
        assert [e[2] for e in events] == [key]
        events.clear()
        run(('PADX', 'pollpads'))
        assert not events
        controls[player] = 0
        run(('PADX', 'pollpads'))
    failed[0] = True
    controls[0] = 0x3fff
    events.clear()
    run(('PADX', 'pollpads'))
    assert not events
    uc.mem_write(sym('LEV1A'), b'\xff\xff')
    uc.mem_write(sym('LEV1B'), b'\xff\xff')
    run(('RAPH', 'entry1'), sym('EXIT1P'))
    assert uc.mem_read(sym('LEV1A'), 2) == b'\xff\xff'
    assert uc.mem_read(sym('LEV1B'), 2) == b'\xff\xff'


def main():
    native_rules()
    vp = load()
    assert b'VonTwinGetState\0' in vp.tanita_dll()
    for build in (vp.RETAIL, vp.JPRE):
        integration(vp, build)
        print('%s: native Raphnet integration passed' % build.name)
    print('identity, exhaustive mappings, claim edges, family ownership: passed')


if __name__ == '__main__':
    main()
