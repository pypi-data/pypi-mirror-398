# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# FileType: SOURCE
# FileCopyrightText: 2025, GFZ Helmholtz Centre for Geosciences
# FileCopyrightText: 2025, Daniel Scheffler (danschef@gfz.de)

"""This module provides a QGIS EnMAPBox GUI for EnFROSP."""

import os
import traceback
from importlib.metadata import version as get_version, PackageNotFoundError

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction, QMessageBox
from enmapbox.gui.applications import EnMAPBoxApplication as _EnMAPBoxApplication
from qgis.core import QgsApplication, Qgis

from .version import __version__
from .enfrosp_algorithm import EnFROSPAlgorithm

VERSION = __version__
LICENSE = 'GPL-3.0-or-later'
APP_DIR = os.path.dirname(__file__)
APP_NAME = 'EnFROSP EnMAPBox App'


class EnFROSPEnMAPBoxApp(_EnMAPBoxApplication):
    """The EnFROSP GUI class."""

    def __init__(self, enmapBox, parent=None):
        super(EnFROSPEnMAPBoxApp, self).__init__(enmapBox, parent=parent)

        self.name = APP_NAME
        self.version = VERSION
        self.licence = LICENSE
        self.ALG = EnFROSPAlgorithm

    def icon(self):
        """Return the QIcon of EnFROSPEnMAPBoxApp.

        :return: QIcon()
        """
        return QIcon(os.path.join(APP_DIR, 'icon.png'))

    def menu(self, appMenu):
        """Return a QMenu that will be added to the parent `appMenu`.

        :param appMenu:
        :return: QMenu
        """
        assert isinstance(appMenu, QMenu)
        """
        Specify menu, submenus and actions that become accessible from the EnMAP-Box GUI
        :return: the QMenu or QAction to be added to the "Applications" menu.
        """

        # this way you can add your QMenu/QAction to another menu entry, e.g. 'Tools'
        # appMenu = self.enmapbox.menu('Tools')

        menu_entry = 'Snow applications'
        _alphanumeric_menu = False
        try:
            # alphanumeric menu ordering was implemented in EnMAP-Box around 3.10.1
            menu = self.utilsAddMenuInAlphanumericOrder(appMenu, menu_entry)
            _alphanumeric_menu = True
        except AttributeError:
            menu = appMenu.addMenu(menu_entry)
        menu.setIcon(self.icon())

        # add a QAction that starts a process of your application.
        # In this case it will open your GUI.
        a = menu.addAction('About EnFROSP')
        a.triggered.connect(self.showAboutDialog)
        a = menu.addAction('Start EnFROSP (EnMAP Fast Retrieval Of Snow Properties)')
        assert isinstance(a, QAction)
        a.triggered.connect(self.startGUI)

        if not _alphanumeric_menu:
            appMenu.addMenu(menu)

        return menu

    def showAboutDialog(self):  # TODO
        try:
            _enfrosp_version_str = get_version('enfrosp')
        except PackageNotFoundError:
            _enfrosp_version_str = 'NA (not installed in QGIS environment)'
        QMessageBox.information(
            None, self.name,
            f'EnFROSP is a Python algorithm developed at GFZ Potsdam for advanced atmospheric correction of '
            f'EnMAP hyperspectral satellite data over snow and ice. It implements several snow parameter retrieval '
            f'algorithms originally developed in FORTRAN by Alexander Kokhanovsky, enabling the retrieval of key snow '
            f'properties such as grain size, albedo, and impurities for both clean and polluted snow. EnFROSP takes '
            f'the official EnMAP L1C data product, provided by the German Aerospace Center (DLR), as input and '
            f'delivers the retrieval results as ENVI BSQ files.\n'
            f'\n'
            f'GUI version:  {self.version}\n'
            f'EnFROSP backend version:  {_enfrosp_version_str}\n'
            f'\n'
            f'Python implementation:  Daniel Scheffler, GFZ Potsdam\n'
            f'Core algorithm (FORTRAN):  Alexander Kokhanovsky, GFZ Potsdam'
        )

    def processingAlgorithms(self):
        """Return the QGIS Processing Framework GeoAlgorithms specified by your application.

        :return: [list-of-GeoAlgorithms]
        """
        return [self.ALG()]

    def startGUI(self):
        """Open the GUI."""
        try:
            from processing.gui.AlgorithmDialog import AlgorithmDialog

            alg = QgsApplication.processingRegistry().algorithmById('enmapbox:EnFROSPAlgorithm')
            assert isinstance(alg, self.ALG)
            dlg = AlgorithmDialog(alg.create(), in_place=False, parent=self.enmapbox.ui)
            dlg.show()

            return dlg

        except Exception as ex:
            msg = str(ex)
            msg += '\n' + str(traceback.format_exc())
            self.enmapbox.messageBar().pushMessage(APP_NAME, 'Error', msg, level=Qgis.Critical, duration=10)

            return None
