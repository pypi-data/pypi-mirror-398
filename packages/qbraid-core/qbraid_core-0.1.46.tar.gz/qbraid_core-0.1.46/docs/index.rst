.. raw:: html
   
   <h1 style="text-align: center">
      <img src="./_static/logo.png" alt="qbraid logo" style="width:60px;height:60px;">
      <span> qBraid</span>
      <span style="color:#808080"> | CORE</span>
   </h1>
   <p style="text-align:center;font-style:italic;color:#808080">
      Python client for developing software with qBraid cloud services
   </p>

Overview
---------

Python library providing core abstractions for software development within the qBraid ecosystem, and a low-level interface
to a growing array of qBraid cloud services. The qbraid-core package forms the foundational base for the `qBraid CLI <https://pypi.org/project/qbraid-cli/>`_,
the `qBraid SDK <https://pypi.org/project/qbraid/>`_, and the `jupyter-environment-manager <https://pypi.org/project/jupyter-environment-manager/>`_.

.. seealso::

   - `qbraid-core-js <https://qbraid.github.io/qbraid-core-js/>`_

Installation
--------------

You can install qbraid-core from PyPI with:

.. code-block:: bash

   pip install qbraid-core


Resources
-----------

- `User Guide <https://docs.qbraid.com/core/user-guide>`_
- `API Reference <https://qbraid.github.io/qbraid-core/api/qbraid_core.html>`_


.. toctree::
   :maxdepth: 1
   :caption: SDK API Reference
   :hidden:

   qbraid <https://qbraid.github.io/qBraid/api/qbraid.html>
   qbraid.programs <https://qbraid.github.io/qBraid/api/qbraid.programs.html>
   qbraid.interface <https://qbraid.github.io/qBraid/api/qbraid.interface.html>
   qbraid.transpiler <https://qbraid.github.io/qBraid/api/qbraid.transpiler.html>
   qbraid.passes <https://qbraid.github.io/qBraid/api/qbraid.passes.html>
   qbraid.runtime <https://qbraid.github.io/qBraid/api/qbraid.runtime.html>
   qbraid.visualization <https://qbraid.github.io/qBraid/api/qbraid.visualization.html>

.. toctree::
   :caption: QIR API Reference
   :hidden:

   qbraid_qir <https://qbraid.github.io/qbraid-qir/api/qbraid_qir.html>
   qbraid_qir.cirq <https://qbraid.github.io/qbraid-qir/api/qbraid_qir.cirq.html>
   qbraid_qir.qasm3 <https://qbraid.github.io/qbraid-qir/api/qbraid_qir.qasm3.html>

.. toctree::
   :maxdepth: 1
   :caption: CORE API Reference
   :hidden:

   api/qbraid_core
   api/qbraid_core.services

.. toctree::
   :caption: PYQASM API Reference
   :hidden:

   pyqasm <https://qbraid.github.io/pyqasm/api/pyqasm.html>