Tutorial
========

This Python client communicates with the Avatar platform.

For more information about the Avatar method and process, check out our
main docs at https://docs.octopize.io

Step 1: Setup and Authentication
--------------------------------

First, import the necessary libraries and set up your authentication. If
you have the correct credentials, you can start interacting with the
Avatarization API right away.

.. code:: python

   import os
   from avatars.manager import Manager

   # Set up the URL and your credentials
   url = os.environ.get("AVATAR_BASE_API_URL", "https://www.octopize.app/api")
   username = os.environ.get("AVATAR_USERNAME")
   password = os.environ.get("AVATAR_PASSWORD")

   # Initialize the Manager and authenticate
   manager = Manager(base_url=url)
   manager.authenticate(username, password)

Make sure to replace ``username`` and ``password`` with your actual
login credentials or configure them in your environment variables.

Step 2: Uploading Your Data
---------------------------

Once authenticated, you can upload your data table to the server. In
this example, we’ll use a CSV file ``wbcd.csv``.

.. code:: python

   # Initialize the runner
   runner = manager.create_runner("test_wbcd")

   # Add the table to the runner
   runner.add_table("wbcd", "fixtures/wbcd.csv")

Here, the wbcd dataset is uploaded and is now ready for anonymization.

Step 3: Avatarization Parameters and Execution
----------------------------------------------

Next, set the **avatarization parameters** and run the avatarization
process:

.. code:: python

   # Set anonymization parameters
   runner.set_parameters("wbcd", k=10)  # Adjust k value for privacy level

   # Run the anonymization pipeline
   runner.run()

   # Get all results after running the anonymization
   results = runner.get_all_results()

Here, ``k=10`` is the number of nearest neighbors used in the `KNN-based
anonymization <https://docs.octopize.io/docs/principles/method/tabular/>`__).
You can adjust this value based on your desired privacy level. If you
want to know more about anonymization parameters, please refer
`here <https://docs.octopize.io/docs/user_guide/step_by_step/run/>`__

Step 4: Retrieve Avatarized Data
--------------------------------

Once the anonymization is complete, you can retrieve and inspect the
avatarized data:

.. code:: python

   # Print a preview of the avatarized data
   print("Avatar data:")
   print(runner.shuffled("wbcd").head())

Step 5: Retrieve Privacy and Signal Metrics
-------------------------------------------

Octopize provides privacy and signal metrics to evaluate the quality of
the synthetic data produced:

.. code:: python

   # Print privacy metrics
   for key, value in runner.privacy_metrics("wbcd")[0].items():
       print(f"{key}: {value}")

   # Print signal metrics
   for key, value in runner.signal_metrics("wbcd")[0].items():
       print(f"{key}: {value}")

Step 6: Download Avatarization Report
-------------------------------------

Once you found the optimal set of parameters for your use case, you can
download a comprehensive report of the anonymization process. This
report compiles the privacy and utility metrics obtained, providing
evidence of both anonymity and the preservation of statistical
properties.

.. code:: python

   # Download the anonymization report as a PDF
   runner.download_report('my_report.pdf')

Once you’ve followed these steps, you’re ready to explore further and
fine-tune your anonymization process!

Further Resources
-----------------

You can explore more features of the Avatar solution by following our
notebook tutorials
`here <https://python.docs.octopize.io/latest/tutorial.html>`__.
