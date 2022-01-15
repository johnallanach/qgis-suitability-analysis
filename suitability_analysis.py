# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SuitabilityAnalysis
 Vector-based site suitability analysis
                              -------------------
        copyright            : (C) 2022 by John Allanach
        email                : j8hnallanach@gmail.com
 ***************************************************************************/
"""


import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .suitability_analysis_provider import SuitabilityAnalysisProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class SuitabilityAnalysisPlugin(object):

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = SuitabilityAnalysisProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
