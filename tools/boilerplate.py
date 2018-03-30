"""
Script to autogenerate pyplot wrappers.

When this script is run, the current contents of pyplot are
split into generatable and non-generatable content (via the magic header
:attr:`PYPLOT_MAGIC_HEADER`) and the generatable content is overwritten.
Hence, the non-generatable content should be edited in the pyplot.py file
itself, whereas the generatable content must be edited via templates in
this file.
"""
# We did try to do the wrapping the smart way,
# with callable functions and new.function, but could never get the
# docstrings right for python2.2.  See
# http://groups.google.com/group/comp.lang.python/browse_frm/thread/dcd63ec13096a0f6/1b14640f3a4ad3dc?#1b14640f3a4ad3dc
# For some later history, see
# http://thread.gmane.org/gmane.comp.python.matplotlib.devel/7068

import inspect
from inspect import Signature, Parameter
import os
import random
import textwrap

# this line imports the installed copy of matplotlib, and not the local copy
import numpy as np
from matplotlib import mlab
from matplotlib.axes import Axes


# this is the magic line that must exist in pyplot, after which the boilerplate content will be
# appended
PYPLOT_MAGIC_HEADER = '################# REMAINING CONTENT GENERATED BY boilerplate.py ##############\n'

PYPLOT_PATH = os.path.join(os.path.dirname(__file__), 'lib', 'matplotlib',
                           'pyplot.py')


AUTOGEN_MSG = """
# Autogenerated by boilerplate.py.  Do not edit as changes will be lost."""


CMAPPABLE_TEMPLATE = AUTOGEN_MSG + """
@_autogen_docstring(Axes.%(func)s)
def %(func)s%(sig)s:
    __ret = gca().%(func)s%(call)s
%(mappable)s
    return __ret
"""


NON_CMAPPABLE_TEMPLATE = AUTOGEN_MSG + """
@docstring.copy_dedent(Axes.%(func)s)
def %(func)s%(sig)s:
    return gca().%(func)s%(call)s
"""

# Used for colormap functions
CMAP_TEMPLATE = AUTOGEN_MSG + '''
def {name}():
    """
    Set the colormap to "{name}".

    This changes the default colormap as well as the colormap of the current
    image if there is one. See ``help(colormaps)`` for more information.
    """
    set_cmap("{name}")

'''

CMAP_TEMPLATE_DEPRECATED = AUTOGEN_MSG + '''
def {name}():
    """
    Set the colormap to "{name}".

    This changes the default colormap as well as the colormap of the current
    image if there is one. See ``help(colormaps)`` for more information.
    """
    from matplotlib.cbook import warn_deprecated
    warn_deprecated(
                    "2.0",
                    name="{name}",
                    obj_type="colormap"
                    )
    set_cmap("{name}")

'''


