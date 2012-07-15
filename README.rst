Okydoky
=======

Okydoky is an automated documentation builder using Sphinx_, GitHub_ and
Distribute_ (which was setuptools_).  It makes your closed Python project
to continuously build documentations, with the following assumptions:

 1. Documentation is done using Sphinx.
 2. Project is packaged through setuptools_ (not pip_ nor any others).
 3. Source code is managed under GitHub.

.. _Sphinx: http://sphinx.pocoo.org/
.. _GitHub: https://github.com/
.. _Distribute: http://pypi.python.org/pypi/distribute
.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _pip: http://www.pip-installer.org/


How it works
------------

It works in the following instructions:

 1. When new commits are pushed, GitHub triggers Okydoky `post-receive hook`__.
 2. Okydoky downloads `tarball archives`__ of pushed commits from GitHub.
 3. Tarball archive gets extracted into a temporary directory.
 4. Sphinx build the documentation.
 5. When users request the docs using their web browser,
    Okydoky asks the user to authenticate using GitHub OAuth.
 6. If they has the authorization, Okydoky serves a built docs.

__ https://help.github.com/articles/post-receive-hooks
__ http://developer.github.com/v3/repos/contents/#get-archive-link
