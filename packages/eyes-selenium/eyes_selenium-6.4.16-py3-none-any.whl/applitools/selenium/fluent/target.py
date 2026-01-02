from __future__ import absolute_import, division, print_function

from typing import TYPE_CHECKING, TypeVar, overload

from applitools.common.fluent.web_target import WebTarget

from .selenium_check_settings import SeleniumCheckSettings

if TYPE_CHECKING:
    from typing import Optional, Text

__all__ = ("Target",)

Self = TypeVar("Self", bound="Target")


class Target(WebTarget):
    CheckSettings = SeleniumCheckSettings

    @classmethod
    @overload
    def webview(cls, use_default=True):
        # type: (Optional[bool]) -> Self.CheckSettings
        pass

    @classmethod
    @overload
    def webview(cls, webview_id):
        # type: (Text) -> Self.CheckSettings
        pass

    @classmethod
    def webview(cls, webview=True):
        return cls.CheckSettings().webview(webview)
