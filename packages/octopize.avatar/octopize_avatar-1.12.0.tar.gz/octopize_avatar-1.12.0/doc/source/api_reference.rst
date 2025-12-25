Detailed doc
============

General approach
----------------

This section gives a high-level mental model for using the Python client.
You typically interact with three abstraction layers:

1. Manager (high-level convenience)
   - Authenticate once and keep session state.
   - Create workflow objects (``Runner``) easily.
   - Quick helpers: recent jobs/results, health checks.
2. Runner (workflow orchestration)
   - Upload data / build YAML config programmatically.
   - Set or advise parameters and launch jobs.
   - Download and access structured results.
3. ApiClient (low-level resource facade)
   - Exposes raw resource clients (jobs, datasets, results, users, etc.).
   - Lets you tweak HTTP layer (timeouts, SSL verification, custom client) and call endpoints directly.

Pick the highest level that covers your use case. Drop down only when you need finer control.

Typical flow
^^^^^^^^^^^^

.. code-block:: python

   from avatars import Manager
   manager = Manager()
   manager.authenticate("user", "pass")
   runner = manager.create_runner("demo_set")
   runner.add_table("wbcd", "fixtures/wbcd.csv")
   runner.advise_parameters()        # optional server guidance
   runner.set_parameters("wbcd", k=15)  # or customize
   runner.run()                      # launch avatarization
   results = manager.get_last_results()

Quick reference
^^^^^^^^^^^^^^^

Use the dedicated pages below for complete APIs:

* :doc:`Manager <manager>` – high-level helpers & session utilities.
* :doc:`Runner <runner>` – workflow orchestration.
* :doc:`ApiClient <apiclient>` – raw resource access & HTTP configuration.

Choosing an abstraction
^^^^^^^^^^^^^^^^^^^^^^^

Pick the highest level that satisfies your need; drop down only when necessary:

Simple run
   :doc:`Manager <manager>` + :doc:`Runner <runner>` — Minimal code; handles auth & orchestration
Batch scripts
   :doc:`Runner <runner>` — Explicit workflow control & state reuse
Custom HTTP logic
   :doc:`ApiClient <apiclient>` — Direct access; tweak retries/timeouts
Tooling / SDK dev
   :doc:`ApiClient <apiclient>` + models — Stable surface for wrapping/extensions
Debug / inspection
   :doc:`Runner <runner>` + results helpers — Organized URLs & metrics access

If unsure, start with ``Manager`` → ``Runner``; move lower only if you hit limitations (timeouts, advanced filtering, custom retry/backoff logic, etc.).


Table of contents
-----------------
.. toctree::
   :maxdepth: 1

   Manager <manager>
   Runner <runner>
   ApiClient <apiclient>
   Models <models>
   Constants <constants>
   Processors <processors>
