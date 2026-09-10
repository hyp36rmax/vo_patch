#!/usr/bin/env python3
"""Native mapping, PE packaging and safe helper installation checks.

Real Windows HID delivery (including unplug/replug and two physical units)
remains a hardware acceptance test. These checks do not claim to emulate it.
"""
import os
import hashlib
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from controllertest import load

ROOT = Path(__file__).resolve().parent.parent


def main():
    subprocess.run([sys.executable, str(ROOT / 'input/build.py'), '--check'], check=True)
    vp = load()
    blob = vp.tanita_dll()
    pe = struct.unpack_from('<I', blob, 0x3c)[0]
    assert blob[pe:pe + 4] == b'PE\0\0'
    assert struct.unpack_from('<H', blob, pe + 4)[0] == 0x14c
    assert struct.unpack_from('<H', blob, pe + 24)[0] == 0x10b
    assert b'TanitaGetState\0' in blob
    with tempfile.TemporaryDirectory() as folder:
        vp.install_tanita(folder)
        vp.install_tanita(folder)
        dest = Path(folder) / 'vontanita.dll'
        assert dest.read_bytes() == blob
        previous = b'previous verified helper fixture'
        old_allowlist = vp.TANITA_PREVIOUS_DLL_SHAS
        vp.TANITA_PREVIOUS_DLL_SHAS = frozenset((hashlib.sha256(previous).hexdigest(),))
        dest.write_bytes(previous)
        vp.install_tanita(folder)
        assert dest.read_bytes() == blob
        vp.TANITA_PREVIOUS_DLL_SHAS = old_allowlist
        dest.write_bytes(b'foreign DLL')
        try:
            vp.install_tanita(folder)
        except ValueError:
            pass
        else:
            raise AssertionError('foreign DLL was overwritten')
        assert dest.read_bytes() == b'foreign DLL'
        cc = shutil.which(os.environ.get('CC', 'cc'))
        if not cc:
            raise SystemExit('C compiler required for Tanita mapping tests')
        source = Path(folder) / 'mapping.c'
        source.write_text(r'''
#include <assert.h>
#include "tanita_map.h"
#include "controller_logic.h"
static TanitaState map(int32_t *v, unsigned b) {
    return tanita_map(v,b,0,255,0,255,0,255,0,255,0,7);
}
int main(void) {
    int32_t v[5] = {128,128,128,128,8};
    TanitaState s = map(v,0);
    assert(!s.buttons && !s.x && !s.y && !s.z && !s.rz && !s.lt && !s.rt);
    /* Full diagonals on both levers, both triggers and both auxiliary pairs. */
    v[0]=255; v[1]=0; v[2]=0; v[3]=255;
    s=map(v,(1u<<4)|(1u<<5)|(1u<<10)|(1u<<11));
    assert(s.x==32767 && s.y==32767 && s.z==-32767 && s.rz==-32767);
    assert(s.lt==255 && s.rt==255 && s.buttons==0x300);
    /* Face buttons, Share, Options, stick presses; PS has no gameplay action. */
    s=map(v,0x1fcf);
    assert(s.buttons==0xf3f0);
    s=map(v,1u<<12); assert(!s.buttons && !s.lt && !s.rt);
    /* September 10 diagnostic: top 6/7 with both levers held up. */
    v[0]=v[2]=128; v[1]=v[3]=0;
    s=map(v,1u<<6); assert(s.buttons==0x140 && s.y==32767 && s.rz==32767);
    s=map(v,1u<<7); assert(s.buttons==0x280 && s.y==32767 && s.rz==32767);
    /* Independent legacy dash aliases remain supported. */
    s=map(v,1u<<10); assert(s.buttons==0x100);
    s=map(v,1u<<11); assert(s.buttons==0x200);
    /* Hat includes diagonal combinations and null, independent of axes. */
    static const unsigned hats[9]={1,9,8,10,2,6,4,5,0};
    for(int i=0;i<9;++i) { v[4]=i; s=map(v,0); assert(s.buttons==hats[i]); }
    /* Every possible 8-bit axis sample: inclusive neutral band, no analog VO. */
    for(int i=0;i<256;++i) {
        v[0]=v[1]=v[2]=v[3]=i; s=map(v,0);
        int expected=i<=63?-32767:i>=192?32767:0;
        assert(s.x==expected && s.z==expected && s.y==-expected && s.rz==-expected);
    }
    /* Signed descriptor ranges and exact quarter-range boundaries. */
    assert(tanita_axis(-100,-100,100,0)==-32767);
    assert(tanita_axis(-50,-100,100,0)==0);
    assert(tanita_axis(50,-100,100,0)==0);
    assert(tanita_axis(100,-100,100,0)==32767);
    /* Every sparse/reversed connection ordering is explicitly claimable. */
    for(int first=0;first<6;++first) for(int second=0;second<6;++second) {
        if(first==second) continue;
        VonOwner owner[2]={{-1,0},{-1,0}};
        assert(von_claim(owner,0,first)); assert(von_claim(owner,1,second));
        assert(owner[0].source==first && owner[1].source==second);
        assert(von_owned_source(owner,0,first>=4?5:4));
        assert(!von_owned_source(owner,0,first>=4?4:5));
        assert(!von_owned_source(owner,2,4));
        assert(von_claim(owner,0,second));
        assert(owner[0].source==second && owner[1].source!=second);
        if((first>=4)==(second>=4)) assert(owner[1].source==first);
        else assert(owner[1].source==-1 && !owner[1].attempted);
    }
    VonCapture capture={0};
    assert(!von_capture(&capture,1)); /* held on entry */
    assert(!von_capture(&capture,0));
    assert(!von_capture(&capture,3)); /* chord rejected; require release */
    assert(!von_capture(&capture,1));
    for(unsigned i=0;i<20;++i) {
        assert(!von_capture(&capture,0));
        assert(von_capture(&capture,1u<<i)==(int)(0xe0+i));
        assert(!von_capture(&capture,1u<<i));
    }
    assert(von_inputs(0xf30f,255,255,0,0,0,0,13000)==0xf00ff);
    assert(!von_inputs(0x30,64,64,13000,-13000,0,0,13000));
    assert(von_inputs(0,0,0,-32767,32767,32767,-32767,13000)==0xa500);
    return 0;
}
''')
        exe = Path(folder) / 'mapping'
        subprocess.run([cc, '-std=c99', '-Wall', '-Wextra', '-Werror',
                        '-I', str(ROOT / 'input'), str(source), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    print('Tanita: digital mapping, 32-bit helper and installation passed')


if __name__ == '__main__':
    main()
