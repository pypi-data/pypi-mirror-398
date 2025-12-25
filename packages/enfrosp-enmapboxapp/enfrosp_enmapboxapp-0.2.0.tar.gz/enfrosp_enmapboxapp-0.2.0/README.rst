.. SPDX-License-Identifier: GPL-3.0-or-later
.. FileType: DOCUMENTATION
.. FileCopyrightText: 2025, GFZ Helmholtz Centre for Geosciences
.. FileCopyrightText: 2025, Daniel Scheffler (danschef@gfz.de)



=====================
EnFROSP EnMAP-Box-App
=====================

A graphical user interface for EnFROSP as an add-in for the EnMAP-Box QGIS plugin.
----------------------------------------------------------------------------------

The EnFROSP EnMAP-Box-App is graphical user interface for the EnFROSP_ Python algorithm
(EnMAP Fast Retrieval Of Snow Properties) and serves as an add-in for the `EnMAP-Box`_ QGIS plugin.
As part of the snow applications entry, it is added to the applications menu of the EnMAP-Box and
offers the user an advanced atmospheric correction of EnMAP hyperspectral satellite data over snow and ice.

It implements several snow parameter retrieval algorithms originally developed in FORTRAN by
Alexander Kokhanovsky, enabling the retrieval of key snow properties such as grain size, albedo,
and impurities for both clean and polluted snow. EnFROSP takes the official EnMAP L1C data product,
provided by the German Aerospace Center (DLR), as input and delivers the retrieval results as ENVI BSQ files.

General information about this EnMAP-Box app can be found in the `EnFROSP EnMAP-Box app documentation`_.
For details, e.g., about the algorithms implemented in EnFROSP, take a look at the `EnFROSP backend documentation`_.


* License: GPL-3.0-or-later
* Copyright GFZ Helmholtz Centre for Geosciences, Daniel Scheffler
* Documentation: https://EnMAP.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/doc/


How the GUI looks like
----------------------

.. image:: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/raw/main/docs/images/screenshot_enfrosp_gui_v0.2.0.png
    :width: 1250 px
    :height: 687 px
    :scale: 70 %



Status
------
.. image:: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/badges/main/pipeline.svg
        :target: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/pipelines
        :alt: Pipelines
.. image:: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/badges/main/coverage.svg
        :target: coverage_
        :alt: Coverage
.. image:: https://img.shields.io/pypi/v/enfrosp_enmapboxapp.svg
        :target: https://pypi.python.org/pypi/enfrosp_enmapboxapp
        :alt: PyPI
.. image:: https://img.shields.io/conda/vn/conda-forge/enfrosp_enmapboxapp.svg
        :target: https://anaconda.org/channels/conda-forge/packages/enfrosp_enmapboxapp/overview
        :alt: conda-forge
.. image:: https://img.shields.io/pypi/l/enfrosp_enmapboxapp.svg
        :target: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/-/blob/main/LICENSES/GPL-3.0-or-later.txt
        :alt: License
.. image:: https://img.shields.io/pypi/pyversions/enfrosp_enmapboxapp.svg
        :target: https://img.shields.io/pypi/pyversions/enfrosp_enmapboxapp.svg
        :alt: Python versions
.. image:: https://img.shields.io/pypi/dm/enfrosp_enmapboxapp.svg
        :target: https://pypi.python.org/pypi/enfrosp_enmapboxapp
        :alt: PyPI downloads
.. image:: https://img.shields.io/static/v1?label=Documentation&message=GitLab%20Pages&color=orange
        :target: `EnFROSP EnMAP-Box app documentation`_
        :alt: Documentation

..
  for adding a DOI badge fill and uncomment the following:
  image:: (link to your DOI badge svg on zenodo)
  target: (link to your DOI on zenodo)
  alt: DOI


See also the latest coverage_ report and the pytest_ HTML report.


History / Changelog
-------------------

You can find the protocol of recent changes in the EnFROSP EnMAP-Box-App package
`here <https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/-/blob/main/HISTORY.rst>`__.


Developed by
------------

enfrosp_enmapboxapp has been developed by Daniel Scheffler, located at the `GFZ Helmholtz Centre for Geosciences <https://www.gfz.de/en/>`_.

Credits
-------

This software was developed within the context of the EnMAP project supported by the DLR Space Agency with
funds of the German Federal Ministry of Economic Affairs and Climate Action on the basis of a decision by
the German Bundestag: 50 EE 0850, 50 EE 1923, and 50 EE 2108.

This package was created with Cookiecutter_ and the `fernlab/cookiecutter-python-package`_ project template.

.. _EnFROSP: https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp
.. _EnFROSP EnMAP-Box app documentation: https://enmap.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/doc/
.. _EnFROSP backend documentation: https://EnMAP.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp/doc/
.. _EnMAP-Box: https://github.com/EnMAP-Box/enmap-box
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`fernlab/cookiecutter-python-package`: https://git.gfz.de/fernlab/products/cookiecutters/cookiecutter-python-package/
.. _coverage: https://EnMAP.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/coverage/
.. _pytest: https://EnMAP.git-pages.gfz-potsdam.de/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/test_reports/report.html
