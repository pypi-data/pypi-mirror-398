Runner
======

The ``Runner`` orchestrates an avatarization workflow: data upload, parameter
configuration, job submission, status polling, and result retrieval.
It encapsulates a configuration object (``avatar_yaml.Config``) that mirrors the
YAML structure used by batch operations.

Responsibilities
----------------

* Collect and upload source (and optional avatar) tables (``add_table``)
* Advise or customize parameters (``advise_parameters`` / ``set_parameters``)
* Create links between tables (only needed for multitable) (``add_link``)
* Launch jobs individually or end-to-end (``run`` and specialized methods)
* Download results (``get_all_results`` and specialized methods)

Design notes
------------

The ``Runner`` is stateful: it remembers tables, generated parameters, created jobs and
download results. You usually create one per anonymization project ("set") via
``manager.create_runner(set_name=...)``. Internally it delegates network calls to the
shared authenticated ``ApiClient``.

Minimal flow
------------

.. code-block:: python

   runner = manager.create_runner("demo")
   runner.add_table("wbcd", "fixtures/wbcd.csv")
   runner.advise_parameters()         # optional
   runner.set_parameters("wbcd", k=15)
   runner.run()                       # runs the full pipeline
   runner.get_all_results()          # downloads all results

Detailed reference
------------------

.. automodule:: avatars.runner
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
