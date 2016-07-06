How-to Contribute
=================

Send patches
------------

If you do not have push rights on the repository, please open a pull request
with your commits for review. We do not *merge* pull requests to avoid merge
commits in git history. Once reviewed, commits are applied manually (keeping
authors) on HEAD to keep a flat history.

Commits
-------

We follow standard git commit guidelines:

https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#Commit-Guidelines

In a few words:

* 1st line summary max. 50 chars
* unless really obvious, a blank line and a detailled description wrap to 72
  chars focused on what and why instead of how (how must be wisely explained in
  codes comments or in documentation)
* only one logical changeset per commit
* git diff --check error free

Code style
----------

NEOS is written in Python, the code must respect the pep8.

Unit tests
----------

There is a collection of unit tests in `tests/` directory. Tests are not
included in neos packages because `neos.__init__` indirectly imports external
packages (such as pyslurm) that we do not want to depend on to run the tests.
Those external libraires are mocked in the unit tests.

To run the tests with nose, just run the following command:

```
nosetests tests
```

To get the code coverage as well, add those parameters:

```
nosetests tests --with-coverage --cover-package=neos
```

All bug fixes must be covered with unit tests, to make sure the bug case is
properly handled. It is also better to cover new features as well.
