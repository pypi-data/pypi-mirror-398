from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from functools import wraps

from Orange.widgets.utils.messages import UnboundMsg

multiple_targets_msg = _tr.m[3252, "Multiple targets are not supported."]
_multiple_targets_data = UnboundMsg(multiple_targets_msg)


def check_multiple_targets_input(f):
    """
    Wrapper for widget's set_data method that checks if the input
    has multiple targets and shows an error if it does.

    :param f: widget's `set_data` method to wrap
    :return: wrapped method that handles multiple targets data inputs
    """

    @wraps(f)
    def new_f(widget, data, *args, **kwargs):
        widget.Error.add_message("multiple_targets_data",
                                 _multiple_targets_data)
        widget.Error.multiple_targets_data.clear()
        if data is not None and len(data.domain.class_vars) > 1:
            widget.Error.multiple_targets_data()
            data = None
        return f(widget, data, *args, **kwargs)

    return new_f
