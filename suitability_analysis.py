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

from lib2to3.pgen2.pgen import DFAState
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
import pandas as pd
import time


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


    def validateWeights(self):
        """ checks that input weights sum to 100 """

        weight_sum = 0
        for row in range(self.dlg.fieldTable.rowCount()):
            weight_sum += int(float(self.dlg.fieldTable.item(row,3).text()))

        if round(weight_sum) == 100:
            pass
        else: 
            iface.messageBar().pushMessage("Input error",
                "Field weights must sum to 100",
                level = Qgis.Critical,
                duration = 10)
            return False

        return True


    def updateFields(self):
        """ reload the available fields when layer is changed """

        self.dlg.fieldSelector.clear()
        self.dlg.fieldTable.clearContents()
        self.dlg.fieldTable.setRowCount(0)
        self.dlg.fieldSelector.addItems([str(x.name()) for x in
            self.dlg.layerInput.currentLayer().fields() if x.isNumeric()])


    def populateTable(self):
        """ populate QTableWidget that shows the fields to be analysed. 
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
                
                field_name = QTableWidgetItem( field_name )
                lower = QTableWidgetItem(str( minValue ))
                upper = QTableWidgetItem(str( maxValue ))
                weight = QTableWidgetItem(str( round( 100 / len( selected_fields ), 2 )))
                effect = QTableWidgetItem( "+" )

                lower.setTextAlignment(Qt.AlignHCenter)
                upper.setTextAlignment(Qt.AlignHCenter)
                weight.setTextAlignment(Qt.AlignHCenter)
                effect.setTextAlignment(Qt.AlignHCenter)

                field_name.setFlags(flags)
                self.dlg.fieldTable.setItem(current, 0, field_name)
                self.dlg.fieldTable.setItem(current, 1, lower)
                self.dlg.fieldTable.setItem(current, 2, upper)
                self.dlg.fieldTable.setItem(current, 3, weight)
                self.dlg.fieldTable.setItem(current, 4, effect)


    def fetchCriteria(self):
        """ get suitability criteria from input form """
        self.criteria = {}

        for row in range(self.dlg.fieldTable.rowCount()):
            field_name = self.dlg.fieldTable.item(row,0).text()

            self.criteria[field_name] = {
                "lower": float(self.dlg.fieldTable.item(row,1).text()),
                "upper": float(self.dlg.fieldTable.item(row,2).text()),
                "weight": int(float(self.dlg.fieldTable.item(row,3).text())),
                "effect": self.dlg.fieldTable.item(row,4).text()
            }


    def createOutputLayer(self):
        """ create output memory layer """
        # get input layer information 
        layer = self.dlg.layerInput.currentLayer()
        layer_type = {'0':'Point', '1':'LineString', '2':'Polygon'}
        layer_crs = layer.crs().authid()

        # duplicated layer into memory
        mem_layer = QgsVectorLayer(layer_type[str(layer.geometryType())] 
                        + "?crs=" + str(layer_crs), 
                        "suitability_output", "memory")
        mem_layer_data = mem_layer.dataProvider()

        # copy attributes from input layer to memory layer
        attr_fields = layer.dataProvider().fields().toList()
        mem_layer_data.addAttributes(attr_fields)
        mem_layer.updateFields()

        # copy features from input layer to memory layer
        feats = [feat for feat in layer.getFeatures()]
        mem_layer_data.addFeatures(feats)

        self.outputLayer = mem_layer


    def pandify(self):
        """ create pandas dataframe for numerical processing """
        # list columns to include in the dataframe
        cols = [f for f in self.criteria] 
        cols.append('FID')

        # generator to yield one row at a time
        datagen = ([f[col] for col in cols] for f in self.outputLayer.getFeatures())

        # create dataframe
        self.df = pd.DataFrame.from_records(data=datagen, columns=cols)


    def calculations(self):
        """ normalize data & calcuate score and rank """
        df = self.df
        criteria = self.criteria

        aggregate_score = 0
        for field in criteria: 
            lower = criteria[field]['lower']
            upper = criteria[field]['upper']
            weight = criteria[field]['weight']
            effect = criteria[field]['effect']

            # trim df by lower/upper bounds
            df = df[df[field] >= lower]
            df = df[df[field] <= upper]
            
            # normalize data
            max_value = df[field].max()
            min_value = df[field].min()
            if effect == "+":
                df[field] = (df[field] - min_value) / (max_value - min_value)
            elif effect == "-":
                df[field] = (max_value - df[field]) / (max_value - min_value)
            else:
                pass

            # calculate weighted score
            weighted_score = df[field] * weight
            aggregate_score += weighted_score

        df['score'] = aggregate_score
        df['rank'] = df['score'].rank(ascending=False)

        self.df = df


    def updateSHP(self):
        """ merge dataframe back into memory layer """

        vpr = self.outputLayer.dataProvider()            

        with edit(self.outputLayer):
            vpr.addAttributes([QgsField('score', QVariant.Double)])
            vpr.addAttributes([QgsField('rank', QVariant.Double)])
            self.outputLayer.updateFields()

            feat_list = [( feat.attribute(feat.fieldNameIndex('FID') ), 
                            feat.id()) for feat in self.outputLayer.getFeatures()]

            score_field = vpr.fieldNameIndex('score')
            rank_field = vpr.fieldNameIndex('rank')

            for feat in feat_list:
                try:
                    fid = feat[0]
                    score_value = float(self.df.loc[self.df['FID']==fid]['score'])
                    rank_value = float(self.df.loc[self.df['FID']==fid]['rank'])
                    self.outputLayer.changeAttributeValue(feat[1], score_field, score_value)
                    self.outputLayer.changeAttributeValue(feat[1], rank_field, rank_value)
                except:
                    vpr.deleteFeatures([ fid ])
                    #self.outputLayer.changeAttributeValue(feat[1], score_field, 0)
                    #self.outputLayer.changeAttributeValue(feat[1], rank_field, 1.7976931348623158e+308)


    def addOutputLayerToMap(self):
        """ add memory layer to map """
        suitability_output = self.outputLayer
        QgsProject.instance().addMapLayer(suitability_output)


    def run(self):
        """ run method that performs all the real work """   

        startTime = time.time()

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
        self.dlg.addFields.clicked.connect(self.populateTable)

        # reset form
        self.dlg.addFields_2.clicked.connect(self.updateFields)

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:

            #if self.validateWeights() == True:

            self.fetchCriteria()
            self.createOutputLayer()
            self.pandify()
            self.calculations()
            self.updateSHP()
            self.addOutputLayerToMap()

            #executionTime = str(round((time.time() - startTime), 2))

            iface.messageBar().pushMessage("Success",
                "Suitability analysis completed.",
                #"Suitability analysis completed in " + executionTime + " s.",
                level = Qgis.Success,
                duration = 10)
