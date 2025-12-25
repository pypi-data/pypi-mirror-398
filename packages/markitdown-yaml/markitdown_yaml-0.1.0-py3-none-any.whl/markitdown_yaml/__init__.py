# SPDX-FileCopyrightText: 2025-present Yasir Alibrahem <alibrahem.yasir@gmail.com>
#
# SPDX-License-Identifier: MIT

from .__about__ import __version__
from ._plugin import YamlConverter, __plugin_interface_version__, register_converters

__all__ = [
    "__version__",
    "__plugin_interface_version__",
    "register_converters",
    "YamlConverter",
]
