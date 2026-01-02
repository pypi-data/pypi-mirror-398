from __future__ import absolute_import, division, print_function

import attr

from applitools.common.fluent.web_check_settings import (
    WebCheckSettings,
    WebCheckSettingsValues,
)


@attr.s
class SeleniumCheckSettingsValues(WebCheckSettingsValues):
    pass


@attr.s
class SeleniumCheckSettings(WebCheckSettings):
    Values = SeleniumCheckSettingsValues
