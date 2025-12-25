User guide
==========

- `User guide <#user-guide>`__

  - `How to setup your email
    account <#how-to-setup-your-email-account>`__
  - `How to reset your password <#how-to-reset-your-password>`__
  - `How to log in to the server <#how-to-log-in-to-the-server>`__
  - `How to launch my first
    avatarization <#how-to-launch-my-first-avatarization>`__
  - `How to handle a large dataset <#how-to-handle-a-large-dataset>`__

    - `Handle large amount of rows <#handle-large-amount-of-rows>`__
    - `Handle large amount of
      dimensions <#handle-large-amount-of-dimensions>`__

  - `Understanding errors <#understanding-errors>`__
  - `Handling timeouts <#handling-timeouts>`__

    - `Asynchronous calls <#asynchronous-calls>`__

  - `How to view my last jobs <#how-to-view-my-last-jobs>`__
  - `How to launch a job from a
    yaml <#how-to-launch-a-job-from-a-yaml>`__
  - `How to change variables types <#how-to-change-variables-types>`__
  - `How to launch an avatarization using differential
    privacy <#how-to-launch-an-avatarization-using-differential-privacy>`__
  - `How to launch metrics
    independently <#how-to-launch-metrics-independently>`__
  - `How to render plots <#how-to-render-plots>`__
  - `How to create a PIA report <#how-to-create-a-pia-report>`__

How to setup your email account
-------------------------------

*This section is only needed if the use of emails to login is activated
in the global configuration.*

At the moment, you have to get in touch with your Octopize contact so
that they can create your account.

Our current email provider is AWS. They need to verify an email address
before our platform can send emails to it.

You’ll thus get an email from AWS asking you to verify your email by
clicking on a link. Once you have verified your email address by
clicking on that link, you can follow the steps in the section about
`reset password <#how-to-reset-your-password>`__.

How to reset your password
--------------------------

**NB**: This section is only available if the use of emails to login is
activated in the global configuration. It is not the case by default.

If you forgot your password or if you need to set one, first call the
forgotten_password endpoint:

.. raw:: html

   <!-- It is python, but we are setting the language to 'javascript' so that test-integration does not run this code (need mail config to run)  -->

.. code:: javascript

   from avatars.client import Manager

   manager = Manager(base_url=os.environ.get("BASE_URL"))
   manager.forgotten_password("yourmail@mail.com")

You’ll then receive an email containing a token. This token is only
valid once, and expires after 24 hours. Use it to reset your password:

.. code:: javascript

   from avatars.client import Manager

   manager = Manager(base_url=os.environ.get("BASE_URL"))
   manager.reset_password("yourmail@mail.com", "new_password", "new_password", "token-received-by-mail")

You’ll receive an email confirming your password was reset.

How to log in to the server
---------------------------

Avatar supports two authentication methods that are mutually exclusive:

Username/Password Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

   import os

   # This is the client that you'll be using for all of your requests
   from avatars.manager import Manager

   import pandas as pd
   import io

   manager = Manager(base_url=os.environ.get("AVATAR_BASE_API_URL", "https://www.octopize.app/api"))
   manager.authenticate(
       username=os.environ.get("AVATAR_USERNAME"),
       password=os.environ.get("AVATAR_PASSWORD"),
   )

API Key Authentication
~~~~~~~~~~~~~~~~~~~~~~

If you have an API key, you can use it directly without calling
``authenticate()``:

.. code:: python

   import os
   from avatars.manager import Manager

   # Authenticate using an API key
   manager = Manager(
       base_url=os.environ.get("AVATAR_BASE_API_URL", "https://www.octopize.app/api"),
       api_key=os.environ.get("AVATAR_API_KEY")
   )
   # No need to call authenticate() - the manager is ready to use

**Note:** API key and username/password authentication are mutually
exclusive. Choose one method based on your credentials.

How to launch my first avatarization
------------------------------------

