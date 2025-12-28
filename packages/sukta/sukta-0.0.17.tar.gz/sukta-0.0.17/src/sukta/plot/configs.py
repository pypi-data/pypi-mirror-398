import contextlib

import matplotlib as mpl
import matplotlib.pyplot as plt

from sukta.utils.tree import apply_vfunc

from .colors import TurboColormap

overriden_styles = ["default"]


@contextlib.contextmanager
def context(style, after_reset: bool = False):
    with mpl.rc_context():
        if after_reset:
            mpl.rcdefaults()
        use(style)
        yield


def use(style):
    TurboColormap.register_turbocmap()

    def _replace_overriden(style):
        if style in overriden_styles:
            return "sukta.plot.styles." + style
        return style

    plt.style.use(apply_vfunc(_replace_overriden, style))
