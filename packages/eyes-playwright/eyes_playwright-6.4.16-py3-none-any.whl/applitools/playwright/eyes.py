from __future__ import absolute_import, division, print_function, unicode_literals

from applitools.common.eyes import WebEyes
from applitools.common.selenium.config import Configuration

from .fluent.target import Target
from .runner import ClassicRunner


class Eyes(WebEyes):
    _Configuration = Configuration
    _DefaultRunner = ClassicRunner
    Target = Target
