# Dataframer

Types:

```python
from dataframer.types import (
    SampleClassification,
    SpecVersion,
    DataframerCheckHealthResponse,
    DataframerListHistoricalRunsResponse,
    DataframerListModelsResponse,
)
```

Methods:

- <code title="get /api/dataframer/health/">client.dataframer.<a href="./src/dataframer/resources/dataframer/dataframer.py">check_health</a>() -> <a href="./src/dataframer/types/dataframer_check_health_response.py">DataframerCheckHealthResponse</a></code>
- <code title="get /api/dataframer/historical-runs/">client.dataframer.<a href="./src/dataframer/resources/dataframer/dataframer.py">list_historical_runs</a>() -> <a href="./src/dataframer/types/dataframer_list_historical_runs_response.py">DataframerListHistoricalRunsResponse</a></code>
- <code title="get /api/dataframer/models/">client.dataframer.<a href="./src/dataframer/resources/dataframer/dataframer.py">list_models</a>() -> <a href="./src/dataframer/types/dataframer_list_models_response.py">DataframerListModelsResponse</a></code>

## Analyze

Types:

```python
from dataframer.types.dataframer import AnalyzeCreateResponse, AnalyzeGetStatusResponse
```

Methods:

- <code title="post /api/dataframer/analyze/">client.dataframer.analyze.<a href="./src/dataframer/resources/dataframer/analyze.py">create</a>(\*\*<a href="src/dataframer/types/dataframer/analyze_create_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/analyze_create_response.py">AnalyzeCreateResponse</a></code>
- <code title="get /api/dataframer/analyze/status/{task_id}/">client.dataframer.analyze.<a href="./src/dataframer/resources/dataframer/analyze.py">get_status</a>(task_id) -> <a href="./src/dataframer/types/dataframer/analyze_get_status_response.py">AnalyzeGetStatusResponse</a></code>

## Chat

Types:

```python
from dataframer.types.dataframer import ChatGetHistoryResponse, ChatSendMessageResponse
```

Methods:

- <code title="get /api/dataframer/chat/">client.dataframer.chat.<a href="./src/dataframer/resources/dataframer/chat.py">get_history</a>() -> <a href="./src/dataframer/types/dataframer/chat_get_history_response.py">ChatGetHistoryResponse</a></code>
- <code title="post /api/dataframer/chat/">client.dataframer.chat.<a href="./src/dataframer/resources/dataframer/chat.py">send_message</a>(\*\*<a href="src/dataframer/types/dataframer/chat_send_message_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/chat_send_message_response.py">ChatSendMessageResponse</a></code>

## Datasets

Types:

```python
from dataframer.types.dataframer import (
    File,
    Folder,
    DatasetRetrieveResponse,
    DatasetUpdateResponse,
    DatasetListResponse,
    DatasetCreateFromZipResponse,
    DatasetCreateWithFilesResponse,
    DatasetListFilesResponse,
    DatasetListFoldersResponse,
)
```

Methods:

- <code title="get /api/dataframer/datasets/{dataset_id}/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">retrieve</a>(dataset_id) -> <a href="./src/dataframer/types/dataframer/dataset_retrieve_response.py">DatasetRetrieveResponse</a></code>
- <code title="put /api/dataframer/datasets/{dataset_id}/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">update</a>(dataset_id, \*\*<a href="src/dataframer/types/dataframer/dataset_update_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/dataset_update_response.py">DatasetUpdateResponse</a></code>
- <code title="get /api/dataframer/datasets/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">list</a>() -> <a href="./src/dataframer/types/dataframer/dataset_list_response.py">DatasetListResponse</a></code>
- <code title="delete /api/dataframer/datasets/{dataset_id}/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">delete</a>(dataset_id) -> None</code>
- <code title="post /api/dataframer/datasets/create-from-zip/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">create_from_zip</a>(\*\*<a href="src/dataframer/types/dataframer/dataset_create_from_zip_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/dataset_create_from_zip_response.py">DatasetCreateFromZipResponse</a></code>
- <code title="post /api/dataframer/datasets/create/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">create_with_files</a>(\*\*<a href="src/dataframer/types/dataframer/dataset_create_with_files_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/dataset_create_with_files_response.py">DatasetCreateWithFilesResponse</a></code>
- <code title="get /api/dataframer/datasets/{dataset_id}/files/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">list_files</a>(dataset_id) -> <a href="./src/dataframer/types/dataframer/dataset_list_files_response.py">DatasetListFilesResponse</a></code>
- <code title="get /api/dataframer/datasets/{dataset_id}/folders/">client.dataframer.datasets.<a href="./src/dataframer/resources/dataframer/datasets.py">list_folders</a>(dataset_id) -> <a href="./src/dataframer/types/dataframer/dataset_list_folders_response.py">DatasetListFoldersResponse</a></code>

## Evaluations

Types:

```python
from dataframer.types.dataframer import (
    EvaluationCreateResponse,
    EvaluationRetrieveResponse,
    EvaluationListResponse,
)
```

Methods:

- <code title="post /api/dataframer/evaluations/">client.dataframer.evaluations.<a href="./src/dataframer/resources/dataframer/evaluations/evaluations.py">create</a>(\*\*<a href="src/dataframer/types/dataframer/evaluation_create_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/evaluation_create_response.py">EvaluationCreateResponse</a></code>
- <code title="get /api/dataframer/evaluations/{evaluation_id}/">client.dataframer.evaluations.<a href="./src/dataframer/resources/dataframer/evaluations/evaluations.py">retrieve</a>(evaluation_id) -> <a href="./src/dataframer/types/dataframer/evaluation_retrieve_response.py">EvaluationRetrieveResponse</a></code>
- <code title="get /api/dataframer/evaluations/">client.dataframer.evaluations.<a href="./src/dataframer/resources/dataframer/evaluations/evaluations.py">list</a>() -> <a href="./src/dataframer/types/dataframer/evaluation_list_response.py">EvaluationListResponse</a></code>
- <code title="delete /api/dataframer/evaluations/{evaluation_id}/">client.dataframer.evaluations.<a href="./src/dataframer/resources/dataframer/evaluations/evaluations.py">delete</a>(evaluation_id) -> None</code>

### Chat

Types:

```python
from dataframer.types.dataframer.evaluations import ChatGetHistoryResponse, ChatSendMessageResponse
```

Methods:

- <code title="get /api/dataframer/evaluations/{evaluation_id}/chat/">client.dataframer.evaluations.chat.<a href="./src/dataframer/resources/dataframer/evaluations/chat.py">get_history</a>(evaluation_id) -> <a href="./src/dataframer/types/dataframer/evaluations/chat_get_history_response.py">ChatGetHistoryResponse</a></code>
- <code title="post /api/dataframer/evaluations/{evaluation_id}/chat/">client.dataframer.evaluations.chat.<a href="./src/dataframer/resources/dataframer/evaluations/chat.py">send_message</a>(evaluation_id, \*\*<a href="src/dataframer/types/dataframer/evaluations/chat_send_message_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/evaluations/chat_send_message_response.py">ChatSendMessageResponse</a></code>

## Files

Types:

```python
from dataframer.types.dataframer import (
    FileListResponse,
    FileDownloadResponse,
    FileGetContentResponse,
)
```

Methods:

- <code title="get /api/dataframer/files/">client.dataframer.files.<a href="./src/dataframer/resources/dataframer/files.py">list</a>() -> <a href="./src/dataframer/types/dataframer/file_list_response.py">FileListResponse</a></code>
- <code title="get /api/dataframer/files/{file_id}/download/">client.dataframer.files.<a href="./src/dataframer/resources/dataframer/files.py">download</a>(file_id) -> <a href="./src/dataframer/types/dataframer/file_download_response.py">FileDownloadResponse</a></code>
- <code title="get /api/dataframer/files/{file_id}/content/">client.dataframer.files.<a href="./src/dataframer/resources/dataframer/files.py">get_content</a>(file_id) -> <a href="./src/dataframer/types/dataframer/file_get_content_response.py">FileGetContentResponse</a></code>

## Generate

Types:

```python
from dataframer.types.dataframer import GenerateCreateResponse, GenerateRetrieveStatusResponse
```

Methods:

- <code title="post /api/dataframer/generate/">client.dataframer.generate.<a href="./src/dataframer/resources/dataframer/generate.py">create</a>(\*\*<a href="src/dataframer/types/dataframer/generate_create_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/generate_create_response.py">GenerateCreateResponse</a></code>
- <code title="get /api/dataframer/generate/status/{task_id}/">client.dataframer.generate.<a href="./src/dataframer/resources/dataframer/generate.py">retrieve_status</a>(task_id) -> <a href="./src/dataframer/types/dataframer/generate_retrieve_status_response.py">GenerateRetrieveStatusResponse</a></code>

## HumanLabels

Types:

```python
from dataframer.types.dataframer import HumanLabelRetrieveResponse, HumanLabelUpdateResponse
```

Methods:

- <code title="get /api/dataframer/human-labels/{label_id}/">client.dataframer.human_labels.<a href="./src/dataframer/resources/dataframer/human_labels.py">retrieve</a>(label_id) -> <a href="./src/dataframer/types/dataframer/human_label_retrieve_response.py">HumanLabelRetrieveResponse</a></code>
- <code title="put /api/dataframer/human-labels/{label_id}/">client.dataframer.human_labels.<a href="./src/dataframer/resources/dataframer/human_labels.py">update</a>(label_id) -> <a href="./src/dataframer/types/dataframer/human_label_update_response.py">HumanLabelUpdateResponse</a></code>
- <code title="delete /api/dataframer/human-labels/{label_id}/">client.dataframer.human_labels.<a href="./src/dataframer/resources/dataframer/human_labels.py">delete</a>(label_id) -> None</code>

## RedTeamRuns

Types:

```python
from dataframer.types.dataframer import (
    RedTeamRunCreateResponse,
    RedTeamRunRetrieveResponse,
    RedTeamRunListResponse,
    RedTeamRunRetrieveStatusResponse,
)
```

Methods:

- <code title="post /api/dataframer/red-team-runs/">client.dataframer.red_team_runs.<a href="./src/dataframer/resources/dataframer/red_team_runs.py">create</a>() -> <a href="./src/dataframer/types/dataframer/red_team_run_create_response.py">RedTeamRunCreateResponse</a></code>
- <code title="get /api/dataframer/red-team-runs/{run_id}/">client.dataframer.red_team_runs.<a href="./src/dataframer/resources/dataframer/red_team_runs.py">retrieve</a>(run_id) -> <a href="./src/dataframer/types/dataframer/red_team_run_retrieve_response.py">RedTeamRunRetrieveResponse</a></code>
- <code title="get /api/dataframer/red-team-runs/">client.dataframer.red_team_runs.<a href="./src/dataframer/resources/dataframer/red_team_runs.py">list</a>() -> <a href="./src/dataframer/types/dataframer/red_team_run_list_response.py">RedTeamRunListResponse</a></code>
- <code title="delete /api/dataframer/red-team-runs/{run_id}/">client.dataframer.red_team_runs.<a href="./src/dataframer/resources/dataframer/red_team_runs.py">delete</a>(run_id) -> None</code>
- <code title="get /api/dataframer/red-team-runs/{run_id}/status/">client.dataframer.red_team_runs.<a href="./src/dataframer/resources/dataframer/red_team_runs.py">retrieve_status</a>(run_id) -> <a href="./src/dataframer/types/dataframer/red_team_run_retrieve_status_response.py">RedTeamRunRetrieveStatusResponse</a></code>

## RedTeamSpecs

Types:

```python
from dataframer.types.dataframer import (
    RedTeamSpecCreateResponse,
    RedTeamSpecRetrieveResponse,
    RedTeamSpecUpdateResponse,
    RedTeamSpecListResponse,
)
```

Methods:

- <code title="post /api/dataframer/red-team-specs/">client.dataframer.red_team_specs.<a href="./src/dataframer/resources/dataframer/red_team_specs.py">create</a>() -> <a href="./src/dataframer/types/dataframer/red_team_spec_create_response.py">RedTeamSpecCreateResponse</a></code>
- <code title="get /api/dataframer/red-team-specs/{spec_id}/">client.dataframer.red_team_specs.<a href="./src/dataframer/resources/dataframer/red_team_specs.py">retrieve</a>(spec_id) -> <a href="./src/dataframer/types/dataframer/red_team_spec_retrieve_response.py">RedTeamSpecRetrieveResponse</a></code>
- <code title="patch /api/dataframer/red-team-specs/{spec_id}/">client.dataframer.red_team_specs.<a href="./src/dataframer/resources/dataframer/red_team_specs.py">update</a>(spec_id) -> <a href="./src/dataframer/types/dataframer/red_team_spec_update_response.py">RedTeamSpecUpdateResponse</a></code>
- <code title="get /api/dataframer/red-team-specs/">client.dataframer.red_team_specs.<a href="./src/dataframer/resources/dataframer/red_team_specs.py">list</a>() -> <a href="./src/dataframer/types/dataframer/red_team_spec_list_response.py">RedTeamSpecListResponse</a></code>
- <code title="delete /api/dataframer/red-team-specs/{spec_id}/">client.dataframer.red_team_specs.<a href="./src/dataframer/resources/dataframer/red_team_specs.py">delete</a>(spec_id) -> None</code>

## RedTeam

Types:

```python
from dataframer.types.dataframer import RedTeamCreateTaskResponse, RedTeamRetrieveStatusResponse
```

Methods:

- <code title="post /api/dataframer/red-team/">client.dataframer.red_team.<a href="./src/dataframer/resources/dataframer/red_team.py">create_task</a>() -> <a href="./src/dataframer/types/dataframer/red_team_create_task_response.py">RedTeamCreateTaskResponse</a></code>
- <code title="get /api/dataframer/red-team/status/{task_id}/">client.dataframer.red_team.<a href="./src/dataframer/resources/dataframer/red_team.py">retrieve_status</a>(task_id) -> <a href="./src/dataframer/types/dataframer/red_team_retrieve_status_response.py">RedTeamRetrieveStatusResponse</a></code>

## Runs

Types:

```python
from dataframer.types.dataframer import (
    RunCreateResponse,
    RunRetrieveResponse,
    RunUpdateResponse,
    RunListResponse,
    RunStatusResponse,
)
```

Methods:

- <code title="post /api/dataframer/runs/">client.dataframer.runs.<a href="./src/dataframer/resources/dataframer/runs/runs.py">create</a>(\*\*<a href="src/dataframer/types/dataframer/run_create_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/run_create_response.py">RunCreateResponse</a></code>
- <code title="get /api/dataframer/runs/{run_id}/">client.dataframer.runs.<a href="./src/dataframer/resources/dataframer/runs/runs.py">retrieve</a>(run_id) -> <a href="./src/dataframer/types/dataframer/run_retrieve_response.py">RunRetrieveResponse</a></code>
- <code title="put /api/dataframer/runs/{run_id}/">client.dataframer.runs.<a href="./src/dataframer/resources/dataframer/runs/runs.py">update</a>(run_id) -> <a href="./src/dataframer/types/dataframer/run_update_response.py">RunUpdateResponse</a></code>
- <code title="get /api/dataframer/runs/">client.dataframer.runs.<a href="./src/dataframer/resources/dataframer/runs/runs.py">list</a>() -> <a href="./src/dataframer/types/dataframer/run_list_response.py">RunListResponse</a></code>
- <code title="delete /api/dataframer/runs/{run_id}/">client.dataframer.runs.<a href="./src/dataframer/resources/dataframer/runs/runs.py">delete</a>(run_id) -> None</code>
- <code title="get /api/dataframer/runs/{run_id}/status/">client.dataframer.runs.<a href="./src/dataframer/resources/dataframer/runs/runs.py">status</a>(run_id) -> <a href="./src/dataframer/types/dataframer/run_status_response.py">RunStatusResponse</a></code>

### Evaluations

Types:

```python
from dataframer.types.dataframer.runs import EvaluationCreateResponse, EvaluationListResponse
```

Methods:

- <code title="post /api/dataframer/runs/{run_id}/evaluations/">client.dataframer.runs.evaluations.<a href="./src/dataframer/resources/dataframer/runs/evaluations.py">create</a>(run_id, \*\*<a href="src/dataframer/types/dataframer/runs/evaluation_create_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/runs/evaluation_create_response.py">EvaluationCreateResponse</a></code>
- <code title="get /api/dataframer/runs/{run_id}/evaluations/">client.dataframer.runs.evaluations.<a href="./src/dataframer/resources/dataframer/runs/evaluations.py">list</a>(run_id) -> <a href="./src/dataframer/types/dataframer/runs/evaluation_list_response.py">EvaluationListResponse</a></code>

### GeneratedFiles

Types:

```python
from dataframer.types.dataframer.runs import (
    GeneratedFileListResponse,
    GeneratedFileDownloadResponse,
    GeneratedFileGetContentResponse,
)
```

Methods:

- <code title="get /api/dataframer/runs/{run_id}/generated-files/">client.dataframer.runs.generated_files.<a href="./src/dataframer/resources/dataframer/runs/generated_files.py">list</a>(run_id) -> <a href="./src/dataframer/types/dataframer/runs/generated_file_list_response.py">GeneratedFileListResponse</a></code>
- <code title="get /api/dataframer/runs/{run_id}/generated-files/{file_id}/download/">client.dataframer.runs.generated_files.<a href="./src/dataframer/resources/dataframer/runs/generated_files.py">download</a>(file_id, \*, run_id) -> <a href="./src/dataframer/types/dataframer/runs/generated_file_download_response.py">GeneratedFileDownloadResponse</a></code>
- <code title="get /api/dataframer/runs/{run_id}/generated-files/download-all/">client.dataframer.runs.generated_files.<a href="./src/dataframer/resources/dataframer/runs/generated_files.py">download_all</a>(run_id) -> BinaryAPIResponse</code>
- <code title="get /api/dataframer/runs/{run_id}/generated-files/{file_id}/content/">client.dataframer.runs.generated_files.<a href="./src/dataframer/resources/dataframer/runs/generated_files.py">get_content</a>(file_id, \*, run_id) -> <a href="./src/dataframer/types/dataframer/runs/generated_file_get_content_response.py">GeneratedFileGetContentResponse</a></code>

### HumanLabels

Types:

```python
from dataframer.types.dataframer.runs import HumanLabelCreateResponse, HumanLabelListResponse
```

Methods:

- <code title="post /api/dataframer/runs/{run_id}/human-labels/">client.dataframer.runs.human_labels.<a href="./src/dataframer/resources/dataframer/runs/human_labels.py">create</a>(run_id) -> <a href="./src/dataframer/types/dataframer/runs/human_label_create_response.py">HumanLabelCreateResponse</a></code>
- <code title="get /api/dataframer/runs/{run_id}/human-labels/">client.dataframer.runs.human_labels.<a href="./src/dataframer/resources/dataframer/runs/human_labels.py">list</a>(run_id) -> <a href="./src/dataframer/types/dataframer/runs/human_label_list_response.py">HumanLabelListResponse</a></code>

### Samples

Types:

```python
from dataframer.types.dataframer.runs import SampleListResponse, SampleRetrieveByIndicesResponse
```

Methods:

- <code title="get /api/dataframer/runs/{run_id}/samples/">client.dataframer.runs.samples.<a href="./src/dataframer/resources/dataframer/runs/samples.py">list</a>(run_id, \*\*<a href="src/dataframer/types/dataframer/runs/sample_list_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/runs/sample_list_response.py">SampleListResponse</a></code>
- <code title="post /api/dataframer/runs/{run_id}/samples/">client.dataframer.runs.samples.<a href="./src/dataframer/resources/dataframer/runs/samples.py">retrieve_by_indices</a>(run_id, \*\*<a href="src/dataframer/types/dataframer/runs/sample_retrieve_by_indices_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/runs/sample_retrieve_by_indices_response.py">SampleRetrieveByIndicesResponse</a></code>

## Specs

Types:

```python
from dataframer.types.dataframer import (
    SpecCreateResponse,
    SpecRetrieveResponse,
    SpecUpdateResponse,
    SpecListResponse,
)
```

Methods:

- <code title="post /api/dataframer/specs/">client.dataframer.specs.<a href="./src/dataframer/resources/dataframer/specs/specs.py">create</a>(\*\*<a href="src/dataframer/types/dataframer/spec_create_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/spec_create_response.py">SpecCreateResponse</a></code>
- <code title="get /api/dataframer/specs/{spec_id}/">client.dataframer.specs.<a href="./src/dataframer/resources/dataframer/specs/specs.py">retrieve</a>(spec_id) -> <a href="./src/dataframer/types/dataframer/spec_retrieve_response.py">SpecRetrieveResponse</a></code>
- <code title="put /api/dataframer/specs/{spec_id}/">client.dataframer.specs.<a href="./src/dataframer/resources/dataframer/specs/specs.py">update</a>(spec_id, \*\*<a href="src/dataframer/types/dataframer/spec_update_params.py">params</a>) -> <a href="./src/dataframer/types/dataframer/spec_update_response.py">SpecUpdateResponse</a></code>
- <code title="get /api/dataframer/specs/">client.dataframer.specs.<a href="./src/dataframer/resources/dataframer/specs/specs.py">list</a>() -> <a href="./src/dataframer/types/dataframer/spec_list_response.py">SpecListResponse</a></code>
- <code title="delete /api/dataframer/specs/{spec_id}/">client.dataframer.specs.<a href="./src/dataframer/resources/dataframer/specs/specs.py">delete</a>(spec_id) -> None</code>

### Versions

Types:

```python
from dataframer.types.dataframer.specs import (
    VersionCreateResponse,
    VersionUpdateResponse,
    VersionListResponse,
)
```

Methods:

- <code title="post /api/dataframer/specs/{spec_id}/versions/">client.dataframer.specs.versions.<a href="./src/dataframer/resources/dataframer/specs/versions.py">create</a>(spec_id) -> <a href="./src/dataframer/types/dataframer/specs/version_create_response.py">VersionCreateResponse</a></code>
- <code title="get /api/dataframer/specs/{spec_id}/versions/{version_id}/">client.dataframer.specs.versions.<a href="./src/dataframer/resources/dataframer/specs/versions.py">retrieve</a>(version_id, \*, spec_id) -> <a href="./src/dataframer/types/spec_version.py">SpecVersion</a></code>
- <code title="put /api/dataframer/specs/{spec_id}/versions/{version_id}/">client.dataframer.specs.versions.<a href="./src/dataframer/resources/dataframer/specs/versions.py">update</a>(version_id, \*, spec_id) -> <a href="./src/dataframer/types/dataframer/specs/version_update_response.py">VersionUpdateResponse</a></code>
- <code title="get /api/dataframer/specs/{spec_id}/versions/">client.dataframer.specs.versions.<a href="./src/dataframer/resources/dataframer/specs/versions.py">list</a>(spec_id) -> <a href="./src/dataframer/types/dataframer/specs/version_list_response.py">VersionListResponse</a></code>
- <code title="delete /api/dataframer/specs/{spec_id}/versions/{version_id}/">client.dataframer.specs.versions.<a href="./src/dataframer/resources/dataframer/specs/versions.py">delete</a>(version_id, \*, spec_id) -> None</code>
