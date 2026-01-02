======================
sealights-python-agent
======================

The sealights-python-agent package integrates with the Sealights Quality Intelligence Platform.


****************
Language Support
****************
* Python 3.7
* Python 3.8
* Python 3.9
* Python 3.10
* Python 3.11
* Python 3.12


************
Installation
************
.. code-block::

    $ pip install sealights-python-agent


*****
Usage
*****

1. **Generating a session ID**

    .. code-block::

        $ sl-python config --appname myApp --branchname master --buildname 1 --exclude "*venv*"

2. **Scanning a build**

    .. code-block::

        $ sl-python build

3. **Running your tests**

    3.1 Running tests with **unittest**

    .. code-block::

        $ sl-python unittest --teststage "Unit Tests" <your args...>

    3.2 Running tests with **pytest**

    .. code-block::

        $ sl-python pytest --teststage "Unit Tests" <your args...>

    3.3 Running tests with **unittest2**

    .. code-block::

        $ sl-python unit2 --teststage "Unit Tests" <your args...>
