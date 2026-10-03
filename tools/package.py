#!/usr/bin/env python3
"""Zip a finished build into the two release zips.

    python3 tools/package.py DIST NAME

DIST holds what the windows job leaves: v-on-patcher/ (the launcher,
v-on-patcher.exe, and _internal/), v-on-patcher-<version>.py and
dpctrl.dll and vontanita.dll. Writes DIST/NAME-win.zip, with the exe and _internal/ at its
top, and DIST/NAME-python.zip, with the script, net/dpctrl.dll and input/vontanita.dll. The
windows job runs it for an unsigned build, the sign job after signing,
so both zips have one layout.
"""
import os
import sys
import zipfile


def main(argv):
    if len(argv) != 3:
        raise SystemExit(__doc__)
    dist, name = argv[1], argv[2]
    app = os.path.join(dist, 'v-on-patcher')
    win = os.path.join(dist, name + '-win.zip')
    with zipfile.ZipFile(win, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(app):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, app))
    py = os.path.join(dist, name + '-python.zip')
    with zipfile.ZipFile(py, 'w', zipfile.ZIP_DEFLATED) as z:
        scripts = [f for f in sorted(os.listdir(dist)) if f.endswith('.py')]
        if len(scripts) != 1:
            raise SystemExit('expected one script in %s, found %s' % (dist, scripts or 'none'))
        z.write(os.path.join(dist, scripts[0]), scripts[0])
        z.write(os.path.join(dist, 'dpctrl.dll'), 'net/dpctrl.dll')
        z.write(os.path.join(dist, 'vontanita.dll'), 'input/vontanita.dll')
    for path in (win, py):
        with zipfile.ZipFile(path) as z:
            print('%s: %d files, %d bytes' % (path, len(z.namelist()), os.path.getsize(path)))


if __name__ == '__main__':
    main(sys.argv)
