Installation
============

Requirements
------------

* Python 3.7 or higher
* requests >= 2.25.0

Installing from PyPI
--------------------

The easiest way to install Power Switch Pro is via pip:

.. code-block:: bash

    pip install power_switch_pro

Installing from Source
----------------------

You can also install from source:

.. code-block:: bash

    git clone https://github.com/bryankemp/power_switch_pro.git
    cd power_switch_pro
    pip install -e .

Development Installation
------------------------

For development, install with dev dependencies:

.. code-block:: bash

    pip install -e ".[dev,docs]"

This installs additional tools for testing, linting, and documentation building.

Verifying Installation
----------------------

To verify the installation, you can run:

.. code-block:: python

    import power_switch_pro
    print(power_switch_pro.__version__)
