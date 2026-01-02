from __future__ import absolute_import, division, print_function

from applitools.common.runner import (
    ClassicEyesRunner,
    RunnerOptions,
    VisualGridEyesRunner,
)

from .protocol import PlaywrightSpecDriver

__all__ = "ClassicRunner", "VisualGridRunner", "RunnerOptions"


class ClassicRunner(ClassicEyesRunner):
    BASE_AGENT_ID = "eyes.playwright.python"
    Protocol = PlaywrightSpecDriver


class VisualGridRunner(VisualGridEyesRunner):
    BASE_AGENT_ID = "eyes.playwright.visualgrid.python"
    Protocol = PlaywrightSpecDriver
