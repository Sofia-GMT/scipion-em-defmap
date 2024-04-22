=======================
Scipion DefMap plugin
=======================

This is a plugin for **scipion** for DefMap, a program that predicts molecular dynamics properties from cryo-EM maps.

==========================
Steps to use this plugin
==========================

**Install the plugin in devel mode**

.. code-block::

    git clone https://github.com/Sofia-GMT/scipion-em-defmap.git
    scipion3 installp -p /SCIPION_HOME/plugins/scipion-em-defmap --devel

If installation fails, you can access pip options like:

.. code-block::

    scipion3 python -m pip ... (list, install, uninstall)

**Running tests**

.. code-block::

    scipion tests defmap.tests
    