When using Avatar, you will interact with an object called ``runner``.
This object serves as interface for managing the avatarization process.
With the ``runner``, you can upload your datasets, configure parameters,
execute the avatarization, and retrieve the results.

.. code:: python

   import secrets
   runner = manager.create_runner(set_name=f"test_wbcd_{secrets.token_hex(4)}")
   runner.add_table("wbcd", "fixtures/wbcd.csv") # upload the data
   runner.set_parameters("wbcd", k=15) # choose parameters
   runner.run() # execute the avatarization

How to handle a large dataset
-----------------------------

Due to the server limit, you can be limited by the number of rows and
the number of dimensions.

Handle large amount of rows
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your dataset contains a large amount of rows, it will automatically
be split into batches and each batch will be anonymized independently
from the others. It is then merged back, so that the final dataset is
the result of the anonymization of the whole dataset.

Handle large amount of dimensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The number of dimensions is the number of continuous variables plus the
number of modalities in categorical variables. The limit of dimension is
frequently reached due to a large number of modalities in one/sample of
categorical variables (high cardinality variables).

There are several solutions to bypass this limitation:

- Encode the categorical variable into a continuous variable (frequency
  encoding, target encoding, …).
- Reduce the number of modalities by grouping some into more general
  modalities. You can use the processor GroupModalities.
- Use the argument ``use_categorical_reduction``

The parameter ``use_categorical_reduction=True`` will reduce the
dimension of the categorical variable by encoding them as vectors. This
step is using the word embedding cat2vec. This solution could reduce the
utility of your dataset.

Understanding errors
--------------------

Most of your actions will have a successfull outcome. However, sometimes
there will be errors, and this section is here to explain the kinds of
errors that can happen, and how to correct them.

1. ``Timeout("The call timed out. Consider increasing the timeout with the 'timeout' parameter.")``

   You’ll encounter this error when the call is taking too long to
   complete on the server. Most of the time, this will be during job
   execution or dataset upload/download. I’ll encourage you to read up
   on the ```handling timeouts`` <#handling-timeouts>`__ section to deal
   with these kind of errors.

2. Validation errors

   Validation errors happen due to bad user input. Our error message
   rely heavily on `HTTP status
   codes <https://en.wikipedia.org/wiki/List_of_HTTP_status_codes>`__.
   In short, codes in the 400-499 range are user errors, and 500-599 are
   server errors. More on those later.

   Here we’ll cover the user errors, than you can remedy by modifying
   your parameters and trying again. The syntax of the error message
   will always be of the following form:

   .. code:: text

      Got error in HTTP request: POST https://company.octopize.app/reports. Error status 400 - privacy_metrics job status is not success: JobStatus.FAILURE

   You’ll have: - the HTTP request method (``POST``, ``GET``, etc…) -
   the endpoint that was affected (``/reports``) - the status (``400``)
   - an informational message that details the exact error that is
   happening
   (``privacy_metrics job status is not success: JobStatus.FAILURE``)

   In this particular case, the user is calling the ``/reports``
   endpoint, trying to generate a report. Generating a report needs a
   privacy metrics job to be successful to be able to show the metrics.
   However, in this case, the privacy job was in the
   ``JobStatus.FAILURE`` state. The fix is then to go look at the error
   message that the privacy job threw up, launch another privacy job
   that is successful, and launch the generation of the report with the
   new privacy job once it is successful.

3. ``JobStatus.FAILURE``

   Jobs that fail do not throw an exception. Rather, you have to inspect
   the ``JobStatus`` that is in the ``status`` property.

   .. code:: python

      job=runner.get_job(JobKind.standard)
      print(job.status)  # JobStatus.FAILURE
      print(job.exception)

   If the status is ``JobStatus.FAILURE``, the ``exception`` property
   will contain an explanation of the error. You’ll have to relaunch the
   job again with the appropriate modifications to your input.

