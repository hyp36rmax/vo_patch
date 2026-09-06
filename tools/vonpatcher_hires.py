"""The resolution patch's tables and helpers, loaded out of v-on-patcher.py
for the tools. Import as: import vonpatcher_hires as hires."""
import importlib.util
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('VONPATCHER_BOOTSTRAP', '1')
_spec = importlib.util.spec_from_file_location(
    'v-on-patcher', os.path.join(os.path.dirname(_here), 'v-on-patcher.py'))
_vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vp)
sys.modules[__name__].__dict__.update(
    {k: v for k, v in _vp.__dict__.items() if not k.startswith('__')})
