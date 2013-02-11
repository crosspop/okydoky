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

It's an ordinary Python package.  You can install it using ``easy_install``:

.. code-block:: console

   $ easy_install Okydoky

This package provides a command line script called ``okydoky``.
It's a web application and also a small web server for itself.
It takes a `config file <config>`.

Config files have to contain some required values like GitHub application
key and secret key.

You have to `create a GitHub application`__ to use Okydoky.  Its **Callback
URL** is very important.  Fill it with::

    http://<host>/auth/finalize

and replaces ``<host>`` with the domain name what you'll use.  And then,
`add a post-receive hook`__ into your GitHub repository::

    http://<host>/

If you make a config file, then run an Okydoky server using ``okydoky`` script:

.. code-block:: console

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

``RECREATE_VIRTUALENV``
   Creates the new virtualenv for every build.  It's a lot slower than
   not using this, but instead makes free from side effects related
   ``site-packages``.

   Set any nonzero value e.g. ``1``, ``True`` if you want to
   recreate the virtualenv everytime.

``COMPLETE_HOOK``
   The callback function (any callable object) which is called when
   the build has complete.  It's called for each commit, even if it
   failed.

   It takes three positional parameters:

   1. (``basestring``) Commit hash
   2. (``basestring``) Permalink of the docs.  It might be 404
      if the build failed.
   3. (``tuple``) Triple ``sys.exc_info()`` function returns
      if the build failed.  ``None`` if the build succeeded.

   You can utilize the last argument for printing the error traceback
   e.g.:

   .. code-block:: python

      import traceback

      def COMPLETE_HOOK(commit_id, permalink, exc_info):
          if exc_info is not None:
              traceback.print_exception(*exc_info)

.. workaround a bug of vim syntax highlight*

__ http://flask.readthedocs.org/en/latest/config/#configuring-from-files
__ http://flask.readthedocs.org/en/latest/quickstart/#sessions


Special environment variable: ``OKYDOKY``
-----------------------------------------

Okydoky sets the special environment variable named ``OKYDOKY`` during
its build process.  You can determine whether it's built by Okydoky or not.

For example, you can add some additional requirements only for Okydoky build
in ``setup.py`` script:

.. code-block:: python

   import os
   from setuptools import setup

   install_requires = ['Flask', 'SQLAlchemy']

   if os.environ.get('OKYDOKY'):
       install_requires.extend(['Sphinx', 'sphinxcontrib-httpdomain'])

   setup(
       name='YourProject',
       install_requires=install_requires
   )

Or ``conf.py`` for Sphinx:

.. code-block:: python

   import os

   if os.environ.get('OKYDOKY'):
       html_theme = 'nature'
   else:
       html_theme = 'default'


Open source
-----------

Okydoky is written by `Hong Minhee`__ for Crosspop.  It's distributed under
`MIT license`__, and the source code can be found in the `GitHub repository`__.
Check out:

.. code-block:: console

   $ git clone git://github.com/crosspop/okydoky.git

__ http://dahlia.kr/
__ http://minhee.mit-license.org/
__ https://github.com/crosspop/okydoky


Changelog
---------

Version 0.9.6
'''''''''''''

Released on February 12, 2013.

- Added ``RECREATE_VIRTUALENV`` option which makes it to create
  the virtualenv for each build.
- Added ``COMPLETE_HOOK`` option.
- Try recreating the virtualenv if the build has failed first.
- Added ``--proxy-fix`` option for HTTP reverse proxies.
- Added ``--force-https`` option.
- Don't use github-distutils_ anymore to prevent several headaches related
  packaging and distribution.

.. _github-distutils: https://github.com/dahlia/github-distutils


Version 0.9.5
'''''''''''''

Released on September 16, 2012.

- GitHub forced ``state`` for OAuth.  Follow that.


Version 0.9.4
'''''''''''''

Released on September 3, 2012.

- Use ``--upgrade`` option for ``setup.py develop`` command.
  This prevents version conflicts of dependencies.
- Build logs are left in the ``build.txt`` file.


Version 0.9.3
'''''''''''''

Released on July 18, 2012.

- Now the index page shows the list of refs.
- Now Okydoky sets ``OKYDOKY=1`` environment variable during its build
  process.  [`#5`_]
- Add ``/head`` special ref url.
- Fixed a bug that the head is not set to the latest commit.

.. _#5: https://github.com/crosspop/okydoky/issues/5


Version 0.9.2
'''''''''''''

Released on July 17, 2012.  Hotfix of 0.9.1.

- Fixed a security bug: now users must have an authorization for the repository.
  [`#4`_]

.. _#4: https://github.com/crosspop/okydoky/issues/4


Version 0.9.1
'''''''''''''

Released on July 17, 2012.  Hotfix of 0.9.0.

- Made ``okydoky`` package empty and moved things to ``okydoky.app`` module.


Version 0.9.0
'''''''''''''

Released on July 17, 2012.

- Initial version.
