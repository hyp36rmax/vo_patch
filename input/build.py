#!/usr/bin/env python3
"""Compile input/tanita.c to input/vontanita.dll and record its hashes in
v-on-patcher.py.

The DLL is a file in the repository: the release build ships it beside the
exe (PyInstaller's _internal/), a source checkout reads it from input/. The
patcher checks the file against TANITA_DLL_SHA before installing it.

    python3 input/build.py            compile, write the DLL and the hashes
    python3 input/build.py --check    is the DLL current? writes nothing

--check compares the native reader, controller UI, mapping headers and exports
against the source hash recorded in v-on-patcher.py
and the DLL file against its recorded hash, rather than recompiling: two
mingw versions do not produce identical output from identical source, so a
byte comparison would fail on any machine but the one that last ran this.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, 'tanita.c')
DEF = os.path.join(HERE, 'tanita.def')
TARGET = os.path.join(ROOT, 'v-on-patcher.py')
DLL = os.path.join(HERE, 'vontanita.dll')

CC = os.environ.get('VON_INPUT_CC', 'i686-w64-mingw32-gcc')

# Left to itself the linker stamps a build time and picks an image base, so
# two runs over unchanged source give different bytes and a 40 KB blob turns
# up in the diff for nothing. Pinned, the same mingw produces the same file.
# Stripping is done by the linker: a separate strip pass re-stamps the time.
IMAGE_BASE = 0x6c640000

BEGIN = '# --- Tanita hashes: written by input/build.py, do not edit ---'
END = '# --- end Tanita hashes ---'

EXPORTS = ('TanitaGetState', 'VonGetState', 'VonSelectController', 'VonCaptureInput')


def source_hash():
    digest = hashlib.sha256()
    for path in (SRC, DEF, *(os.path.join(HERE, name) for name in
                            ('tanita_map.h', 'controller.c', 'controller_logic.h'))):
        with open(path, 'rb') as f:
            digest.update(f.read())
    return digest.hexdigest()


def compile_dll(workdir):
    """Build a stripped 32-bit DLL and return its bytes."""
    if not shutil.which(CC):
        sys.exit('%s not found. Install gcc-mingw-w64-i686.' % CC)

    out = os.path.join(workdir, 'vontanita.dll')
    cmd = [CC, '-O2', '-shared', '-s', '-o', out, SRC, os.path.join(HERE, 'controller.c'), DEF,
           '-lhid', '-lsetupapi', '-Wall', '-Wextra', '-Werror', '-Wl,--enable-stdcall-fixup',
           '-Wl,--no-insert-timestamp', '-Wl,--image-base=%#x' % IMAGE_BASE]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        sys.stderr.write(proc.stderr)
        sys.exit('compile failed')

    with open(out, 'rb') as f:
        blob = f.read()

    if blob[:2] != b'MZ':
        sys.exit('output is not a PE file')
    for name in EXPORTS:
        if name.encode() not in blob:
            sys.exit('export missing from the build: %s' % name)
    return blob


def render(blob, sha):
    """The hash block as it appears in v-on-patcher.py."""
    dll_sha = hashlib.sha256(blob).hexdigest()
    return (
        "%s\n"
        "# Source: input/tanita.c, compiled by input/build.py.\n"
        "TANITA_SRC_SHA = '%s'\n"
        "# sha256 of input/vontanita.dll, so the patcher can tell its own build\n"
        "# from an older one already installed.\n"
        "TANITA_DLL_SHA = '%s'\n"
        "%s" % (BEGIN, sha, dll_sha, END))


def splice(text, block):
    start = text.index(BEGIN)
    stop = text.index(END) + len(END)
    return text[:start] + block + text[stop:]


def recorded(text, name):
    for line in text.splitlines():
        if line.startswith(name):
            return line.split("'")[1]
    return None


def file_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def main(argv):
    check = '--check' in argv

    with open(TARGET, encoding='utf-8') as f:
        text = f.read()
    if BEGIN not in text or END not in text:
        sys.exit('markers not found in v-on-patcher.py')

    sha = source_hash()

    if check:
        have = recorded(text, 'TANITA_SRC_SHA')
        if have != sha:
            print('input/tanita.c and input/vontanita.dll disagree.')
            print('  source: %s' % sha)
            print('  built:  %s' % (have or 'none'))
            print('Run: python3 input/build.py')
            return 1
        want = recorded(text, 'TANITA_DLL_SHA')
        got = file_hash(DLL)
        if got != want:
            print('input/vontanita.dll is not the file v-on-patcher.py expects.')
            print('  recorded: %s' % want)
            print('  file:     %s' % (got or 'missing'))
            print('Run: python3 input/build.py')
            return 1
        print('input/vontanita.dll matches input/tanita.c (%s)' % sha[:12])
        return 0

    with tempfile.TemporaryDirectory() as workdir:
        blob = compile_dll(workdir)

    with open(DLL, 'wb') as f:
        f.write(blob)
    with open(TARGET, 'w', encoding='utf-8') as f:
        f.write(splice(text, render(blob, sha)))

    print('wrote input/vontanita.dll, %d bytes (%s)' % (len(blob), sha[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
