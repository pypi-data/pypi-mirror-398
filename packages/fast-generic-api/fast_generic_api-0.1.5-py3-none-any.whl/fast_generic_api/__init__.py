# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:31
# @Author  : fzf
# @FileName: __init__.py
# @Software: PyCharm
r"""
 _____         _     ____  _____ ____ _____    __                                             _
|  ___|_ _ ___| |_  |  _ \| ____/ ___|_   _|  / _|_ __ __ _ _ __ ___   _____      _____  _ __| | __
| |_ / _` / __| __| | |_) |  _| \___ \ | |   | |_| '__/ _` | '_ ` _ \ / _ \ \ /\ / / _ \| '__| |/ /
|  _| (_| \__ \ |_  |  _ <| |___ ___) || |   |  _| | | (_| | | | | | |  __/\ V  V / (_) | |  |   <
|_|  \__,_|___/\__| |_| \_\_____|____/ |_|   |_| |_|  \__,_|_| |_| |_|\___| \_/\_/ \___/|_|  |_|\_\
"""

__title__ = 'Fast REST framework'
__version__ = '0.1.0'
__author__ = 'Tom Christie'
__license__ = 'BSD 3-Clause'
__copyright__ = 'Copyright 2011-2023 Encode OSS Ltd'

# Version synonym
VERSION = __version__

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = 'iso-8859-1'

# Default datetime input and output formats
ISO_8601 = 'iso-8601'

class RemovedInDRF315Warning(DeprecationWarning):
    pass


class RemovedInDRF317Warning(PendingDeprecationWarning):
    pass
