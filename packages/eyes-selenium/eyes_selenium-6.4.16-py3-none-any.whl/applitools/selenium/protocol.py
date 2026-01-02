from __future__ import absolute_import, division, print_function

from applitools.common.protocol import USDKProtocol

from .__version__ import __version__
from .object_registry import SeleniumWebdriverObjectRegistry


class SeleniumWebDriver(USDKProtocol):
    _ObjectRegistry = SeleniumWebdriverObjectRegistry
    SDK_INFO = "eyes-selenium", __version__
