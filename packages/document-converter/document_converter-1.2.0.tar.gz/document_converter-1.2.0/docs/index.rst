Document Converter Documentation
==================================

Welcome to the Document Converter documentation!

The Document Converter is a comprehensive Python library for converting documents between various formats including PDF, DOCX, HTML, Markdown, and more.

Features
--------

* **Multi-format Support**: Convert between PDF, DOCX, HTML, Markdown, ODT, and TXT
* **Batch Processing**: Process multiple files in parallel
* **Template Rendering**: Custom template engine with variables, loops, and conditionals
* **Smart Caching**: Two-tier caching system (memory + disk) for fast conversions
* **Error Handling**: Comprehensive error handling with actionable suggestions
* **Transaction Safety**: Automatic rollback on conversion failures

Quick Start
-----------

Installation::

    pip install -r requirements.txt

Basic usage::

    from converter.engine import ConversionEngine
    from converter.formats.pdf_converter import PDFConverter

    engine = ConversionEngine()
    engine.register_converter('pdf', PDFConverter)
    engine.convert('document.pdf', 'document.txt')

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Documentation

   installation
   quickstart
   user_guide
   cli_reference

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/converter
   api/core
   api/formatters
   api/processors

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog

API Documentation (Modules)
----------------------------

Converter Package
~~~~~~~~~~~~~~~~~

.. automodule:: converter.engine
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: converter.batch_processor
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: converter.template_engine
   :members:
   :undoc-members:
   :show-inheritance:

Core Package
~~~~~~~~~~~~

.. automodule:: core.cache_manager
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: core.error_handler
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: core.transaction
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: core.worker_pool
   :members:
   :undoc-members:
   :show-inheritance:

Format Converters
~~~~~~~~~~~~~~~~~

.. automodule:: converter.formats.pdf_converter
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: converter.formats.docx_converter
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: converter.formats.txt_converter
   :members:
   :undoc-members:
   :show-inheritance:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
