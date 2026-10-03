#!/usr/bin/env python3
"""Assemble the Windows release.

    python tools/bundle.py OUT

Run with the Python the release should carry, on Windows. OUT gets
_internal/: that Python's own files, unpacked and as it ships them -
python.exe, pythonw.exe, the DLLs, Tcl/Tk - with the standard library
compiled into one zip, certifi, the script, net/dpctrl.dll and input/vontanita.dll. The
launcher (launcher/) goes beside _internal/ as v-on-patcher.exe and starts
_internal\\pythonw.exe _internal\\v-on-patcher.py.

python3XY._pth makes that Python use only what is listed in it: no
PYTHONPATH, no user site-packages, nothing from another Python installed
on the machine.
"""
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Standard library packages the patcher never reaches: the test suites,
# IDLE and the demos, and what only installs packages.
SKIP = {'test', 'tests', 'idle_test', 'idlelib', 'turtledemo', 'ensurepip',
        'venv', 'lib2to3', 'site-packages', '__pycache__'}


def keep(path):
    return not (set(os.path.normpath(path).split(os.sep)) & SKIP)


def main(argv):
    if len(argv) != 2 or sys.platform != 'win32':
        raise SystemExit(__doc__)
    home = sys.base_prefix
    tag = 'python%d%d' % sys.version_info[:2]
    internal = os.path.join(argv[1], '_internal')
    if os.path.exists(internal):
        shutil.rmtree(internal)
    os.makedirs(internal)

    # The interpreter, its DLL and the C runtime beside it.
    for name in os.listdir(home):
        if name.lower() in ('python.exe', 'pythonw.exe', 'license.txt') \
                or name.lower().endswith('.dll'):
            shutil.copy2(os.path.join(home, name), internal)

    # Extension modules, OpenSSL, Tcl/Tk; not the test modules.
    os.makedirs(os.path.join(internal, 'DLLs'))
    for name in os.listdir(os.path.join(home, 'DLLs')):
        if name.lower().endswith(('.pyd', '.dll')) and not name.startswith('_test'):
            shutil.copy2(os.path.join(home, 'DLLs', name), os.path.join(internal, 'DLLs'))

    # Tcl/Tk's script library, which tkinter finds at sys.prefix\tcl.
    shutil.copytree(os.path.join(home, 'tcl'), os.path.join(internal, 'tcl'),
                    ignore=shutil.ignore_patterns('demos'))

    # The standard library, compiled into one zip that zipimport reads.
    lib = os.path.join(home, 'Lib')
    with zipfile.PyZipFile(os.path.join(internal, tag + '.zip'), 'w',
                           zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(lib)):
            path = os.path.join(lib, name)
            if not keep(path):
                continue
            if os.path.isdir(path) and os.path.exists(os.path.join(path, '__init__.py')):
                z.writepy(path, filterfunc=keep)
            elif name.endswith('.py'):
                z.writepy(path)

    # certifi, the CA list the cnc-ddraw download falls back on.
    import certifi
    shutil.copytree(os.path.dirname(certifi.__file__),
                    os.path.join(internal, 'Lib', 'site-packages', 'certifi'),
                    ignore=shutil.ignore_patterns('__pycache__'))

    with open(os.path.join(internal, tag + '._pth'), 'w', newline='\r\n') as fh:
        fh.write('%s.zip\n.\nDLLs\nLib\\site-packages\n' % tag)

    # The patcher: the stamped script, and the netplay DLL where the script
    # looks for it, in net\ beside itself.
    shutil.copy2(os.path.join(ROOT, 'v-on-patcher.py'), internal)
    os.makedirs(os.path.join(internal, 'net'))
    shutil.copy2(os.path.join(ROOT, 'net', 'dpctrl.dll'), os.path.join(internal, 'net'))

    os.makedirs(os.path.join(internal, 'input'))
    shutil.copy2(os.path.join(ROOT, 'input', 'vontanita.dll'), os.path.join(internal, 'input'))

    files = sum(len(f) for _r, _d, f in os.walk(internal))
    size = sum(os.path.getsize(os.path.join(r, n)) for r, _d, f in os.walk(internal) for n in f)
    print('%s: %d files, %.1f MB, from %s' % (internal, files, size / 1e6, home))


if __name__ == '__main__':
    main(sys.argv)
