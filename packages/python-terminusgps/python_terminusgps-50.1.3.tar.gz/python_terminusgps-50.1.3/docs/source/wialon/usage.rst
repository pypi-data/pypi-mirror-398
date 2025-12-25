Usage
=====

To perform Wialon API operations, open a :py:obj:`~terminusgps.wialon.session.WialonSession` in a context manager, passing in your desired Wialon API token to use during the session's lifetime.

If :py:data:`token` isn't provided, the environment variable ``"WIALON_TOKEN"`` is passed instead.

.. code:: python

    from terminusgps.wialon.session import WialonSession

    # Context manager handles logging in and out of the Wialon API session
    with WialonSession(token="my_wialon_api_token") as session:
        # Perform Wialon API calls within this block
        # Session is logged out when the interpreter exits this block
        session.wialon_api.core_search_item(**{"id": 123, "flags": 0x1})

    # Will raise WialonAPIError because the session is now invalid (logged out)
    session.wialon_api.core_search_item(**{"id": 123, "flags": 0x1})

Instead of remembering every `Wialon API endpoint <https://help.wialon.com/en/api/user-guide/api-reference>`_, initialize a :py:obj:`~terminusgps.wialon.items.factory.WialonObjectFactory` in a :py:obj:`~terminusgps.wialon.session.WialonSession` to retrieve objects with convenient methods for calling the Wialon API:

.. code:: python

    from terminusgps.wialon.items import WialonObjectFactory
    from terminusgps.wialon.session import WialonSession

    with WialonSession(token="my_wialon_api_token") as session:
        # A valid Wialon API session is the only argument passed to the factory
        factory = WialonObjectFactory(session)
        # Call get() or create() on the factory to retrieve a WialonObject instance
        # The 'items_type' argument mirrors Wialon's definition of Wialon objects, e.g. 'avl_unit' for WialonUnit, 'avl_resource' for WialonResource, etc.
        unit = factory.get("avl_unit", 123)
        # Refer to your IDE or this documentation for available attributes and methods of each Wialon object type.

========
Examples
========

Creating a new Wialon user
--------------------------

.. code:: python

    from terminusgps.wialon.items import WialonObjectFactory
    from terminusgps.wialon.session import WialonSession

    with WialonSession() as session:
        factory = WialonObjectFactory(session)
        user = factory.create(
            "user",
            creator_id=12345678,
            name="New User",
            password="my_secure_password!1",
        )

.. seealso:: :py:meth:`~terminusgps.wialon.items.user.WialonUser.create` for details on creating a Wialon user.

Update an existing Wialon user's name
-------------------------------------

.. code:: python

    from terminusgps.wialon.items import WialonObjectFactory
    from terminusgps.wialon.session import WialonSession

    with WialonSession() as session:
        factory = WialonObjectFactory(session)
        user = factory.get("user", id=12345678)
        user.set_name("New User")
