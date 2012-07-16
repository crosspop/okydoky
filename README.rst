Okydoky
=======

Okydoky is an automated documentation builder using Sphinx_, GitHub_ and
Distribute_ (which was setuptools_).  It makes your closed Python project
to continuously build documentations, with the following assumptions:

1. Documentation is done using Sphinx.
2. Project is packaged through setuptools_ (not pip_ nor any others).
3. Source code is managed under GitHub.

**To say shortly, it's simply a ReadTheDocs.org for private use.**

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
4. Sphinx builds the documentation.
5. When users request the docs using their web browser,
   Okydoky asks the user to authenticate using GitHub OAuth.
6. If they has the authorization, Okydoky serves a built docs.

__ https://help.github.com/articles/post-receive-hooks
__ http://developer.github.com/v3/repos/contents/#get-archive-link


How to use
----------

It's an ordinary Python package.  You can install it using ``easy_install``::

    $ easy_install Okydoky

This package provides a command line script called ``okydoky``.
It's a web application and also a small web server for itself.
It takes a `config file <config>`.

Config files have to contain some required values like GitHub application
key and secret key.

You have to `create a GitHub application`__ to use Okydoky.  It's **Callback
URL** is very important.  Fill it with::

    http://<host>/auth/finalize

and replaces ``<host>`` with the domain name what you'll use.  And then,
`add a post-receive hook`__ into your GitHub repository::

    http://<host>/

If you make a config file, then run an Okydoky server using ``okydoky`` script::

    $ okydoky -H 0.0.0.0 -p 8080 yourconfig.py

Lastly, you have to make an initial auth to finish installation.
Open ``http://<host>/`` in your web browser and login with GitHub from there.

__ https://github.com/settings/applications/new
__ https://help.github.com/articles/post-receive-hooks


.. _config:

Configuration
-------------

The config file is a normal Python script.  It uses Flask's config system.
Read `Flask's docs about config files`__.

``REPOSITORY``
   The user and repository name e.g. ``'crosspop/okydoky'``.

``CLIENT_ID``
   The GitHub application's client key.

``CLIENT_SECRET``
   The GitHub application's secret key.

``SAVE_DIRECTORY``
   The path of the directory to store data.  This directory will store
   some configured data, tarballs, and built documentations.

``SECRET_KEY``
   The secret key to sign sessions.  See `Flask's docs about sessions`__ also.

__ http://flask.readthedocs.org/en/latest/config/#configuring-from-files
__ http://flask.readthedocs.org/en/latest/quickstart/#sessions
