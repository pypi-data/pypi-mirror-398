from __future__ import absolute_import, division, print_function

import attr

from applitools.common.fluent.web_check_settings import (
    WebCheckSettings,
    WebCheckSettingsValues,
)


@attr.s
class PlaywrightCheckSettingsValues(WebCheckSettingsValues):
    pass


@attr.s
class PlaywrightCheckSettings(WebCheckSettings):
    Values = PlaywrightCheckSettingsValues
