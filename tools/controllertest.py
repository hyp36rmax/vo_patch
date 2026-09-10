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
        names.insert(2, 'Twin-Stick (Custom)')
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
        for site, target in ((0x96739, 'SPENDNONE'), (0x95be4, 'NODIALOG')):
            offset = site if build.short == 'retail' else build.sites[site][0]
            actual = next(new for off, _old, new in rows if off == offset)
            assert actual == struct.pack('<I', vp.symbol_va(target, build)).hex()


def emulate(vp, build, ucmod, regs):
    uc = ucmod.Uc(ucmod.UC_ARCH_X86, ucmod.UC_MODE_32)
    uc.mem_map(0x400000, 0x4000000)
    stack, stop, xinput = 0x10000000, 0x10001000, 0x10001100
    uc.mem_map(stack, 0x2000)
    sym = lambda name: vp.symbol_va(name, build)
    for name in ('DEVORDER', 'TWIN', 'PADX', 'PAD_COND'):
        uc.mem_write(vp.cave_va(name, build), vp.link(name, build))
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
    order = [1, 2, 4, 3, 0] if build.short in ('retail', 'jpre') else [1, 2, 3, 0]
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
    for device in (0, 1, 2, 3, 4):
        word('PADIDX', 0)
        uc.mem_write(sym('DEVICES'), struct.pack('<II', device, 1))
        uc.reg_write(regs.UC_X86_REG_EAX, 1)
        uc.reg_write(regs.UC_X86_REG_EDX, sym('STATE'))
        run(('PADX', 'padpoll'))
        uses_pad = device in (1, 2) or (device == 4 and len(order) == 5)
        assert bytes(uc.mem_read(sym('PADIDX'), 2)) == (b'\x01\x02' if uses_pad else b'\x05\x01')

    if len(order) != 5:
        return
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
