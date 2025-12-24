# Auth

Types:

```python
from wood_wide_ai.types import AuthRetrieveMeResponse
```

Methods:

- <code title="get /auth/me">client.auth.<a href="./src/wood_wide_ai/resources/auth.py">retrieve_me</a>() -> <a href="./src/wood_wide_ai/types/auth_retrieve_me_response.py">AuthRetrieveMeResponse</a></code>

# API

## Datasets

Types:

```python
from wood_wide_ai.types.api import DatasetPublic, Schema, DatasetListResponse
```

Methods:

- <code title="get /api/datasets/{dataset_id}">client.api.datasets.<a href="./src/wood_wide_ai/resources/api/datasets.py">retrieve</a>(dataset_id, \*\*<a href="src/wood_wide_ai/types/api/dataset_retrieve_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/dataset_public.py">DatasetPublic</a></code>
- <code title="get /api/datasets">client.api.datasets.<a href="./src/wood_wide_ai/resources/api/datasets.py">list</a>(\*\*<a href="src/wood_wide_ai/types/api/dataset_list_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/dataset_list_response.py">DatasetListResponse</a></code>
- <code title="delete /api/datasets/{dataset_id}">client.api.datasets.<a href="./src/wood_wide_ai/resources/api/datasets.py">delete</a>(dataset_id, \*\*<a href="src/wood_wide_ai/types/api/dataset_delete_params.py">params</a>) -> object</code>
- <code title="post /api/datasets">client.api.datasets.<a href="./src/wood_wide_ai/resources/api/datasets.py">upload</a>(\*\*<a href="src/wood_wide_ai/types/api/dataset_upload_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/dataset_public.py">DatasetPublic</a></code>

## Models

Types:

```python
from wood_wide_ai.types.api import ModelPublic, ModelListResponse
```

Methods:

- <code title="get /api/models/{model_id}">client.api.models.<a href="./src/wood_wide_ai/resources/api/models/models.py">retrieve</a>(model_id, \*\*<a href="src/wood_wide_ai/types/api/model_retrieve_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/model_public.py">ModelPublic</a></code>
- <code title="get /api/models">client.api.models.<a href="./src/wood_wide_ai/resources/api/models/models.py">list</a>() -> <a href="./src/wood_wide_ai/types/api/model_list_response.py">ModelListResponse</a></code>

### Prediction

Methods:

- <code title="post /api/models/prediction/{model_id}/infer">client.api.models.prediction.<a href="./src/wood_wide_ai/resources/api/models/prediction.py">infer</a>(model_id, \*\*<a href="src/wood_wide_ai/types/api/models/prediction_infer_params.py">params</a>) -> object</code>
- <code title="post /api/models/prediction/train">client.api.models.prediction.<a href="./src/wood_wide_ai/resources/api/models/prediction.py">train</a>(\*\*<a href="src/wood_wide_ai/types/api/models/prediction_train_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/model_public.py">ModelPublic</a></code>

### Clustering

Methods:

- <code title="post /api/models/clustering/{model_id}/infer">client.api.models.clustering.<a href="./src/wood_wide_ai/resources/api/models/clustering.py">infer</a>(model_id, \*\*<a href="src/wood_wide_ai/types/api/models/clustering_infer_params.py">params</a>) -> object</code>
- <code title="post /api/models/clustering/train">client.api.models.clustering.<a href="./src/wood_wide_ai/resources/api/models/clustering.py">train</a>(\*\*<a href="src/wood_wide_ai/types/api/models/clustering_train_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/model_public.py">ModelPublic</a></code>

### Anomaly

Methods:

- <code title="post /api/models/anomaly/{model_id}/infer">client.api.models.anomaly.<a href="./src/wood_wide_ai/resources/api/models/anomaly.py">infer</a>(model_id, \*\*<a href="src/wood_wide_ai/types/api/models/anomaly_infer_params.py">params</a>) -> object</code>
- <code title="post /api/models/anomaly/train">client.api.models.anomaly.<a href="./src/wood_wide_ai/resources/api/models/anomaly.py">train</a>(\*\*<a href="src/wood_wide_ai/types/api/models/anomaly_train_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/model_public.py">ModelPublic</a></code>

### Embedding

Methods:

- <code title="post /api/models/embedding/{model_id}/infer">client.api.models.embedding.<a href="./src/wood_wide_ai/resources/api/models/embedding.py">infer</a>(model_id, \*\*<a href="src/wood_wide_ai/types/api/models/embedding_infer_params.py">params</a>) -> object</code>
- <code title="post /api/models/embedding/train">client.api.models.embedding.<a href="./src/wood_wide_ai/resources/api/models/embedding.py">train</a>(\*\*<a href="src/wood_wide_ai/types/api/models/embedding_train_params.py">params</a>) -> <a href="./src/wood_wide_ai/types/api/model_public.py">ModelPublic</a></code>
