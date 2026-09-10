#!/usr/bin/env python3
"""Execute the Custom editor and persistence code with a mocked Win32 UI.

The real Windows dialog still needs visual/input acceptance testing.
"""
import struct
import os
from controllertest import load


def check(vp, build, unicorn, r):
    u = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_32)
    u.mem_map(0x400000, 0x4000000)
    stack, stop, mocks, heap = 0x10000000, 0x10002000, 0x10003000, 0x10010000
    u.mem_map(stack, 0x30000)
    sym = lambda n: vp.symbol_va(n, build)
    for name in ('CUSTOM', 'TWIN', 'PAD_BINDS', 'PAD_NAMES', 'BINDBLOCK', 'INIPARSE'):
        u.mem_write(vp.cave_va(name, build), vp.link(name, build))
    lines, titles, controls, ended = {}, {}, {}, []
    functions = {}
    cursor = heap

    def readstr(p):
        data = bytearray()
        for i in range(2048):
            b = u.mem_read(p + i, 1)[0]
            if not b:
                return data.decode()
            data.append(b)
        raise AssertionError('unterminated string')

    def allocate(text):
        nonlocal cursor
        p = cursor
        raw = text.encode() + b'\0'
        u.mem_write(p, raw)
        cursor += len(raw) + 8
        return p

    def callback(_u, address, _size, _data):
        if address not in functions:
            return
        func, argc = functions[address]
        sp = _u.reg_read(r.UC_X86_REG_ESP)
        args = struct.unpack('<%dI' % argc, _u.mem_read(sp + 4, argc * 4))
        result = func(*args)
        _u.reg_write(r.UC_X86_REG_EAX, (result or 0) & 0xffffffff)

    def mock(func, argc, stdcall=True):
        address = mocks + len(functions) * 16
        functions[address] = func, argc
        u.mem_write(address, b'\xc2' + struct.pack('<H', argc * 4) if stdcall else b'\xc3')
        return address

    def word(name, value):
        u.mem_write(sym(name), struct.pack('<I', value))

    def findline(key):
        value = lines.get(readstr(key))
        return allocate(value) if value is not None else 0

    def writeline(key, value):
        lines[readstr(key)] = readstr(value)

    def send(hwnd, iid, message, wp, lp):
        c = controls.setdefault((hwnd, iid), {'items': [], 'selection': -1})
        if message == 0x143:
            c['items'].append(readstr(lp))
            return len(c['items']) - 1
        if message == 0x14e:
            c['selection'] = wp
            return wp
        assert message == 0x147
        return c['selection']

    # FINDLINE/WRITELINE are direct cdecl code addresses, not IAT pointers.
    for name, func, argc in (('FINDLINE', findline, 1), ('WRITELINE', writeline, 2)):
        address = sym(name)
        functions[address] = func, argc
        u.mem_write(address, b'\xc3')
    word(('CUSTOM', 'sendfn'), mock(send, 5))
    word(('CUSTOM', 'titlefn'), mock(lambda hwnd, text: titles.update({hwnd: readstr(text)}), 2))
    word(('CUSTOM', 'activefn'), mock(lambda: 0x701, 0))
    word('ENDDIALOG', mock(lambda hwnd, result: ended.append((hwnd, result)), 2))
    u.hook_add(unicorn.UC_HOOK_CODE, callback)

    def run(entry, args=(), eax=0, end=stop):
        u.reg_write(r.UC_X86_REG_ESP, stack + 0x1000)
        u.mem_write(stack + 0x1000, struct.pack('<%dI' % (len(args) + 1), stop, *args))
        u.reg_write(r.UC_X86_REG_EAX, eax)
        u.emu_start(sym(entry), end, count=100000)
        assert u.reg_read(r.UC_X86_REG_EIP) == end, entry

    def binds(player):
        return bytes(u.mem_read(sym(('CUSTOM', 'binds1')) + player * 24, 24))

    defaults = bytes(u.mem_read(sym(('TWIN', 'custombinds')), 24))
    def open_editor(player):
        hwnd = 0x700 + player
        for key in list(controls):
            if key[0] == hwnd:
                del controls[key]
        run(('CUSTOM', 'procedure'), (hwnd, 0x110, 0, player))
        assert titles[hwnd].endswith('Player %d' % (player + 1))
        for slot in range(12):
            c = controls[hwnd, 100 + slot]
            assert c['items'][0] == 'None' and len(c['items']) == 21
            assert c['selection'] == (binds(player)[slot * 2] - 0xe0 + 1 if binds(player)[slot * 2] else 0)
        return hwnd

    # Missing lines and malformed lines cannot erase either shipped default.
    run(('CUSTOM', 'load'))
    assert binds(0) == binds(1) == defaults
    for bad in ('', 'e0', 'g'*48, 'e001'*12, 'ff00'*12, 'e000'*11):
        lines['1P Custom Assign'] = bad
        run(('CUSTOM', 'load'))
        assert binds(0) == defaults and binds(1) == defaults
    lines.clear()

    for player in (0, 1):
        hwnd = open_editor(player)
        # Individually choose a different input for every slot, and unbind one.
        selected = [0] + list(range(1, 12))
        expected = b''.join(struct.pack('<H', 0 if pos == 0 else 0xdf + pos) for pos in selected)
        other = binds(1 - player)
        for slot, pos in enumerate(selected):
            controls[hwnd, 100 + slot]['selection'] = pos
        run(('CUSTOM', 'procedure'), (hwnd, 0x111, 1, 0))
        assert ended[-1] == (hwnd, 1)
        assert binds(player) == expected and binds(1 - player) == other
        assert lines['%dP Custom Assign' % (player + 1)] == expected.hex()
        # Cancel after Default must not commit or save the reset.
        hwnd = open_editor(player)
        saved = dict(lines)
        run(('CUSTOM', 'procedure'), (hwnd, 0x111, 3, 0))
        run(('CUSTOM', 'procedure'), (hwnd, 0x111, 2, 0))
        assert binds(player) == expected and lines == saved
        # A fresh load restores the saved remap, including None.
        run(('CUSTOM', 'load'))
        assert binds(player) == expected and binds(1 - player) == other
        # Default + OK restores Xbox/Brook for only this player.
        hwnd = open_editor(player)
        run(('CUSTOM', 'procedure'), (hwnd, 0x111, 3, 0))
        run(('CUSTOM', 'procedure'), (hwnd, 0x111, 1, 0))
        assert binds(player) == defaults and binds(1 - player) == other
        assert lines['%dP Custom Assign' % (player + 1)] == defaults.hex()
    assert set(lines) == {'1P Custom Assign', '2P Custom Assign'}

    # Two distinct saved layouts must coexist across a fresh startup load.
    first = bytes.fromhex('e100')*12
    second = bytes.fromhex('f300')*12
    lines.update({'1P Custom Assign':first.hex(), '2P Custom Assign':second.hex()})
    run(('CUSTOM','load'))
    assert binds(0) == first and binds(1) == second
    hwnd = open_editor(0)
    run(('CUSTOM','procedure'), (hwnd,0x111,3,0))
    run(('CUSTOM','procedure'), (hwnd,0x111,1,0))
    assert binds(0) == defaults and binds(1) == second
    assert lines['2P Custom Assign'] == second.hex()

    # The F7 branch preserves its frame and returns the modal result, including
    # failure/cancel, instead of reporting success unconditionally.
    frame = stack + 0x1800
    for result in (0, 1, -1):
        word(('CUSTOM', 'dialogfn'), mock(lambda *args: result, 5))
        word('CURPLAYER', 1)
        u.reg_write(r.UC_X86_REG_EBP, frame)
        run(('CUSTOM', 'page'), end=sym('CUSTOM_PAGE_END'))
        actual = struct.unpack('<I', u.mem_read(frame - 0x14, 4))[0]
        assert actual == int(result == 1)
    print('%s: Custom editing, Cancel, Default, save/reload and player isolation passed' % build.name)


def main():
    try:
        import unicorn
        from unicorn import x86_const
    except ImportError:
        if os.environ.get('CI') == 'true':
            raise
        raise SystemExit('Unicorn is required for Custom editor tests')
    vp = load()
    for build in (vp.RETAIL, vp.JPRE):
        check(vp, build, unicorn, x86_const)


if __name__ == '__main__':
    main()
