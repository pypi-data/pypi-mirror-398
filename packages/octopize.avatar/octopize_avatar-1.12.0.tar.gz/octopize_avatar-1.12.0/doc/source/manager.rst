Manager
=======

The Manager is the high-level entry point for most users.
It wraps an authenticated ``ApiClient`` and offers helper methods
that reduce boilerplate when running avatarizations.

Why use the Manager?
--------------------

* Single place to authenticate.
* Shortcuts to create a ``Runner`` and load YAML configs.
* Convenience helpers to inspect recent jobs / results.

.. seealso::
   For detailed information about configuring the Manager to connect to different
   servers (SaaS vs on-premise), authentication methods, and advanced configuration
   options, see :doc:`configuration`.

Quick example
-------------

**Using username/password authentication:**

.. code-block:: python

   from avatars import Manager
   manager = Manager()
   manager.authenticate(username="user", password="pass")
   runner = manager.create_runner(set_name="demo")
   runner.add_table("wbcd", "fixtures/wbcd.csv")
   runner.set_parameters("wbcd", k=15)
   runner.run()

Detailed reference
------------------

.. automodule:: avatars.manager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