4. Internal error

   Internal errors happen when there is an error on the server, meaning
   that we did not handle the error on our side, and something
   unexpected happened, for which we cannot give you an exact error
   message. These come with a 500 HTTP status code, and the message is
   ``internal error``. In these cases, there is not much you can do
   except trying again with different parameters, hoping to not trigger
   the error again.

   When these happen, our error monitoring software catches these and
   notifies us instantly. You can reach out to your Octopize contact
   (support@octopize.io) for more information and help for
   troubleshooting, while we investigate on our side. We’ll be hard at
   work trying to resolve the bug, and push out a new version with the
   fix.

Handling timeouts
-----------------

Asynchronous calls
~~~~~~~~~~~~~~~~~~

A lot of endpoints of the Avatar API are asynchronous, meaning that you
request something that will run in the background, and will return a
result after some time using another method, like
``runner.get_all_results`` for ``runner.run``.

The default timeout for most of the calls to the engine is not very
high, i.e. a few seconds long. You will quite quickly reach a point
where a job on the server is taking longer than that to run.

The calls being asynchronous, you don’t need to sit and wait for the job
to finish, you can simply take a break, come back after some time, and
run the method requesting the result again.

Example:

.. code:: python

   from avatars.models import JobKind
   job = runner.run(jobs_to_run = [JobKind.standard, JobKind.privacy_metrics, JobKind.signal_metrics])

   print(job)

.. code:: python

   # Take a coffee break, close the script, come back in 3 minutes

   finished_job = runner.get_all_results()

   print(finished_job)  # JobStatus.success

How to view my last jobs
------------------------

A user can view all the jobs that they created. Jobs are listed by
creation date. Attributes of the jobs such as job ID, creation date and
job status can be used to enable their management (job deletion for
example).

.. code:: python

   manager.get_last_results(count = 10) # get the last 10 jobs

Or it is also possible to see last jobs and results in the `web
application <https://www.octopize.app>`__.

How to launch a job from a yaml
-------------------------------

A user can launch a job using a YAML configuration file. If you are
using the web application to run jobs, you can download the
configuration of a job and reuse it with the Python client. This
approach is particularly helpful when iterating the anonymization
process.

Here is an example of a python script :

.. code:: python

   job_name = "from_yaml_" + secrets.token_hex(4)
   runner = manager.create_runner(job_name)
   runner.from_yaml("fixtures/yaml_from_web.yaml")
   # If needed, upload your data for each table.
   # By default, they are stored on the server for 24 hours.
   runner.upload_file("iris", data="fixtures/iris.csv")
   runner.run()

How to change variables types
-----------------------------

Sometimes, it is helpful to change the type of your variables. For
instance, a numeric variable might only contain a few unique values,
making it more appropriate to treat it as a categorical variable. This
can optimize utility performance in your avatarization.

.. code:: python

   from avatar_yaml.models.schema import ColumnType
   runner.add_table("wbcd", data="fixtures/wbcd.csv", types={"Clump_Thickness": ColumnType.CATEGORY})

or either use pandas to do it :

.. code:: python

   df = pd.read_csv("fixtures/wbcd.csv")
   df["Clump_Thickness"]=df["Clump_Thickness"].astype("string")
   runner.add_table("wbcd", data=df)

How to launch an avatarization using differential privacy
---------------------------------------------------------

You can use differential privacy in the avatarization pipeline.

.. code:: python

   runner.set_parameters("wbcd", dp_epsilon=10)

How to launch metrics independently
-----------------------------------

Data quality evaluation can be performed independently of the
anonymization process by running only the metrics jobs on both the
original and the anonymized datasets. For an accurate assessment, the
data should not be shuffled.

For more details about our metrics, refer to our `public
documentation <https://docs.octopize.io/docs/principles/metrics/>`__.

