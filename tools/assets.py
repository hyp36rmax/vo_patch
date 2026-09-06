#!/usr/bin/env python3
"""Derive the files the patcher ships from the artwork in assets/.

    python3 tools/assets.py

Writes assets/logo.png, assets/icon.png and assets/icon.ico. The originals
are far larger than the window needs and Tk cannot resample well, so they
are scaled here with Pillow and the results committed.
"""

import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets')

LOGO_SRC = 'VONPatcherLogo1.png'
ICON_SRC = 'VONPatcherIcon.png'

# Twice the height the window shows at 100% (LOGO_HEIGHT in v-on-patcher.py),
# so it holds up at 200% scaling and is subsampled below that.
LOGO_HEIGHT = 192
ICON_SIZE = 256
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def main():
    logo = Image.open(os.path.join(ASSETS, LOGO_SRC)).convert('RGBA')
    width = int(round(logo.width * LOGO_HEIGHT / float(logo.height)))
    logo = logo.resize((width, LOGO_HEIGHT), Image.LANCZOS)
    logo.save(os.path.join(ASSETS, 'logo.png'), optimize=True)
    print('logo.png %dx%d' % logo.size)

    icon = Image.open(os.path.join(ASSETS, ICON_SRC)).convert('RGBA')
    icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
    icon.save(os.path.join(ASSETS, 'icon.png'), optimize=True)
    print('icon.png %dx%d' % icon.size)

    icon.save(os.path.join(ASSETS, 'icon.ico'),
              sizes=[(s, s) for s in ICO_SIZES])
    print('icon.ico %s' % ', '.join(str(s) for s in ICO_SIZES))
    return 0


if __name__ == '__main__':
    sys.exit(main())
