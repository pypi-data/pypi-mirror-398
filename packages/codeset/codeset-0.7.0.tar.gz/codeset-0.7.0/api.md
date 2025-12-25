# Health

Types:

```python
from codeset.types import HealthCheckResponse
```

Methods:

- <code title="get /health">client.health.<a href="./src/codeset/resources/health.py">check</a>() -> <a href="./src/codeset/types/health_check_response.py">HealthCheckResponse</a></code>

# Samples

Types:

```python
from codeset.types import SampleListResponse
```

Methods:

- <code title="get /samples">client.samples.<a href="./src/codeset/resources/samples.py">list</a>(\*\*<a href="src/codeset/types/sample_list_params.py">params</a>) -> <a href="./src/codeset/types/sample_list_response.py">SampleListResponse</a></code>
- <code title="get /samples/{dataset}/{sample_id}/download">client.samples.<a href="./src/codeset/resources/samples.py">download</a>(sample_id, \*, dataset, \*\*<a href="src/codeset/types/sample_download_params.py">params</a>) -> object</code>

# Datasets

Types:

```python
from codeset.types import DatasetListResponse
```

Methods:

- <code title="get /datasets">client.datasets.<a href="./src/codeset/resources/datasets.py">list</a>() -> <a href="./src/codeset/types/dataset_list_response.py">DatasetListResponse</a></code>

# Sessions

Types:

```python
from codeset.types import (
    ContainerInfo,
    ErrorInfo,
    Session,
    SessionStatus,
    SessionCreateResponse,
    SessionListResponse,
    SessionCloseResponse,
    SessionExecuteCommandResponse,
    SessionStrReplaceResponse,
)
```

Methods:

- <code title="post /sessions">client.sessions.<a href="./src/codeset/resources/sessions/sessions.py">create</a>(\*\*<a href="src/codeset/types/session_create_params.py">params</a>) -> <a href="./src/codeset/types/session_create_response.py">SessionCreateResponse</a></code>
- <code title="get /sessions/{session_id}">client.sessions.<a href="./src/codeset/resources/sessions/sessions.py">retrieve</a>(session_id) -> <a href="./src/codeset/types/session.py">Session</a></code>
- <code title="get /sessions">client.sessions.<a href="./src/codeset/resources/sessions/sessions.py">list</a>() -> <a href="./src/codeset/types/session_list_response.py">SessionListResponse</a></code>
- <code title="delete /sessions/{session_id}">client.sessions.<a href="./src/codeset/resources/sessions/sessions.py">close</a>(session_id) -> <a href="./src/codeset/types/session_close_response.py">SessionCloseResponse</a></code>
- <code title="post /sessions/{session_id}/exec">client.sessions.<a href="./src/codeset/resources/sessions/sessions.py">execute_command</a>(session_id, \*\*<a href="src/codeset/types/session_execute_command_params.py">params</a>) -> <a href="./src/codeset/types/session_execute_command_response.py">SessionExecuteCommandResponse</a></code>
- <code title="post /sessions/{session_id}/str_replace">client.sessions.<a href="./src/codeset/resources/sessions/sessions.py">str_replace</a>(session_id, \*\*<a href="src/codeset/types/session_str_replace_params.py">params</a>) -> <a href="./src/codeset/types/session_str_replace_response.py">SessionStrReplaceResponse</a></code>

## Verify

Types:

```python
from codeset.types.sessions import JobStatus, VerifyStartResponse, VerifyStatusResponse
```

Methods:

- <code title="post /sessions/{session_id}/verify">client.sessions.verify.<a href="./src/codeset/resources/sessions/verify.py">start</a>(session_id) -> <a href="./src/codeset/types/sessions/verify_start_response.py">VerifyStartResponse</a></code>
- <code title="get /sessions/{session_id}/verify/{job_id}">client.sessions.verify.<a href="./src/codeset/resources/sessions/verify.py">status</a>(job_id, \*, session_id) -> <a href="./src/codeset/types/sessions/verify_status_response.py">VerifyStatusResponse</a></code>
