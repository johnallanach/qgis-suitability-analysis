# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SuitabilityRanker
 A QGIS plugin
 Vector-based site suitability analysis

        copyright            : (C) 2022 by John Allanach
        email                : j8hnallnach@gmail.com
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis.gui import *
from qgis.core import *
from qgis.utils import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .suitability_analysis_dialog import SuitabilityAnalysisDialog
import os.path

import numpy as np


class SuitabilityAnalysis:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SuitabilityAnalysis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Suitability Analysis')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SuitabilityAnalysis', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/suitability_analysis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Suitability Analysis'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

        #self.dlg.pushButton.clicked.connect(self.run1)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Suitability Analysis'),
                action)
            self.iface.removeToolBarIcon(action)









    def updateFields(self):
        """Reload the available fields when layer is changed"""

        self.dlg.fieldSelector.clear()
        self.dlg.fieldTable.clearContents()
        self.dlg.fieldTable.setRowCount(0)
        self.dlg.fieldSelector.addItems([str(x.name()) for x in
            self.dlg.layerInput.currentLayer().fields() if x.isNumeric()])


    def populateFields(self):
        """Populate QTableWidget that shows the fields to be analysed. 
        Called after user clicks the "Add selected fields" button"""

        selected_fields = self.dlg.fieldSelector.selectedItems()
        flags = Qt.ItemIsEnabled
        if len(selected_fields) > 0:
            self.dlg.fieldTable.clearContents()
            self.dlg.fieldTable.setRowCount(len(selected_fields))

            layer = self.dlg.layerInput.currentLayer()

            for current, i in enumerate(selected_fields):
                field_name = str(i.text())
                field_index = layer.fields().lookupField(field_name)
                maxValue = layer.maximumValue(field_index)
                minValue = layer.minimumValue(field_index)
                
                indicator = QTableWidgetItem( field_name )
                lower = QTableWidgetItem(str( round( minValue, 2)))
                upper = QTableWidgetItem(str( round( maxValue,2 )))
                weight = QTableWidgetItem(str( round( 100 / len( selected_fields ), 2 )))
                influence = QTableWidgetItem( "+" )

                lower.setTextAlignment(Qt.AlignHCenter)
                upper.setTextAlignment(Qt.AlignHCenter)
                weight.setTextAlignment(Qt.AlignHCenter)
                influence.setTextAlignment(Qt.AlignHCenter)

                indicator.setFlags(flags)
                self.dlg.fieldTable.setItem(current, 0, indicator)
                self.dlg.fieldTable.setItem(current, 1, lower)
                self.dlg.fieldTable.setItem(current, 2, upper)
                self.dlg.fieldTable.setItem(current, 3, weight)
                self.dlg.fieldTable.setItem(current, 4, influence)


    def fetchCriteria(self):

        criteria = {}

        for row in range(self.dlg.fieldTable.rowCount()):
            indicator = self.dlg.fieldTable.item(row,0).text()
            #lower = int(float(self.dlg.fieldTable.item(row,1).text()))
            #upper = int(float(self.dlg.fieldTable.item(row,2).text()))
            #weight = int(float(self.dlg.fieldTable.item(row,3).text()))
            #influence = self.dlg.fieldTable.item(row,4).text()

            criteria[indicator] = {
                "lower": int(float(self.dlg.fieldTable.item(row,1).text())),
                "upper": int(float(self.dlg.fieldTable.item(row,2).text())),
                "weight": int(float(self.dlg.fieldTable.item(row,3).text())),
                "influence": self.dlg.fieldTable.item(row,4).text()
            }


    def layerToNumpy(self):
        """"""

        pass


    def validateWeights(self):
        """Checks that input weights sum to 100"""

        weight_sum = 0
        for row in range(self.dlg.fieldTable.rowCount()):
            weight_sum += int(self.dlg.fieldTable.item(row,3).text())

        if weight_sum == 100:
            pass
        else: 
            iface.messageBar().pushMessage("Input error",
                "Field weights must sum to 100",
                level = Qgis.Critical,
                duration = 10)
            return False

        return True
    

    def trimThresholds(self):
        """Removes features that are below or above the
        lower or upper thresholds, respectively"""

        layer = self.dlg.layerInput.currentLayer()
        vpr = layer.dataProvider()

        for row in range(self.dlg.fieldTable.rowCount()):
            indicator = self.dlg.fieldTable.item(row,0).text()
            lower = int(float(self.dlg.fieldTable.item(row,1).text()))
            upper = int(float(self.dlg.fieldTable.item(row,2).text()))

            with edit(layer):
                for feature in layer.getFeatures():
                    feature_value = feature[indicator]
                    if (feature_value > upper or 
                        feature_value < lower):
                        vpr.deleteFeatures([feature.id()])


    def createTempFields(self):
        """Creates temporary calculation fields"""

        layer = self.dlg.layerInput.currentLayer()
        vpr = layer.dataProvider()

        for row in range(self.dlg.fieldTable.rowCount()):
            indicator = self.dlg.fieldTable.item(row,0).text()
            #field_index = layer.fields().lookupField(field_name)
            field_name_score = indicator + "_s"              

            with edit(layer):
                vpr.addAttributes([QgsField(field_name_score, QVariant.Double)])
                layer.updateFields()


    def standardizeFields(self):
        """Main calculations to standardize the selected fields"""

        layer = self.dlg.layerInput.currentLayer()
        #vpr = layer.dataProvider()
        #vpr.addAttributes([QgsField('Score', QVariant.Double)])

        for row in range(self.dlg.fieldTable.rowCount()):
            indicator = self.dlg.fieldTable.item(row,0).text()
            field_name_score = indicator + "_s"  
            field_index = layer.fields().lookupField(indicator)
            maxValue = layer.maximumValue(field_index)
            minValue = layer.minimumValue(field_index)  

            weight = float(self.dlg.fieldTable.item(row,3).text())  
            influence = self.dlg.fieldTable.item(row,4).text()           

            #aggregate_score = 0 

            with edit(layer):
                if influence == "+":
                    for feature in layer.getFeatures():
                        score = float((feature[indicator]-minValue)/(maxValue-minValue))
                        weighted_score = score * weight
                        feature.setAttribute(feature.fieldNameIndex(field_name_score), 
                            weighted_score)
                        layer.updateFeature(feature) 
                elif influence == "-":
                    for feature in layer.getFeatures():
                        score = float((maxValue-feature[indicator])/(maxValue-minValue))
                        weighted_score = score * weight
                        feature.setAttribute(feature.fieldNameIndex(field_name_score), 
                            weighted_score)
                        layer.updateFeature(feature) 
                else:
                    pass
            

    def calculateAggregateScore(self):
        """"""
        layer = self.dlg.layerInput.currentLayer()
        vpr = layer.dataProvider()
             
        with edit(layer):
            vpr.addAttributes([QgsField('Score', QVariant.Double)])
            for feature in layer.getFeatures():
                aggregate_score = []
                feature.setAttribute(feature.fieldNameIndex('Score'), 
                            aggregate_score)
                layer.updateFeature(feature)
            layer.updateFields()

        pass


    def calculateFinalRank(self):
        """"""
        layer = self.dlg.layerInput.currentLayer()
        vpr = layer.dataProvider()
             
        with edit(layer):
            vpr.addAttributes([QgsField('Rank', QVariant.Double)])
            # CALCULATIONS 
            layer.updateFields()

        pass


    def deleteTempFields(self):
        """"""
        pass


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SuitabilityAnalysisDialog()

        # show the dialog
        self.dlg.show()

        # populate the initial available fields
        self.dlg.fieldSelector.addItems([str(x.name()) for x in 
            self.dlg.layerInput.currentLayer().fields() if x.isNumeric()])

        # update fields when active layer changed
        self.dlg.layerInput.layerChanged.connect(self.updateFields)

        self.dlg.fieldSelector.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # populate table with selected fields
        self.dlg.addFields.clicked.connect(self.populateFields)

        # reset form
        self.dlg.addFields_2.clicked.connect(self.updateFields)

        #self.dlg.fieldTable.item(row,3).itemChanged.connect(self.updateFields)

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            #if self.validateWeights() == True:
            self.fetchCriteria()
            #self.trimThresholds()
            #self.createTempFields()
            #self.standardizeFields()
            #self.applyScoreWeights()
            #self.calculateAggregateScore()
            #self.calculateFinalRank()
            #self.deleteTempFields()
            
            iface.messageBar().pushMessage("Success",
                "Suitability analysis complete.",
                level = Qgis.Success,
                duration = 10)
