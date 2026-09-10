#!/usr/bin/env python3
"""Check profile availability and execute controller blobs with mocked XInput.

No game files are needed. Unicorn exercises the assembled x86 routines;
Windows input delivery and in-game behaviour still need a real play test.
"""
import importlib.util
import os
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    spec = importlib.util.spec_from_file_location('vp', os.path.join(ROOT, 'v-on-patcher.py'))
    vp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vp)
    return vp


def tables(vp, build):
    custom = build.short in ('retail', 'jpre')
    names = ['Gamepad (XInput)', 'Twin-stick (XInput)',
             'Keyboard (Simple)', 'Keyboard (Real)']
    if custom:
        names[2:2] = ['Twin-Stick (Custom)', 'Twin-Stick (Tanita)', 'Twin-Stick (HORI EX)']
    strings = vp.link('PAD_PROFILES', build)
    base = vp.cave_va('PAD_PROFILES', build)
    pointers = struct.unpack('<8I', vp.link('PAD_DEVLIST', build))
    actual = [strings[p - base:].split(b'\0')[0].decode() for p in pointers if p]
    assert actual == names, (build.short, actual)
    assert pointers[len(names):] == (0,) * (8 - len(names))
    rows = vp.by_key(build)['padxinput'][2]
    for retail, jpre, player in ((0x422b4, 0x41974, 1), (0x1bc147, 0x1b6ab7, 2)):
        target = struct.pack('<I', vp.symbol_va(('TWIN', 'custom%dp' % player), build)).hex()
        matches = [off for off, _old, new in rows if new == target]
        assert matches == ([retail if build.short == 'retail' else jpre] if custom else [])
    if custom:
        for site, target in ((0x96739, 'SPENDNONE'), (0x95be4, ('CUSTOM', 'page'))):
            offset = site if build.short == 'retail' else build.sites[site][0]
            actual = next(new for off, _old, new in rows if off == offset)
            assert actual == struct.pack('<I', vp.symbol_va(target, build)).hex()

    # Every new site is absent from unverified builds. On verified builds,
    # check startup, spending, dialog and INI routes as well as gameplay.
    hardware_sites = {
        0x422b8: ('TWIN','tanita1p'), 0x1bc14b: ('TWIN','tanita2p'),
        0x422bc: ('TWIN','hori1p'), 0x1bc14f: ('TWIN','hori2p'),
        0x9521b: 'JOYCHECKOK', 0x9521f: 'JOYCHECKOK',
        0x9673d: 'SPENDNONE', 0x96741: 'SPENDNONE',
        0x95be8: 'NODIALOG', 0x96263: 'SAVENONE', 0x96267: 'SAVENONE'}
    assert set(hardware_sites) | {0x958a3, 0x958a4} <= vp.CUSTOM_DISPATCH_SITES
    if custom:
        for site, target in hardware_sites.items():
            offset = site if build.short == 'retail' else build.sites[site][0]
            actual = next(new for off, _old, new in rows if off == offset)
            assert actual == struct.pack('<I', vp.symbol_va(target, build)).hex()
        for site in (0x958a3, 0x958a4):
            offset = site if build.short == 'retail' else build.sites[site][0]
            assert next(new for off, _old, new in rows if off == offset) == '03'


def emulate(vp, build, ucmod, regs):
    uc = ucmod.Uc(ucmod.UC_ARCH_X86, ucmod.UC_MODE_32)
    uc.mem_map(0x400000, 0x4000000)
    stack, stop, xinput = 0x10000000, 0x10001000, 0x10001100
    uc.mem_map(stack, 0x2000)
    sym = lambda name: vp.symbol_va(name, build)
    for name in ('DEVORDER', 'TWIN', 'PADX', 'PAD_COND', 'LEVERS', 'CUSTOM'):
        uc.mem_write(vp.cave_va(name, build), vp.link(name, build))
    epilogue = sym(('PADX', 'epilogue'))
    uc.mem_write(epilogue, b'\xe9' + struct.pack('<i', vp.cave_va('LEVERS', build) - epilogue - 5))
    # The fake XInputGetState succeeds, preserving the input supplied below.
    uc.mem_write(xinput, bytes.fromhex('31c0c20800'))
    for name in ('KBD1P', 'KBD2P', 'CAMSKIP'):
        uc.mem_write(sym(name), b'\xc3')

    def word(name, value):
        uc.mem_write(sym(name), struct.pack('<I', value))

    def run(entry, end=stop):
        uc.reg_write(regs.UC_X86_REG_ESP, stack + 0x100)
        uc.mem_write(stack + 0x100, struct.pack('<I', stop))
        uc.emu_start(sym(entry), end, count=10000)
        assert uc.reg_read(regs.UC_X86_REG_EIP) == end, (build.short, entry)

    # Execute both directions of the F7 mapping for each player and profile.
    order = [1, 2, 4, 5, 6, 3, 0] if build.short in ('retail', 'jpre') else [1, 2, 3, 0]
    frame = stack + 0x800
    for player in range(2):
        for pos, device in enumerate(order):
            uc.mem_write(sym('BLOCKS') + player * 0x70, struct.pack('<I', device))
            uc.reg_write(regs.UC_X86_REG_EAX, player * 0x70)
            run(('DEVORDER', 'posshim'))
            assert uc.reg_read(regs.UC_X86_REG_EAX) == pos
            uc.reg_write(regs.UC_X86_REG_EBP, frame)
            uc.mem_write(frame + sym('DEVSEL'), struct.pack('<I', pos))
            uc.mem_write(frame + sym('DEVNUM'), struct.pack('<I', player))
            run(('DEVORDER', 'devshim'))
            assert uc.reg_read(regs.UC_X86_REG_EAX) == device
            assert uc.reg_read(regs.UC_X86_REG_ECX) == player

    word('XIFN', xinput)
    # A hidden legacy device 4 must not consume the first pad ahead of 2P.
    for device in (0, 1, 2, 3, 4, 5, 6):
        word('PADIDX', 0)
        uc.mem_write(sym('DEVICES'), struct.pack('<II', device, 1))
        uc.reg_write(regs.UC_X86_REG_EAX, 1)
        uc.reg_write(regs.UC_X86_REG_EDX, sym('STATE'))
        run(('PADX', 'padpoll'))
        uses_pad = device in (1, 2) or (device in (4, 6) and len(order) == 7)
        assert bytes(uc.mem_read(sym('PADIDX'), 2)) == (b'\x01\x02' if uses_pad else b'\x05\x01')

    if len(order) != 7:
        return
    # Every profile pairing allocates each API independently, P1 first.
    word(('PADX', 'tanitafn'), xinput)
    calls = []
    def record(_uc, address, _size, _data):
        if address == xinput:
            sp = _uc.reg_read(regs.UC_X86_REG_ESP)
            calls.append(struct.unpack('<I', _uc.mem_read(sp + 4, 4))[0])
    hook = uc.hook_add(ucmod.UC_HOOK_CODE, record)
    uc.ctl_remove_cache(xinput, xinput + 5)
    for first in order:
        for second in order:
            uc.mem_write(sym('DEVICES'), struct.pack('<II', first, second))
            word('PADIDX', 0)
            for player, device in enumerate((first, second)):
                if device not in (1, 2, 4, 5, 6):
                    continue
                calls.clear()
                uc.reg_write(regs.UC_X86_REG_EAX, player)
                uc.reg_write(regs.UC_X86_REG_EDX, sym('STATE'))
                run(('PADX', 'padpoll'))
                expected = int(player == 1 and ((first == 5) if device == 5 else first in (1, 2, 4, 6)))
                assert calls[-1] == expected, (first, second, player, calls)
    uc.hook_del(hook)
    uc.mem_write(sym('DEVICES'), struct.pack('<II', 4, 4))
    word('MODE', 4)
    word('SUBMODE', 8)
    # (wButtons, LT, RT, expected left mask, expected right mask).
    cases = [(0, 0, 0, 0, 0),
             (1, 0, 0, 0x20, 0), (2, 0, 0, 0x10, 0),
             (4, 0, 0, 0x80, 0), (8, 0, 0, 0x40, 0),
             (0x8000, 0, 0, 0, 0x20), (0x1000, 0, 0, 0, 0x10),
             (0x4000, 0, 0, 0, 0x80), (0x2000, 0, 0, 0, 0x40),
             (0, 255, 0, 1, 0), (0, 0, 255, 0, 1),
             (0x100, 0, 0, 2, 0), (0x200, 0, 0, 0, 2)]
    for player in (1, 2):
        for buttons, lt, rt, left, right in cases:
            word('PADIDX', 0x0201)
            uc.mem_write(sym('BTN'), struct.pack('<HBBhhhh', buttons, lt, rt, 0, 0, 0, 0))
            for side in (1, 2):
                for lever in ('A', 'B'):
                    uc.mem_write(sym('LEV%d%s' % (side, lever)), b'\xff\xff')
            run(('TWIN', 'custom%dp' % player), sym('EXIT%dP' % player))
            for side in (1, 2):
                for lever, mask in (('A', left), ('B', right)):
                    actual = struct.unpack('<H', uc.mem_read(sym('LEV%d%s' % (side, lever)), 2))[0]
                    expected = 0xffff ^ mask if side == player else 0xffff
                    assert actual == expected, (build.short, player, buttons, lt, rt, lever, hex(actual), hex(expected))

    # A reassigned D-pad must not also fire its old gameplay direction.
    original = bytes(uc.mem_read(sym(('CUSTOM', 'binds1')),24))
    uc.mem_write(sym(('CUSTOM', 'binds1')), bytes.fromhex('e000') + b'\0'*22)
    uc.mem_write(sym('DEVICES'), struct.pack('<II',4,0))
    for mode, buttons, mask in ((4,1,0),(4,0x1000,0x20),(0,1,0x20)):
        word('MODE',mode)
        word('PADIDX',0x0501)
        uc.mem_write(sym('BTN'),struct.pack('<HBBhhhh',buttons,0,0,0,0,0,0))
        uc.mem_write(sym('LEV1A'),b'\xff\xff\xff\xff')
        run(('TWIN','custom1p'),sym('EXIT1P'))
        assert struct.unpack('<H',uc.mem_read(sym('LEV1A'),2))[0] == 0xffff ^ mask
        assert bytes(uc.mem_read(sym('LEV1B'),2)) == b'\xff\xff'
    word('MODE',4)
    uc.mem_write(sym(('CUSTOM', 'binds1')),original)

    # Hardware profile directions, diagonals, triggers and dashes per side.
    # Raw XInput Y is positive up; Tanita's reader normalizes HID Y to that.
    word('DZTHR1', 13000)
    uc.mem_write(sym('DZTHR1') + 4, struct.pack('<I', 13000))
    for profile, device in (('stub', 2), ('tanita', 5), ('hori', 6)):
        uc.mem_write(sym('DEVICES'), struct.pack('<II', device, device))
        inputs = [(0, 0, 0, 0, 0, 0, 0, 0, 0)]
        for sign, axis, left, right in ((1,1,0x20,0),(-1,1,0x10,0),
                (-1,0,0x80,0),(1,0,0x40,0),(1,3,0,0x20),(-1,3,0,0x10),
                (-1,2,0,0x80),(1,2,0,0x40)):
            axes = [0]*4
            buttons = 0
            if profile == 'hori' and axis < 2:
                buttons = {0x20:1,0x10:2,0x80:4,0x40:8}[left]
            else:
                axes[axis] = sign*32767
            inputs.append((buttons,0,0,*axes,left,right))
        inputs += [(0,255,255,0,0,0,0,1,1), (0x300,0,0,0,0,0,0,2,2),
                   (9 if profile == 'hori' else 0,0,0,
                    0 if profile == 'hori' else 32767,
                    0 if profile == 'hori' else 32767,32767,32767,0x60,0x60)]
        for player in (1, 2):
            for buttons, lt, rt, lx, ly, rx, ry, left, right in inputs:
                word('PADIDX', 0x0201)
                uc.mem_write(sym('BTN'), struct.pack('<HBBhhhh', buttons,lt,rt,lx,ly,rx,ry))
                for side in (1,2):
                    for lever in ('A','B'):
                        uc.mem_write(sym('LEV%d%s' % (side,lever)), b'\xff\xff')
                run(('TWIN', '%s%dp' % (profile,player)), sym('EXIT%dP' % player))
                for side in (1,2):
                    for lever,mask in (('A',left),('B',right)):
                        got = struct.unpack('<H',uc.mem_read(sym('LEV%d%s' % (side,lever)),2))[0]
                        assert got == (0xffff ^ mask if side == player else 0xffff), (profile,player,inputs,hex(got))

    # Tanita Options/Cross still reach the window during pause without XInput.
    post = xinput + 0x40
    uc.mem_write(post, bytes.fromhex('31c0c21000'))
    word('POSTMSG', post)
    word('XIFN', 1)
    uc.mem_write(sym('DEVICES'), struct.pack('<II', 5, 0))
    uc.mem_write(sym(('PADX', 'tanitaprev')), b'\0'*4)
    events = []
    def posted(_uc, address, _size, _data):
        if address == post:
            sp = _uc.reg_read(regs.UC_X86_REG_ESP)
            events.append(struct.unpack('<4I', _uc.mem_read(sp + 4,16)))
    uc.hook_add(ucmod.UC_HOOK_CODE, posted)
    uc.mem_write(sym('PBTN'), struct.pack('<H',0x1010))
    run(('PADX','pollpads'))
    assert [event[2] for event in events] == [0x72,0x20]
    events.clear()
    run(('PADX','pollpads'))
    assert not events
    uc.mem_write(sym('PBTN'), b'\0\0')
    run(('PADX','pollpads'))
    uc.mem_write(sym('PBTN'), struct.pack('<H',0x10))
    run(('PADX','pollpads'))
    assert [event[2] for event in events] == [0x72]


def main():
    vp = load()
    try:
        import unicorn
        from unicorn import x86_const
    except ImportError:
        if os.environ.get('CI') == 'true':
            raise
        unicorn = None
        print('note: no python3-unicorn; controller execution was not tested')
    for build in vp.BUILDS.values():
        tables(vp, build)
        if unicorn:
            emulate(vp, build, unicorn, x86_const)
        print('%s: controller checks passed' % build.name)


if __name__ == '__main__':
    main()
