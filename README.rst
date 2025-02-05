==========================
circuitpython_wifimanager
==========================

.. start short_desc

**Helper library for microcontrollers with builtin WiFi, such as the ESP32-S2.**

.. end short_desc

This library provides a similar interface to the Adafruit_ESP32SPI_ library's ``adafruit_esp32spi_wifimanager`` module,
but to support boards with builtin WiFi using the ``wifi`` module [1]_.

.. _Adafruit_ESP32SPI: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
.. [1] https://circuitpython.readthedocs.io/en/latest/shared-bindings/wifi/index.html

.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Tests
	  - |actions_linux| |actions_windows| |actions_macos|
	* - Activity
	  - |commits-latest| |commits-since| |maintained|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |actions_linux| image:: https://github.com/domdfcoding/circuitpython_wifimanager/workflows/Linux/badge.svg
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/domdfcoding/circuitpython_wifimanager/workflows/Windows/badge.svg
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/domdfcoding/circuitpython_wifimanager/workflows/macOS/badge.svg
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/domdfcoding/circuitpython_wifimanager/workflows/Flake8/badge.svg
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/domdfcoding/circuitpython_wifimanager/workflows/mypy/badge.svg
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://dependency-dash.repo-helper.uk/github/domdfcoding/circuitpython_wifimanager/badge.svg
	:target: https://dependency-dash.repo-helper.uk/github/domdfcoding/circuitpython_wifimanager/
	:alt: Requirements Status

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/domdfcoding/circuitpython_wifimanager?logo=codefactor
	:target: https://www.codefactor.io/repository/github/domdfcoding/circuitpython_wifimanager
	:alt: CodeFactor Grade

.. |license| image:: https://img.shields.io/github/license/domdfcoding/circuitpython_wifimanager
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/domdfcoding/circuitpython_wifimanager
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/domdfcoding/circuitpython_wifimanager/v0.0.0
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/domdfcoding/circuitpython_wifimanager
	:target: https://github.com/domdfcoding/circuitpython_wifimanager/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2025
	:alt: Maintenance

.. end shields

Installation
--------------

.. start installation

``circuitpython_wifimanager`` can be installed from GitHub.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install git+https://github.com/domdfcoding/circuitpython_wifimanager

.. end installation
