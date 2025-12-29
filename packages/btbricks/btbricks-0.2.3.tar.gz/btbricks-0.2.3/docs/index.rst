btbricks documentation
========================

.. image:: ../img/btbricks.png
   :alt: btbricks logo
   :align: center
   :width: 200px

Installation
============

Using ViperIDE Package Manager (Recommended)
--------------------------------------------

1. Open **ViperIDE** on your device
2. Go to **Tools** → **Package Manager**
3. Select **Install Package via Link**
4. Enter the package link: ``https://github.com/antonvh/btbricks``
5. Follow the on-screen prompts to complete installation

Using micropip from PyPI
------------------------

.. code-block:: python

   import micropip
   await micropip.install("btbricks")

Note: ``micropip`` must be available on the target board and may require an internet connection from the device.

API Reference
=============

.. automodule:: btbricks
   :members:
   :undoc-members:
   :show-inheritance:



