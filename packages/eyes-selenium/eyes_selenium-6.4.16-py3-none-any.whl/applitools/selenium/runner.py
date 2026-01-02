from __future__ import absolute_import, division, print_function

from applitools.common.runner import (
    ClassicEyesRunner,
    EyesRunner,
    RunnerOptions,
    VisualGridEyesRunner,
    log_session_results_and_raise_exception,
)

from .protocol import SeleniumWebDriver

__all__ = (
    "ClassicRunner",
    "EyesRunner",
    "RunnerOptions",
    "VisualGridRunner",
    "log_session_results_and_raise_exception",
)


class ClassicRunner(ClassicEyesRunner):
    BASE_AGENT_ID = "eyes.sdk.python"
    Protocol = SeleniumWebDriver


class VisualGridRunner(VisualGridEyesRunner):
    BASE_AGENT_ID = "eyes.selenium.visualgrid.python"
    Protocol = SeleniumWebDriver
