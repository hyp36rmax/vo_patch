#!/usr/bin/env python3
"""Check CE helper delivery in generated ZIPs, or exercise the packager in isolation.

    python3 tools/packagetest.py                 # temporary staging fixture
    python3 tools/packagetest.py WIN.zip PY.zip  # actual distribution archives

The fixture tests archive generation and helper discovery, not Windows execution.
"""
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify(path):
    windows = str(path).endswith('-win.zip')
    prefix = '_internal/' if windows else ''
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'duplicate archive entries'
        scripts = [n for n in names if n.endswith('.py') and
                   n.startswith(prefix + 'v-on-patcher') and
                   '/' not in n[len(prefix):]]
        assert len(scripts) == 1, 'expected one patcher script'
        script = scripts[0]
        for name in ('input/vontanita.dll', 'net/dpctrl.dll'):
            assert archive.read(prefix + name) == (ROOT / name).read_bytes(), name
        if windows:
            assert archive.read('v-on-patcher.exe') == (ROOT / 'launcher/v-on-patcher.exe').read_bytes()
            for name in ('python.exe', 'pythonw.exe', 'python312.dll',
                         'python312.zip', 'python312._pth', 'DLLs/_tkinter.pyd',
                         'Lib/site-packages/certifi/cacert.pem'):
                assert prefix + name in names, 'missing ' + name
        # Exercise the distributed script's real file lookup and SHA checks.
        # Extract only known paths, never arbitrary members of an input ZIP.
        with tempfile.TemporaryDirectory() as tmp:
            for name in (script, prefix + 'input/vontanita.dll', prefix + 'net/dpctrl.dll'):
                dest = Path(tmp) / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.read(name))
            patcher = runpy.run_path(str(Path(tmp) / script))
            assert patcher['tanita_dll']() == (ROOT / 'input/vontanita.dll').read_bytes()
            assert patcher['netplay_dll']() == (ROOT / 'net/dpctrl.dll').read_bytes()
    print('%s: archive paths, helper bytes and packaged loader PASS' % path)


def fixture():
    with tempfile.TemporaryDirectory() as tmp:
        dist = Path(tmp)
        app = dist / 'v-on-patcher'
        internal = app / '_internal'
        internal.mkdir(parents=True)
        # Runtime placeholders deliberately cannot launch: this is a ZIP test.
        for name in ('python.exe', 'pythonw.exe', 'python312.dll', 'python312.zip',
                     'python312._pth', 'DLLs/_tkinter.pyd',
                     'Lib/site-packages/certifi/cacert.pem'):
            path = internal / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'archive fixture, not a runtime')
        shutil.copy2(ROOT / 'launcher/v-on-patcher.exe', app)
        shutil.copy2(ROOT / 'v-on-patcher.py', internal)
        shutil.copy2(ROOT / 'v-on-patcher.py', dist / 'v-on-patcher-test.py')
        for name in ('input/vontanita.dll', 'net/dpctrl.dll'):
            (internal / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, internal / name)
            shutil.copy2(ROOT / name, dist / Path(name).name)
        subprocess.run([sys.executable, str(ROOT / 'tools/package.py'), tmp, 'test'], check=True)
        for kind in ('win', 'python'):
            path = dist / ('test-%s.zip' % kind)
            verify(path)
            # Missing, misplaced and stale helpers must all be rejected.
            helper = ('_internal/' if kind == 'win' else '') + 'input/vontanita.dll'
            for defect in ('missing', 'misplaced', 'stale'):
                bad = dist / ('bad-%s.zip' % kind)
                with zipfile.ZipFile(path) as src, zipfile.ZipFile(bad, 'w') as dst:
                    for item in src.infolist():
                        data = src.read(item.filename)
                        if item.filename == helper:
                            if defect == 'missing':
                                continue
                            if defect == 'misplaced':
                                dst.writestr('wrong/vontanita.dll', data)
                                continue
                            data = b'stale DLL'
                        dst.writestr(item, data)
                try:
                    verify(bad)
                except (AssertionError, KeyError):
                    pass
                else:
                    raise AssertionError('accepted %s helper in %s' % (defect, kind))
        print('six missing/misplaced/stale helper rejection cases PASS')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        fixture()
    else:
        for arg in sys.argv[1:]:
            verify(Path(arg).resolve())
