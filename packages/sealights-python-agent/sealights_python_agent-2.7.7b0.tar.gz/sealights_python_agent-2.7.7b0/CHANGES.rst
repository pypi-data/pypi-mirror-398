Changes
=======

1.0.14 (2022-11-20)
--------------------
* Added support for Python 3.8, 3.9, 3.10

1.0.6 (2022-08-30)
--------------------
* Fixed "TIA Not Supported" Indicator for Test Optimization

1.0.5 (2022-07-05)
--------------------
* Dropped support for Python 2.7, 3.4 and 3.5.
* Upgraded dependencies
* Using coverage.py 6
* Bugfix: build session ids and lab ids were not encoded

0.2.247 (2022-05-19)
--------------------
* feature - tests can now run using labid only if build session id is not known. 

  Relies on at least one app that is active and configured with the same lab id.

0.2.245 (2022-03-28)
--------------------
* bugfix - test recommendations were running more tests than expected

0.2.244 (2022-02-20)
--------------------
* Added support for pytest-xdist version 2 and above

0.2.243 (2022-02-16)
--------------------
* bugfix - test recommendations API upgraded to v3

0.2.240 (2021-12-02)
--------------------
* entry log "Not upgrading agent" is now INFO

0.2.238 (2021-07-22)
--------------------
* bugfix - nose args were parsed incorrectly. First arg was ignored.

0.2.234 (2020-05-06)
--------------------
* bugfix - wrong xml coverage report when using pytest-xdist

0.2.230 (2020-03-11)
--------------------
* Handling not ready test recommendations

0.2.229 (2020-03-11)
--------------------
* Added better test recommendations error handling

0.2.228 (2020-02-22)
--------------------
* Fixed bug when running the agent after dependency update - gitdb2 - ModuleNotFoundError

0.2.219 (2019-10-30)
--------------------
* Pytest test selection support

0.2.213 (2019-10-16)
--------------------
* Python 3.7 support

0.2.201 (2019-07-14)
--------------------
* Use pytest + nose exit code

0.2.199 (2019-02-24)
--------------------
* Performance optimization
    * Added --per-test flag for pytest, nose, unittest, unit2 and run commands. default is on.

0.2.198 (2019-01-21)
--------------------
* changed default scm provider from github to null

0.2.197 (2019-01-14)
--------------------
* added --cov-report option to run command
