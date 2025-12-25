Configuration
=============

This guide explains how to configure the Avatar Python client to connect to different server environments.

Server Connection Basics
-------------------------

The Avatar Python client needs to know which server to connect to. By default, it connects to Octopize's **SaaS server** at ``https://www.octopize.app``, but you can configure it to connect to your own on-premise installation.

Default Configuration (SaaS Server)
------------------------------------

If you're using Octopize's cloud service, you don't need to provide any URL configuration:

.. code-block:: python

   from avatars import Manager

   # Connects to https://www.octopize.app by default
   manager = Manager()
   manager.authenticate(username="your_username", password="your_password")

On-Premise Server Configuration
--------------------------------

If you're using an on-premise installation, you need to tell the client where your server is located:

.. code-block:: python

   from avatars import Manager

   # Connect to your on-premise server
   manager = Manager(base_url="https://avatar.yourcompany.com")
   manager.authenticate(username="your_username", password="your_password")

The ``base_url`` parameter should be the **base URL** of your Avatar server (without the ``/api`` suffix).

.. note::
   **For users migrating from earlier versions:** The older pattern of specifying
   ``base_url="https://avatar.yourcompany.com/api"`` with the ``/api`` suffix still
   works for backward compatibility, but the recommended approach is to use the base
   URL without the suffix.

Authentication Methods
----------------------

Username and Password
^^^^^^^^^^^^^^^^^^^^^

The traditional authentication method uses username and password:

.. code-block:: python

   from avatars import Manager

   manager = Manager(base_url="https://avatar.yourcompany.com")
   manager.authenticate(username="user", password="pass")

API Key Authentication
^^^^^^^^^^^^^^^^^^^^^^

You can also authenticate using an API key, which is particularly useful for automated scripts and CI/CD pipelines:

.. code-block:: python

   from avatars import Manager

   manager = Manager(
       base_url="https://avatar.yourcompany.com",
       api_key="your-api-key-here"
   )
   # No need to call authenticate() - you're already authenticated!

.. important::
   When using API key authentication, **do not call** ``authenticate()``. The API key
   is active immediately upon initialization. Attempting to call ``authenticate()`` with
   an API key will raise an error.

Advanced Configuration Options
-------------------------------

SSL Certificate Verification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For on-premise deployments without dedicated SSL certificates, you can disable SSL verification:

.. code-block:: python

   from avatars import Manager, ApiClient

   manager = Manager(
       api_client=ApiClient(
           base_url="https://avatar.yourcompany.com",
           should_verify_ssl=False
       )
   )

.. warning::
   Disabling SSL verification should only be done in trusted environments.
   It reduces security by making your connection vulnerable to man-in-the-middle attacks.

Using ClientConfig
^^^^^^^^^^^^^^^^^^

For more control over all configuration options, you can use a ``ClientConfig`` object:

.. code-block:: python

   from avatars import Manager
   from avatars.client_config import ClientConfig

   config = ClientConfig(
       base_url="https://avatar.yourcompany.com",
       should_verify_ssl=False,
       timeout=120  # Custom timeout in seconds
   )

   manager = Manager(config=config)

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

You can also configure the client using environment variables with the ``AVATAR_`` prefix:

.. code-block:: bash

   export AVATAR_BASE_URL="https://avatar.yourcompany.com"
   export AVATAR_API_KEY="your-api-key-here"
   export AVATAR_SHOULD_VERIFY_SSL="false"
   export AVATAR_TIMEOUT="120"

Then in Python:

.. code-block:: python

   from avatars import Manager

   # Configuration is automatically loaded from environment variables
   manager = Manager()

Configuration Priority
^^^^^^^^^^^^^^^^^^^^^^

When multiple configuration sources are provided, they follow this priority order (highest to lowest):

1. Parameters passed directly to ``Manager()`` constructor (``base_url``, ``api_key``, etc.)
2. ``ClientConfig`` object passed to ``Manager()``
3. Environment variables with ``AVATAR_`` prefix
4. Default values (SaaS server)
