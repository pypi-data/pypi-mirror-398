avatars
=======

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   Installation <installation>
   Configuration <configuration>
   Tutorial <tutorial>
   User Guide <user_guide>
   Detailed doc <api_reference>
   Changelog <changelog>

.. toctree::
   :hidden:

   Notebooks tutorial <https://github.com/octopize/avatar-python/tree/main/notebooks>
   Main documentation site <https://docs.octopize.io/>
   Web application <https://www.octopize.app>
   Create an account for free<https://content.octopize.io/free-trial>



Resources
-----------------

Our main docs are at https://docs.octopize.io/

Our web application is at https://www.octopize.app

Our Notebooks tutorials are at https://github.com/octopize/avatar-python/tree/main/notebooks

To contact us, reach out at support@octopize.io


Overview
--------

The Python client is structured in layered components so you can choose the
highest level of abstraction that fits your workflow and drop down only when
you need more control.

Core layers
^^^^^^^^^^^

1. Manager (high-level convenience)
   A thin facade you instantiate first. It authenticates the user, creates
   workflow ``Runner`` objects, and offers shortcuts to recent jobs, results,
   and health checks. For most day‑to‑day usage you only interact with the
   ``Manager`` plus a ``Runner``.

2. Runner (workflow orchestration)
   Encapsulates an avatarization "set": uploading tables, linking them,
   advising or setting parameters, executing jobs, and gathering results.
   It maintains in‑memory state (tables, jobs, results URLs) and uses the
   authenticated API session carried by the Manager.

3. ApiClient (low-level resource interface)
   Handles HTTP calls, authentication tokens, retries/timeouts and exposes
   resource clients (``jobs``, ``datasets``, ``results``, ``users``, etc.). Use
   it directly when you need fine‑grained control beyond what ``Manager`` / ``Runner`` provide.

Supporting pieces
^^^^^^^^^^^^^^^^^

* Pydantic models – Strongly typed request/response schemas ensuring your
  inputs are validated before they reach the server.
* avatar_yaml configuration – A Python representation of the YAML structure
  used to describe avatarization parameters (tables, links, privacy / signal
  settings). The ``Runner`` builds and manipulates a ``avatar_yaml.Config`` under
  the hood; you can also load from / export to YAML directly.
* Processors – Pre / post processing helpers that can be referenced in configs
  to transform data prior to or after avatarization.

Typical usage pattern
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from avatars import Manager
   manager = Manager()
   manager.authenticate("user", "pass")
   runner = manager.create_runner("demo_set")
   runner.add_table("wbcd", "fixtures/wbcd.csv")
   runner.advise_parameters()          # optional server guidance
   runner.set_parameters("wbcd", k=15) # fine‑tune
   runner.run()                        # launch avatarization
   runner.shuffled("wbcd")        # access result table

Where to go next
^^^^^^^^^^^^^^^^

* Start with Installation / Tutorial for a first run.
* You can download other tutorials here: https://github.com/octopize/avatar-python/tree/main/notebooks
* See Detailed doc for the conceptual overview and the full API surface.
* Consult dedicated pages for ``Manager``, ``Runner`` and ``ApiClient`` when you
  need deeper control.
