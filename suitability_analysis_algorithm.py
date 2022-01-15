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


from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingMultiStepFeedback)

import processing


class SuitabilityAnalysisAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. 
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'input', 
                'Input Layer', 
                types=[QgsProcessing.TypeVectorPoint], 
                defaultValue=None
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'Output', 
                'Suitability Output', 
                type=QgsProcessing.TypeVectorAnyGeometry, 
                createByDefault=True, 
                supportsAppend=True, 
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                'Weight', 
                'Feature Weight', 
                type=QgsProcessingParameterNumber.Double, 
                minValue=-1.79769e+308, 
                maxValue=1.79769e+308, 
                defaultValue=1
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        """
        Here is where the processing itself takes place.
        """

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        model_steps = 1
        feedback = QgsProcessingMultiStepFeedback(model_steps, model_feedback)
        results = {}
        outputs = {}

        alg_params = {
            'INPUT': parameters['input'],
            'FIELD_NAME':'calculated', # CHANGE ACCORDING TO INPUT FIELD
            'FIELD_TYPE':0, # FLOAT TYPE
            'FIELD_LENGTH':0,
            'FIELD_PRECISION':0,
            'FORMULA':' \"noise_km\" * ' + str(parameters['Weight']),
            'OUTPUT': parameters['Output']
            }

        outputs['FieldCalculator'] = processing.run(
            'native:fieldcalculator', 
            alg_params, 
            context=context, 
            feedback=feedback, 
            is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        results['Output'] = outputs['FieldCalculator']['OUTPUT']

        # Return the results of the algorithm. 
        return results     


    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Suitability Analysis'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SuitabilityAnalysisAlgorithm()
