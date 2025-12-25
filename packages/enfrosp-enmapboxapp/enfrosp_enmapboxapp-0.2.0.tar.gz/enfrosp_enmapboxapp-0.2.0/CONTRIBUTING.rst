.. SPDX-License-Identifier: GPL-3.0-or-later
.. FileType: DOCUMENTATION
.. FileCopyrightText: 2025, GFZ Helmholtz Centre for Geosciences
.. FileCopyrightText: 2025, Daniel Scheffler (danschef@gfz.de)



.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitLab issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitLab issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

EnFROSP EnMAP-Box-App could always use more documentation, whether as part of the
official EnFROSP EnMAP-Box-App docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Commit Changes
--------------

How to
~~~~~~

0. Update the base environment and install system-packages::

    $ apt-get update -y && \
       echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    $ apt-get install -y -q dialog apt-utils && \
    $ apt-get install -y -q \
          bzip2 \
          curl \
          fish \
          gcc \
          gdb \
          make \
          nano \
          python3-pip \
          tree \
          wget \
          cron \
          zip \
          unzip \
          vim \
          bash-completion \
          git \
          git-lfs && \
    $ git-lfs install

    $ mamba activate base
    $ mamba update all

1. Clone the repository::

    $ git clone git@git.gfz.de:EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp.git

2. Create an environment::

    $ cd enfrosp_enmapboxapp/
    $ mamba env create -f enfrosp_enmapboxapp/tests/CI_docker/context/environment_enfrosp_enmapboxapp.yml
    $ pip install .

3. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes, check that your changes pass flake8 and the
   tests::

    $ make pytest
    $ make lint
    $ make urlcheck


5. Commit your changes and push your branch to GitLab::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push -u origin name-of-your-bugfix-or-feature

6. Submit a merge request through the GitLab website.

Sign your commits
~~~~~~~~~~~~~~~~~

Please note that our license terms only allow signed commits.
A guideline how to sign your work can be found here: https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work

If you are using the PyCharm IDE, the `Commit changes` dialog has an option called `Sign-off commit` to
automatically sign your work.


License header
~~~~~~~~~~~~~~

If you commit new Python files, please note that they have to contain the following license header:

.. code:: bash

    # SPDX-License-Identifier: GPL-3.0-or-later
    # FileType: SOURCE
    # FileCopyrightText: 2025, GFZ Helmholtz Centre for Geosciences
    # FileCopyrightText: 2025, Daniel Scheffler (danschef@gfz.de)


Merge Request Guidelines
------------------------

Before you submit a pull request, check that it meets these guidelines:

1. The merge request should include tests.
2. If the merge request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for the latest three Python versions. Check
   https://git.gfz.de/EnMAP/GFZ_Tools_EnMAP_BOX/enfrosp_enmapboxapp/-/merge_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

$ pytest tests.test_enfrosp_enmapboxapp -k <test_name_prefix>

Code of Conduct
---------------

Please note that this project is released with a `Contributor Code of Conduct`_.
By participating in this project you agree to abide by its terms.

.. _`Contributor Code of Conduct`: CODE_OF_CONDUCT.rst
