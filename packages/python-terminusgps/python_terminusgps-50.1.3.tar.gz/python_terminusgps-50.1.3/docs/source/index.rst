.. python-terminusgps documentation master file, created by
   sphinx-quickstart on Wed Feb 19 10:39:57 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

python-terminusgps documentation
================================

`python-terminusgps <https://pypi.org/project/python-terminusgps>`_ is a Python package [#f1]_ that streamlines the use of web APIs for Terminus GPS developers.

`Terminus GPS <https://terminusgps.com/>`_ is an IoT software/hardware GPS monitoring company.

Commonly written and repeated Python code used in Terminus GPS Django projects is accessible from the :py:mod:`terminusgps` package, e.g. :py:obj:`~terminusgps.mixins.HtmxTemplateResponseMixin` for HTMX-enabled Django views and :py:obj:`~terminusgps.validators.validate_e164_phone_number` for validating Django model/form fields.

.. [#f1] In other programming languages, the term "library" is used to describe what Python calls a "package". Put simply, a "package" is a Python "library".

============
Installation
============

Use pip to install from `PyPI <https://pypi.org/project/python-terminusgps/>`_.

.. code:: bash

    pip install python-terminusgps

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    authorizenet/index.rst
    mixins.rst
    validators.rst
    wialon/index.rst
