# Deephaven Core+ Python Client

The Deephaven Core+ Python client allows you to connect to Persistent Queries
using the Core+  engine in the Deephaven Enterprise system.  You may connect
to either a new temporary Persistent Query, or one of the existing persistent queries
that you have access to on the server.

The Python client wheel is located on a Deephaven server in
`/usr/illumon/coreplus/latest/py/wheel/`, with a name of the form
`deephaven_coreplus_client-1.20231218.039-py3-none-any.whl`.  To use the wheel,
use `pip` (e.g., `pip install deephaven_coreplus_client-1.20231218.039-py3-none-any.whl`).
`pip` automatically installs dependencies referenced by the wheel, including the
underlying [`pydeephaven` client](https://deephaven.io/core/client-api/python/)
from Deephaven Community Core.

The first step in either case is to create a SessionManager, the Deephaven
installation exposes a `connection.json` file that is the simplest way to
create a session.  Simply specify the URL from your Deephaven installation.
Alternatively, you may provide a JSON string, using the `json=` named parameter.
```python
from deephaven_enterprise.client.session_manager import SessionManager

connection_info = "https://deephaven-host.int.illumon.com:8000/iris/connection.json"
session_mgr: SessionManager = SessionManager(connection_info)
```

After the session is created, you may authenticate with a password:
```python
session_mgr.password("username", "password")
```

Or using a private key:
```python
session_mgr.private_key("/path-to-private-key/priv-username.base64.txt")
```

At this point, you can then connect to an existing Persistent Query.  The session
object extends from the Deephaven Community `pydeephaven.session.Session`.  The
[Deephaven Community Python API documentation](https://deephaven.io/core/client-api/python/)
provides more information on interacting with the worker session.
```python
session = session_mgr.connect_to_persistent_query("Community Python")
qc = session.open_table("tt")
print("Table size: ", qc.size)
session.close()
```

Instead of connecting to an existing Persistent Query, you can instead make a new temporary
persistent query to host your worker.  
```python
session = session_mgr.connect_to_new_worker(name=None, heap_size_gb=1.0)

# We can run arbitrary script code
session.run_script('from deephaven import time_table\n'
                   'tt = time_table("PT1s").update("Remote=false")')

table = session.time_table(period=1000_000_000).update("Remote=true")
session.bind_table("remote", table)

session.close()
```
You can interact with the session through the Community Python API and view tables with
the Deephaven Web UI.  By default, the temporary queries are stopped and deleted after
you close the session object.
