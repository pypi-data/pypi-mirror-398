.. SPDX-License-Identifier: GPL-3.0-or-later
.. FileType: DOCUMENTATION
.. FileCopyrightText: 2025, GFZ Helmholtz Centre for Geosciences
.. FileCopyrightText: 2025, Daniel Scheffler (danschef@gfz.de)



.. _installation:

============
Installation
============


Using Mamba (recommended)
-------------------------

Using mamba_ (latest version recommended), EnFROSP EnMAP-Box-App is installed as follows:

1. Update the base environment and install system-packages

   .. code-block:: bash

    $ mamba activate base
    $ mamba update all


2. Clone the EnFROSP EnMAP-Box-App source code:

   .. code-block:: bash

    $ git clone git@git.gfz.de:EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp.git
    $ cd enfrosp_enmapboxapp


3. Create virtual environment for enfrosp_enmapboxapp and install all dependencies from the environment_enfrosp_enmapboxapp.yml file and install EnFROSP EnMAP-Box-App itself:

   .. code-block:: bash

    $ mamba env create -f tests/CI_docker/context/environment_enfrosp_enmapboxapp.yml
    $ mamba activate enfrosp_enmapboxapp
    $ pip install .


This is the preferred method to install EnFROSP EnMAP-Box-App, as it always installs the most recent stable release and
automatically resolves all the dependencies.



.. _mamba: https://github.com/mamba-org/mamba
