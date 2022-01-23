# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SuitabilityRanker
 A QGIS plugin
 Vector-based site suitability analysis

        copyright            : (C) 2022 by John Allanach
        email                : johnallanach@protonmail.com
 ***************************************************************************/
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SuitabilityAnalysis class from file SuitabilityAnalysis.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .suitability_analysis import SuitabilityAnalysis
    return SuitabilityAnalysis(iface)
