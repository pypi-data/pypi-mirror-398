:hide-toc: true

.. CodeGrade Python API documentation master file, created by
   sphinx-quickstart on Thu Oct 28 14:29:38 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

CodeGrade API
=============


.. First display signle files, which have higher priority. These
   are the for example the clients, which are the entry point for someone
   starting to work on a project using CodeGrade's API
   After this display the indexed files in subfolders

.. toctree::
   :hidden:
   :caption: Documentation


   clients/AuthenticatedClient.rst
   utils.rst

   models/index
   services/index
   maybe/index


.. toctree::
   :maxdepth: 1
   :hidden:
   :glob:
   :caption: Examples


   examples/*


.. mdinclude:: readme/Introduction.md

The packages is made of three main elements: an :class:`.AuthenticatedClient`,
i.e. the authenticated entry-point used to query the server for information,
the :ref:`Services <services>`, which expose the API to query the server and
get, patch, remove, etc.. the data, and :ref:`Models <models>`, which are
the representations of the data received and sent to the server.

Alongside these elements, we provide documentation for some ``utils`` which
make working with these elements easier, and :class:`.Maybe`, a class used to
represent data that is not guaranteed to be present in the models as it is
optional data.


Installation
------------


.. mdinclude:: readme/Installation.md


Where to start
--------------

The CodeGrade API relies entirely on accessing information through an authenticated
client, which can be easily obtained with one of the following methods:

.. currentmodule:: codegrade

.. autofunction:: codegrade.login

.. autofunction:: codegrade.login_from_cli

These are just aliases for :class:`.AuthenticatedClient`'s methods. We suggest
to take a look at its documentation for further usage of the API.


Examples
--------


Following are some basic examples of the API. For more specific and advanced
examples refer to these:

* `Export Feedback <examples/export_feedback.html>`_
* `Export Student Progress <examples/export_progress.html>`_
* `CodeGrade and GitHub automation <examples/github_integration.html>`_

.. note::

   The following examples assume you know the ID of the objects you want to
   query. Please, refer to the aforementioned examples for how you could get
   the same information without knowing the IDs beforehand.

Get a course
^^^^^^^^^^^^

.. code-block:: python

   with codegrade.login_from_cli() as client:
      course = client.course.get(course_id)

Get all assignments in a course
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   with codegrade.login_from_cli() as client:
      assignemnts = client.course.get(course_id).assignments

Get all users in a course
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   with codegrade.login_from_cli() as client:
      users = client.course.get_all_users(course_id)

Get all submissions in an assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   with codegrade.login_from_cli() as client:
      submissions = client.assignment.get_all_submissions(assignment_id)


Backwards compatibility
-----------------------

.. mdinclude:: readme/Backwards_compatibility.md


Supported python versions
-------------------------

.. mdinclude:: readme/Supported_python_versions.md


License
-------

.. mdinclude:: readme/License.md
