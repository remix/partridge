========================
Publishing a new release
========================

Based on https://packaging.python.org/en/latest/tutorials/packaging-projects

Prerequisites
~~~~~~~~~~~~~

* Update ``HISTORY.rst``
* Tag Git release, e.g.::

    $ git tag v1.2.3
    $ git push --tags

* If needed, create an account on TestPyPI: https://test.pypi.org/account/register/
* Generate a test API token: https://test.pypi.org/manage/account/token/
* Generate a real API token: https://pypi.org/manage/account/token/
* Install deployment tools::

    $ pip install --upgrade build twine

Process
~~~~~~~

* Build the package::

    $ python -m build

* Check package validity (optional)::

    $ python -m twine check dist/*

* Upload the package to TestPyPI (username is ``__token__``, password is your API token)::

    $ python -m twine upload --repository testpypi dist/*

* Verify the test release can be installed::

    $ python -m venv testing
    $ testing/bin/pip install --index-url https://test.pypi.org/simple/ --no-deps partridge==<VERSION>

  Note: we use ``--no-deps`` because not all dependencies are present in
  TestPyPI. For more comprehensive testing, manually install deps from the real
  PyPI.

* Upload the package to PyPI (username is ``__token__``, password is your API token)::

    $ python -m twine upload dist/*