.. code:: python

   job_name = "only_metrics" + secrets.token_hex(4)
   runner = manager.create_runner(job_name)
   # Original and anonymized data should be in the same order
   runner.add_table("iris", data="fixtures/iris.csv", avatar_data="fixtures/iris_avatarized.csv")
   runner.set_parameters("iris", k=10)
   runner.run(jobs_to_run=[JobKind.privacy_metrics, JobKind.signal_metrics])

How to render plots
-------------------

You can generate plots to assess how well utility is preserved during
the avatarization process, using four levels of analysis:

- **Univariate:** Compare distributions with ``PlotKind.DISTRIBUTION``
  or review mean and standard deviation summaries for the first 10
  columns using ``PlotKind.AGGREGATE_STATS``.
- **Bivariate:** Examine correlations with ``PlotKind.CORRELATION`` and
  analyze correlation differences with
  ``PlotKind.CORRELATION_DIFFERENCE``.
- **Multivariate:** Visualize data projections using
  ``PlotKind.PROJECTION_2D`` and ``PlotKind.PROJECTION_3D``.
- **Data structure:** Explore variable contributions within the model
  using ``PlotKind.CONTRIBUTION``.

Visualizations are a great way to fine tuned the parameters and
understand your results.

To render a plot, simply use:

.. code:: python

   runner.render_plot("iris", PlotKind.PROJECTION_3D)

If you encounter issues displaying plots directly in your notebook (for
example, in VS Code), or if you prefer to download the plot as an HTML
file, you can use the ``open_in_browser=True`` parameter. This will save
the plot as an HTML file and open it in your default web browser:

.. code:: python

   runner.render_plot("iris", PlotKind.PROJECTION_3D, open_in_browser=True)

How to create a PIA report
--------------------------

When running the avatarization, you can **generate 2 reports**: a
technical report and a PIA (Privacy Impact Assessment) report. The PIA
report helps determine whether the residual risk is compatible with the
intended use of the data and with its level of sensitivity. While the
technical evaluation quantifies the re-identification risk associated
with potential attacks, the risk analysis report evaluates the
likelihood of such attacks occurring and the resources an adversary
would need to carry them out.

The **PIA report can be customized** with information about your dataset
and the avatarization context:

- `SensitivityLevel <https://octopize.github.io/avatar-python/main/avatar_yaml.html#avatar_yaml.models.avatar_metadata.SensitivityLevel>`__:
  indicates the sensitivity level of the data being processed. The
  sensitivity increases as the data are or are not personal, sensitive…

- `DataType <https://octopize.github.io/avatar-python/main/avatar_yaml.html#avatar_yaml.models.avatar_metadata.DataType>`__
  : indicates the type of data being processed (e.g., health data,
  financial data, etc.). Different data types may have different privacy
  implications and regulatory requirements.

- `DataSubject <https://octopize.github.io/avatar-python/main/avatar_yaml.html#avatar_yaml.models.avatar_metadata.DataSubject>`__
  : identifies the individual or group to whom the data relates, helping
  to contextualize privacy considerations.

- `DataRecipient <https://octopize.github.io/avatar-python/main/avatar_yaml.html#avatar_yaml.models.avatar_metadata.DataRecipient>`__
  : describes the intended recipients of the data, which can influence
  the assessment of privacy risks and necessary safeguards.

You can set these parameters when creating the runner:

.. code:: python

   from avatar_yaml.models.avatar_metadata import SensitivityLevel, DataType, DataSubject, DataRecipient

   runner = manager.create_runner(set_name="test_pia_report",
           pia_data_recipient = DataRecipient.OPENDATA,
           pia_data_type = DataType.HEALTH,
           pia_data_subject = DataSubject.PATIENTS,
           pia_sensitivity_level = SensitivityLevel.HIGH,)

You can then download the PIA report as a DOCX file:

.. code:: python

   from avatar_yaml.models.parameters import ReportType
   runner.download_report("pia_report.docx", report_type=ReportType.PIA)
