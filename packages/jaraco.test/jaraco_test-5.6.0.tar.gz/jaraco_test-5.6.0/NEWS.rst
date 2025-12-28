v5.6.0
======

Features
--------

- Add ensure_git fixture.


v5.5.1
======

Bugfixes
--------

- Added `__future__.annotations`. (#10)


v5.5.0
======

Features
--------

- Complete annotations and add ``py.typed`` marker -- by :user:`Avasam` (#8)


v5.4.0
======

Features
--------

- Added cpython module with support for loading functions across moves.


v5.3.0
======

#5: Plugin now honors the ``network`` marker convention for
tagging network-required tests.

v5.2.0
======

Added pytest fixture ``needs_internet`` to skip tests that require
HTTP connectivity.

v5.1.0
======

Added ``property_error`` function for testing a property error.

v5.0.0
======

Moved enabler to
`pytest-enabler <https://pypi.org/project/pytest-enabler>`_.

v4.0.1
======

#2: In enabler, remove third-party packages from sys.modules
to avoid spurious non-coverage of lines covered at import time.

v4.0.0
======

Remove pytest plugin added in 3.0.

v3.2.0
======

Add a hack around pytest-cov to enable support for configuring it
in the enabler plugin.

v3.1.1
======

Changed enabler plugin to run at ``pytest_load_initial_conftests``
hook.

v3.1.0
======

#1: Added the "enabler" plugin with support for adding
arbitrary options for plugins that are present. For
pytest-dev/pytest#7675.

v3.0.0
======

Removed remaining modules.

Added pytest plugin for pytest-dev/pytest#7675.

2.3
===

Deprecated the last module in this package (http) in
favor of the
`responses <https://pypi.org/project/responses>`_
project.

2.2
===

Moved hosting to Github.

2.1
===

Moved services module to ``jaraco.test.services`` and
``jaraco.mongodb.service``.

2.0.5
=====

Extend timeout for MongoDB mongod to listen on the port from
one second to three seconds, preventing spurious failures
on slower systems.

2.0.2
=====

Replace lingering reference to removed socket_test module.

2.0.1
=====

Fix issue in MongoDB finder where MONGODB_HOME wasn't honored.

2.0
===

Removed jaraco.test.socket_test. Use portend instead.

Use setuptools_scm for version generation.

1.9
===

Improved MongoDBFinder to locate MongoDB in new canonical
locations used by the MongoDB Windows Installer.
