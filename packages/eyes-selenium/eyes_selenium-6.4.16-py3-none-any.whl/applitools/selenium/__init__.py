from __future__ import absolute_import, division, print_function

from applitools.common import DynamicTextType, logger
from applitools.common.accessibility import (
    AccessibilityGuidelinesVersion,
    AccessibilityLevel,
    AccessibilityRegionType,
    AccessibilitySettings,
)
from applitools.common.batch_close import BatchClose
from applitools.common.config import BatchInfo
from applitools.common.cut import (
    FixedCutProvider,
    NullCutProvider,
    UnscaledFixedCutProvider,
)
from applitools.common.extract_text import ImageOCRRegion, OCRRegion, TextRegionSettings
from applitools.common.fluent.region import AccessibilityRegionByRectangle
from applitools.common.fluent.target_path import TargetPath
from applitools.common.geometry import AccessibilityRegion, RectangleSize, Region
from applitools.common.locators import VisualLocator
from applitools.common.logger import FileLogger, StdoutLogger
from applitools.common.match import MatchLevel
from applitools.common.selenium.config import Configuration
from applitools.common.selenium.misc import BrowserType, MobileOptions, StitchMode
from applitools.common.server import FailureReports
from applitools.common.test_results import (
    TestResultContainer,
    TestResults,
    TestResultsSummary,
)
from applitools.common.ultrafastgrid import (
    AndroidMultiDeviceTarget,
    ChromeEmulationInfo,
    DesktopBrowserInfo,
    DeviceName,
    IosDeviceInfo,
    IosDeviceName,
    IosMultiDeviceTarget,
    IosVersion,
    ScreenOrientation,
    VisualGridOption,
)

from .__version__ import __version__  # noqa
from .eyes import Eyes
from .fluent.target import Target
from .runner import ClassicRunner, RunnerOptions, VisualGridRunner

__all__ = (
    "AccessibilityGuidelinesVersion",
    "AccessibilityLevel",
    "AccessibilityRegion",
    "AccessibilityRegionByRectangle",
    "AccessibilityRegionType",
    "AccessibilitySettings",
    "BatchClose",
    "BatchInfo",
    "BrowserType",
    "ChromeEmulationInfo",
    "ClassicRunner",
    "Configuration",
    "DesktopBrowserInfo",
    "DeviceName",
    "DynamicTextType",
    "Eyes",
    "FailureReports",
    "FileLogger",
    "FixedCutProvider",
    "ImageOCRRegion",
    "IosDeviceInfo",
    "IosDeviceName",
    "IosVersion",
    "MatchLevel",
    "NullCutProvider",
    "OCRRegion",
    "RectangleSize",
    "Region",
    "RunnerOptions",
    "ScreenOrientation",
    "StdoutLogger",
    "StitchMode",
    "Target",
    "TargetPath",
    "TestResultContainer",
    "TestResults",
    "TestResultsSummary",
    "TextRegionSettings",
    "UnscaledFixedCutProvider",
    "VisualGridRunner",
    "VisualLocator",
    "VisualGridOption",
    "logger",
    "IosMultiDeviceTarget",
    "AndroidMultiDeviceTarget",
    "MobileOptions",
)
