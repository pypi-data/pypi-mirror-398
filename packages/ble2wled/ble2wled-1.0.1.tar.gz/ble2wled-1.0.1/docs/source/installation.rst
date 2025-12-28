Installation
=============

BLE2WLED can be installed from source. PyPI publication is planned for future releases.

From Source
-----------

Prerequisites
~~~~~~~~~~~~~

- Python 3.10 or higher
- pip
- git (to clone the repository)

Installation Steps
~~~~~~~~~~~~~~~~~~~

1. **Clone the repository:**

   .. code-block:: bash

       git clone https://github.com/tobus3000/ble2wled.git
       cd ble2wled

2. **Install in development mode (recommended for development):**

   .. code-block:: bash

       pip install -e ".[dev]"

   This installs BLE2WLED with all development dependencies (testing, linting, documentation).

3. **Or install in standard mode (for users):**

   .. code-block:: bash

       pip install -e .

   This installs only the runtime dependencies.

Verify Installation
~~~~~~~~~~~~~~~~~~~

Verify the installation was successful:

.. code-block:: bash

    python -c "from ble2wled import BeaconState; print('BLE2WLED installed successfully')"

Run the simulator to verify everything works:

.. code-block:: bash

    python -m ble2wled.cli_simulator --duration 5

You should see an animated LED strip visualization for 5 seconds.

Dependencies
~~~~~~~~~~~~

**Core Dependencies:**

- ``paho-mqtt`` - MQTT client library for beacon data reception
- ``requests`` - HTTP library for WLED device communication
- ``python-dotenv`` - .env file support for configuration

**Development Dependencies:**

- ``pytest`` - Testing framework
- ``pytest-cov`` - Code coverage reporting
- ``sphinx`` - Documentation generation
- ``sphinx-rtd-theme`` - ReadTheDocs theme for Sphinx
- ``myst-parser`` - Markdown support in Sphinx
- ``ruff`` - Code linting and formatting

Virtual Environment (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's recommended to use a virtual environment to avoid conflicts with system packages:

.. code-block:: bash

    # Create virtual environment
    python -m venv venv

    # Activate virtual environment
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    venv\Scripts\activate

    # Install BLE2WLED
    pip install -e ".[dev]"

Installing from PyPI (Future)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once BLE2WLED is published to PyPI, installation will be as simple as:

.. code-block:: bash

    pip install ble2wled

Troubleshooting Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**ImportError: No module named 'ble2wled'**

Make sure you've installed the package:

.. code-block:: bash

    pip install -e .

**MQTT Connection Error**

Ensure:
- MQTT broker is running and accessible
- Correct broker host and port in configuration
- Network connectivity between your machine and broker

**WLED Connection Error**

Ensure:
- WLED device is powered on and connected to the network
- Correct WLED host/IP address in configuration
- UDP or HTTP port is accessible (21324 for UDP, 80 for HTTP)

Next Steps
----------

- :doc:`quickstart` - Get started in 5 minutes
- :doc:`guides/configuration` - Learn about configuration options
