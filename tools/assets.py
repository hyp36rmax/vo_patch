#!/usr/bin/env python3
"""Bake the artwork in assets/ into the patcher.

    python3 tools/assets.py

Writes the logo and the window icon as base64 PNG between the ASSETS BLOB
markers in v-on-patcher.py, and assets/icon.ico for the exe. Both are
reduced to a 256-colour palette, which the artwork fits and which is a
fifth of the size. Needs Pillow.
"""

import base64
import io
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets')
PATCHER = os.path.join(ROOT, 'v-on-patcher.py')

LOGO_SRC = 'VONPatcherLogo1.png'
ICON_SRC = 'VONPatcherIcon.png'

# Twice the height the window shows at 100% (LOGO_HEIGHT in the patcher),
# so it holds up at 200% scaling and is subsampled below that.
LOGO_HEIGHT = 192
ICON_SIZE = 256
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

BEGIN = '# ASSETS BLOB BEGIN - tools/assets.py\n'
END = '# ASSETS BLOB END\n'
WIDTH = 72


def png(image):
    out = io.BytesIO()
    image.quantize(256, method=Image.FASTOCTREE).save(out, 'PNG',
                                                      optimize=True)
    return out.getvalue()


def literal(name, data):
    text = base64.b64encode(data).decode('ascii')
    lines = [text[i:i + WIDTH] for i in range(0, len(text), WIDTH)]
    return '%s = (\n%s\n)\n' % (name, '\n'.join("    '%s'" % l for l in lines))


def main():
    logo = Image.open(os.path.join(ASSETS, LOGO_SRC)).convert('RGBA')
    width = int(round(logo.width * LOGO_HEIGHT / float(logo.height)))
    logo = logo.resize((width, LOGO_HEIGHT), Image.LANCZOS)
    icon = Image.open(os.path.join(ASSETS, ICON_SRC)).convert('RGBA')
    icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)

    logo_png, icon_png = png(logo), png(icon)
    with open(PATCHER, encoding='utf-8') as fh:
        source = fh.read()
    pattern = re.compile(re.escape(BEGIN) + '.*?' + re.escape(END), re.S)
    if not pattern.search(source):
        raise SystemExit('no ASSETS BLOB markers in v-on-patcher.py')
    block = BEGIN + literal('LOGO_PNG', logo_png) \
        + literal('ICON_PNG', icon_png) + END
    source = pattern.sub(lambda _m: block, source, count=1)
    with open(PATCHER, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(source)
    print('logo %dx%d, %d bytes; icon %dx%d, %d bytes -> v-on-patcher.py'
          % (logo.size + (len(logo_png),) + icon.size + (len(icon_png),)))

    icon.save(os.path.join(ASSETS, 'icon.ico'),
              sizes=[(s, s) for s in ICO_SIZES])
    print('icon.ico %s' % ', '.join(str(s) for s in ICO_SIZES))
    return 0


if __name__ == '__main__':
    sys.exit(main())
