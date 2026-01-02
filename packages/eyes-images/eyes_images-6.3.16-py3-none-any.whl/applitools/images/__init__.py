from __future__ import absolute_import, division, print_function

from applitools.common import logger
from applitools.common.accessibility import (
    AccessibilityGuidelinesVersion,
    AccessibilityLevel,
    AccessibilityRegionType,
    AccessibilitySettings,
)
from applitools.common.batch_close import BatchClose
from applitools.common.config import BatchInfo, Configuration
from applitools.common.cut import (
    FixedCutProvider,
    NullCutProvider,
    UnscaledFixedCutProvider,
)
from applitools.common.fluent.region import AccessibilityRegionByRectangle
from applitools.common.geometry import AccessibilityRegion, RectangleSize, Region
from applitools.common.locators import VisualLocator
from applitools.common.logger import FileLogger, StdoutLogger
from applitools.common.match import MatchLevel
from applitools.common.test_results import (
    TestResultContainer,
    TestResults,
    TestResultsSummary,
)

from .__version__ import __version__  # noqa
from .extract_text import OCRRegion, TextRegionSettings
from .eyes import Eyes
from .fluent import Target

__all__ = (
    "AccessibilityGuidelinesVersion",
    "AccessibilityLevel",
    "AccessibilityRegion",
    "AccessibilityRegionByRectangle",
    "AccessibilityRegionType",
    "AccessibilitySettings",
    "BatchClose",
    "BatchInfo",
    "Configuration",
    "Eyes",
    "FileLogger",
    "FixedCutProvider",
    "MatchLevel",
    "NullCutProvider",
    "OCRRegion",
    "RectangleSize",
    "Region",
    "StdoutLogger",
    "Target",
    "TestResultContainer",
    "TestResults",
    "TestResultsSummary",
    "TextRegionSettings",
    "UnscaledFixedCutProvider",
    "logger",
    "VisualLocator",
)
