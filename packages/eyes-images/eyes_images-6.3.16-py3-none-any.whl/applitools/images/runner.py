from __future__ import absolute_import, division, print_function

from applitools.common.runner import ClassicEyesRunner

from .protocol import Images


class ClassicRunner(ClassicEyesRunner):
    BASE_AGENT_ID = "eyes.images.python"
    Protocol = Images