def boilerplate_gen():
    """Generator of lines for the automated part of pyplot."""

    # These methods are all simple wrappers of Axes methods by the same name.
    _commands = (
        'acorr',
        'angle_spectrum',
        'annotate',
        'arrow',
        'autoscale',
        'axhline',
        'axhspan',
        'axvline',
        'axvspan',
        'bar',
        'barbs',
        'barh',
        'boxplot',
        'broken_barh',
        'cla',
        'clabel',
        'cohere',
        'contour',
        'contourf',
        'csd',
        'errorbar',
        'eventplot',
        'fill',
        'fill_between',
        'fill_betweenx',
        'grid',
        'hexbin',
        'hist',
        'hist2d',
        'hlines',
        'imshow',
        'legend',
        'locator_params',
        'loglog',
        'magnitude_spectrum',
        'margins',
        'pcolor',
        'pcolormesh',
        'phase_spectrum',
        'pie',
        'plot',
        'plot_date',
        'psd',
        'quiver',
        'quiverkey',
        'scatter',
        'semilogx',
        'semilogy',
        'specgram',
        'spy',
        'stackplot',
        'stem',
        'step',
        'streamplot',
        'table',
        'text',
        'tick_params',
        'ticklabel_format',
        'tricontour',
        'tricontourf',
        'tripcolor',
        'triplot',
        'violinplot',
        'vlines',
        'xcorr',
    )

    cmappable = {
        'contour': 'if __ret._A is not None: sci(__ret)',
        'contourf': 'if __ret._A is not None: sci(__ret)',
        'hexbin': 'sci(__ret)',
        'scatter': 'sci(__ret)',
        'pcolor': 'sci(__ret)',
        'pcolormesh': 'sci(__ret)',
        'hist2d': 'sci(__ret[-1])',
        'imshow': 'sci(__ret)',
        'spy': 'if isinstance(ret, cm.ScalarMappable): sci(__ret)',
        'quiver': 'sci(__ret)',
        'specgram': 'sci(__ret[-1])',
        'streamplot': 'sci(__ret.lines)',
        'tricontour': 'if __ret._A is not None: sci(__ret)',
        'tricontourf': 'if __ret._A is not None: sci(__ret)',
        'tripcolor': 'sci(__ret)',
    }

    class value_formatter:
        """
        Format function default values as needed for inspect.formatargspec.
        The interesting part is a hard-coded list of functions used
        as defaults in pyplot methods.
        """

        def __init__(self, value):
            if value is mlab.detrend_none:
                self._repr = "mlab.detrend_none"
            elif value is mlab.window_hanning:
                self._repr = "mlab.window_hanning"
            elif value is np.mean:
                self._repr = "np.mean"
            else:
                self._repr = repr(value)

        def __repr__(self):
            return self._repr

    text_wrapper = textwrap.TextWrapper(
        break_long_words=False, width=70,
        initial_indent=' ' * 8, subsequent_indent=' ' * 8)

    for func in _commands:
        # For some commands, an additional line is needed to set the color map.
        if func in cmappable:
            fmt = CMAPPABLE_TEMPLATE
            mappable = '    ' + cmappable[func]
        else:
            fmt = NON_CMAPPABLE_TEMPLATE

        # Get signature of wrapped function.
        sig = inspect.signature(getattr(Axes, func))

        # Replace self argument.
        params = list(sig.parameters.values())[1:]

        sig = str(sig.replace(parameters=[
            param.replace(default=value_formatter(param.default))
            if param.default is not param.empty else param
            for param in params]))
        # Move opening parenthesis before newline.
        sig = '(\n' + text_wrapper.fill(sig).replace('(', '', 1)

        # How to call the wrapped function.
        call = '(\n' + text_wrapper.fill(', '.join(
            ('{0}={0}' if param.kind in [Parameter.POSITIONAL_OR_KEYWORD,
                                         Parameter.KEYWORD_ONLY] else
             '*{0}' if param.kind is Parameter.VAR_POSITIONAL else
             '**{0}' if param.kind is Parameter.VAR_KEYWORD else
             # Intentionally crash for Parameter.POSITIONAL_ONLY.
             None).format(param.name)
            for param in params) + ')')

        # Bail out in case of name collision.
        for reserved in ('gca', 'gci', '__ret'):
            if reserved in params:
                raise ValueError(
                    'Axes method {} has kwarg named {}'.format(func, reserved))

        yield fmt % locals()

    cmaps = (
        'autumn',
        'bone',
        'cool',
        'copper',
        'flag',
        'gray',
        'hot',
        'hsv',
        'jet',
        'pink',
        'prism',
        'spring',
        'summer',
        'winter',
        'magma',
        'inferno',
        'plasma',
        'viridis',
        "nipy_spectral"
    )
    deprecated_cmaps = ("spectral", )
    # add all the colormaps (autumn, hsv, ....)
    for name in cmaps:
        yield CMAP_TEMPLATE.format(name=name)
    for name in deprecated_cmaps:
        yield CMAP_TEMPLATE_DEPRECATED.format(name=name)

    yield ''
    yield '_setup_pyplot_info_docstrings()'


def build_pyplot():
    pyplot_path = os.path.join(os.path.dirname(__file__), "..", 'lib',
                               'matplotlib', 'pyplot.py')

    pyplot_orig = open(pyplot_path, 'r').readlines()

    try:
        pyplot_orig = pyplot_orig[:pyplot_orig.index(PYPLOT_MAGIC_HEADER) + 1]
    except IndexError:
        raise ValueError('The pyplot.py file *must* have the exact line: %s'
                         % PYPLOT_MAGIC_HEADER)

    pyplot = open(pyplot_path, 'w')
    pyplot.writelines(pyplot_orig)
    pyplot.write('\n')

    pyplot.writelines(boilerplate_gen())
    pyplot.write('\n')


if __name__ == '__main__':
    # Write the matplotlib.pyplot file
    build_pyplot()
