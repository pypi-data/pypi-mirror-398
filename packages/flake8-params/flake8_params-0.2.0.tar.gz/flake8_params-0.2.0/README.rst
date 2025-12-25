################
flake8-params
################

.. start short_desc

**A flake8 plugin which checks for mismatches between function signatures and docstring params.**

.. end short_desc


.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Docs
	  - |docs| |docs_check|
	* - Tests
	  - |actions_linux| |actions_windows| |actions_macos| |coveralls|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Activity
	  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |docs| image:: https://img.shields.io/readthedocs/flake8-params/latest?logo=read-the-docs
	:target: https://flake8-params.readthedocs.io/en/latest
	:alt: Documentation Build Status

.. |docs_check| image:: https://github.com/python-formate/flake8-params/workflows/Docs%20Check/badge.svg
	:target: https://github.com/python-formate/flake8-params/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |actions_linux| image:: https://github.com/python-formate/flake8-params/workflows/Linux/badge.svg
	:target: https://github.com/python-formate/flake8-params/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/python-formate/flake8-params/workflows/Windows/badge.svg
	:target: https://github.com/python-formate/flake8-params/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/python-formate/flake8-params/workflows/macOS/badge.svg
	:target: https://github.com/python-formate/flake8-params/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/python-formate/flake8-params/workflows/Flake8/badge.svg
	:target: https://github.com/python-formate/flake8-params/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/python-formate/flake8-params/workflows/mypy/badge.svg
	:target: https://github.com/python-formate/flake8-params/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://dependency-dash.repo-helper.uk/github/python-formate/flake8-params/badge.svg
	:target: https://dependency-dash.repo-helper.uk/github/python-formate/flake8-params/
	:alt: Requirements Status

.. |coveralls| image:: https://img.shields.io/coveralls/github/python-formate/flake8-params/master?logo=coveralls
	:target: https://coveralls.io/github/python-formate/flake8-params?branch=master
	:alt: Coverage

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/python-formate/flake8-params?logo=codefactor
	:target: https://www.codefactor.io/repository/github/python-formate/flake8-params
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/flake8-params
	:target: https://pypi.org/project/flake8-params/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/flake8-params?logo=python&logoColor=white
	:target: https://pypi.org/project/flake8-params/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/flake8-params
	:target: https://pypi.org/project/flake8-params/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/flake8-params
	:target: https://pypi.org/project/flake8-params/
	:alt: PyPI - Wheel

.. |license| image:: https://img.shields.io/github/license/python-formate/flake8-params
	:target: https://github.com/python-formate/flake8-params/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/python-formate/flake8-params
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/python-formate/flake8-params/v0.2.0
	:target: https://github.com/python-formate/flake8-params/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/python-formate/flake8-params
	:target: https://github.com/python-formate/flake8-params/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2025
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/flake8-params
	:target: https://pypi.org/project/flake8-params/
	:alt: PyPI - Downloads

.. end shields

|

Installation
--------------

.. start installation

``flake8-params`` can be installed from PyPI.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install flake8-params

.. end installation

flake8 codes
--------------

============== ============================================
Code           Description
============== ============================================
PRM001			PRM001 Docstring parameters in wrong order.
PRM002			PRM002 Missing parameters in docstring.
PRM003			PRM003 Extra parameters in docstring.
============== ============================================


Use as a pre-commit hook
--------------------------

See `pre-commit <https://github.com/pre-commit/pre-commit>`_ for instructions

Sample ``.pre-commit-config.yaml``:

.. code-block:: yaml

	 - repo: https://gitlab.com/pycqa/flake8
	   rev: 3.8.1
	   hooks:
	    - id: flake8
	      additional_dependencies: [flake8-params==0.2.0]
