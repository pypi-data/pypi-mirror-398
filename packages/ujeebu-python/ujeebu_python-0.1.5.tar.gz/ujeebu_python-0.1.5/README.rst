=====================
Ujeebu API Python SDK
=====================


.. image:: https://img.shields.io/pypi/v/ujeebu_python.svg
        :target: https://pypi.python.org/pypi/ujeebu_python

.. image:: https://img.shields.io/pypi/pyversions/ujeebu_python.svg
        :target: https://pypi.python.org/pypi/ujeebu_python

.. image:: https://readthedocs.org/projects/ujeebu-python/badge/?version=latest
        :target: https://ujeebu-python.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Ujeebu_ is a set of powerful APIs for Web data scraping and automatic content extraction.
This SDK provides an easy-to-use interface for interacting with Ujeebu API using Python.


Installation
------------

Install using pip::

    pip install ujeebu_python


Quick Start
-----------

.. code-block:: python

    from ujeebu_python import UjeebuClient
    import json

    ujeebu = UjeebuClient(api_key="__YOUR-API-KEY__")
    url = "https://ujeebu.com/blog/scraping-javascript-heavy-pages-using-puppeteer/"
    response = ujeebu.extract(url=url)

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result['article'], indent=2))
    else:
        print("Error:", response.json())


Features
--------

* **Scrape API**: Scrape any web page with JavaScript rendering support
* **Extract API**: Automatically extract article content from web pages
* **SERP API**: Search Google and get structured results
* **Helper Methods**: Convenient methods for common tasks (screenshots, PDFs, HTML)

For full documentation, visit https://ujeebu.com/docs


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _Ujeebu: https://ujeebu.com
