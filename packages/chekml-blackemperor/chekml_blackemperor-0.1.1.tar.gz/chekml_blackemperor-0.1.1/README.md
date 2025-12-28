ChekML Black Emperor — Quick Guide
=================================

This README shows example model code, how to add a custom aggregation plugin, how to configure model hyperparameters (including model I/O shapes and "online" aggregation), and documents the server API endpoints available in this repository.

Quick start
-----------
- Install requirements (use a virtualenv):

```bash
pip install -r requirements.txt
# If not present, typical deps: aiohttp, torch, torchvision, google-api-python-client, pandas, numpy
```

- Run the server:

```bash
python -m chekml_blackemperor.cli server
```

- Start a worker (example):

```bash
python -m chekml_blackemperor.worker
```

Environment variables
---------------------
The project supports configuring runtime behavior via environment variables. Below are common examples for both Unix-like shells and Windows (PowerShell / cmd). Replace values with paths or names that match your environment.

Common variables:
- `CHEKML_GOOGLE_FOLDER`: Google Drive folder name used for dataset listing/downloads (example: `chekml_datasets`).
- `CHEKML_DRIVE_CREDENTIALS`: Path to Google Drive credentials JSON (if using Drive integration).
- `CHEKML_SERVER_HOST`: Host interface for the server (default `0.0.0.0`).
- `CHEKML_SERVER_PORT`: Port for the server (default `8080`).
- `CHEKML_VERBOSE`: Set to `1` to enable verbose worker logs.

Bash / zsh (temporary for session):

```bash
export CHEKML_GOOGLE_FOLDER=chekml_datasets
export CHEKML_DRIVE_CREDENTIALS=/path/to/credentials.json
export CHEKML_SERVER_HOST=0.0.0.0
export CHEKML_SERVER_PORT=8080
export CHEKML_VERBOSE=1
```

PowerShell (temporary for session):

```powershell
$env:CHEKML_GOOGLE_FOLDER = 'chekml_datasets'
$env:CHEKML_DRIVE_CREDENTIALS = 'C:\path\to\credentials.json'
$env:CHEKML_SERVER_HOST = '0.0.0.0'
$env:CHEKML_SERVER_PORT = '8080'
$env:CHEKML_VERBOSE = '1'
```

PowerShell (persistent for current user):

```powershell
setx CHEKML_GOOGLE_FOLDER 'chekml_datasets'
setx CHEKML_DRIVE_CREDENTIALS 'C:\path\to\credentials.json'
setx CHEKML_SERVER_HOST '0.0.0.0'
setx CHEKML_SERVER_PORT '8080'
setx CHEKML_VERBOSE '1'
```

Command Prompt (cmd.exe, temporary):

```cmd
set CHEKML_GOOGLE_FOLDER=chekml_datasets
set CHEKML_DRIVE_CREDENTIALS=C:\path\to\credentials.json
set CHEKML_SERVER_HOST=0.0.0.0
set CHEKML_SERVER_PORT=8080
set CHEKML_VERBOSE=1
```

Linux systemd service (example snippet):

```
[Unit]
Description=ChekML Black Emperor Server

[Service]
Environment=CHEKML_GOOGLE_FOLDER=chekml_datasets
Environment=CHEKML_DRIVE_CREDENTIALS=/path/to/credentials.json
Environment=CHEKML_SERVER_PORT=8080
ExecStart=/usr/bin/python -m chekml_blackemperor.cli server

[Install]
WantedBy=multi-user.target
```

Example model (PyTorch)
-----------------------
Place model files in `chekml_blackemperor/local_models` or `drive_models` (the project scans `local_models`). A minimal example model class that the `ModelLoader` will discover:

```python
# example model: drive_models/simple_mlp.py
import torch.nn as nn

class SimpleMLP(nn.Module):
    def __init__(self, input_dim=784, hidden=128, output_dim=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
            nn.LogSoftmax(dim=1)
        )
    def forward(self, x):
        return self.net(x)
```

Custom aggregation plugin
-------------------------
Create a Python file under `chekml_blackemperor/plugins` (or `chekml_blackemperor/plugins/*.py`) exporting either a `register_aggregations(registry)` function or defining an `AggregationMethod` subclass. Example:

```python
# plugins/my_online_agg.py
from aggregation.base import AggregationMethod
import torch

class MyOnlineAggregation(AggregationMethod):
    def aggregate(self, global_weights, local_results, config=None):
        # offline aggregation (called when full results are available)
        # naive average example
        if not local_results:
            return global_weights
        # assume tensors list
        stacked = torch.stack(local_results, dim=0)
        return torch.mean(stacked, dim=0)

    def on_intermediate(self, global_weights, local_payload, config=None):
        # called when workers send intermediate payloads (e.g. after backward)
        # You can return {'weights': new_weights} to update global model immediately
        try:
            # inspect payload (example expects dict with 'grad_norms')
            gn = local_payload.get('grad_norms')
            # optionally adjust global_weights and return
            return None
        except Exception:
            return None

def register_aggregations(registry):
    registry.register('my_online', MyOnlineAggregation())
```

Model hyperparameters and I/O shapes
-----------------------------------
Model configs are stored on the server in `model_configs.json` and editable from the Control Panel or via API.
A model config is standard JSON. Common keys:

- `learning_rate`: float
- `batch_size`: int
- `max_batches`: int
- `online_aggregation`: boolean — if true, worker will send intermediate payloads and aggregators may react
- `aggregation`: string — aggregator name to use for online aggregation
- `input_shape`: array — e.g. `[1,28,28]` or `[784]`
- `output_shape`: array — e.g. `[10]`
- `handlers`: dict — optional handler descriptions to map outputs to next model inputs

Example config JSON:

```json
{
  "learning_rate": 0.01,
  "batch_size": 64,
  "max_batches": 500,
  "online_aggregation": true,
  "aggregation": "my_online",
  "input_shape": [1,28,28],
  "output_shape": [10],
  "handlers": { "softmax_to_next": "take argmax and embed" }
}
```

Set/get model config via API (or use the Control Panel):

- GET /get_model_config?name=MODEL_NAME  -> JSON config
- POST /set_model_config (form: `name`, `config` JSON) -> saves config

APIs (HTTP + WebSocket)
-----------------------
HTTP endpoints (server routes) provided by `server.py`:

- GET /                 : Control Panel (UI)
- GET /ws               : WebSocket endpoint for workers to connect (legacy)
- GET /client_ws        : WebSocket endpoint for browser clients (UI notifications)
- GET /model_tree       : Returns JSON with current nodes, edges, clusters, available_aggregations
- POST /model_tree      : Add/delete model-tree edges (form fields)
- POST /create_cluster  : Create a cluster from selected node ids (form: `nodes`, `name`)
- POST /delete_cluster  : Delete a cluster (form: `id`)
- POST /join_nodes      : Create an aggregation link (form: `nodes`, `aggregation`, `save_name`)
- POST /aggregate_flow  : Trigger aggregation for a cluster (form: `target`, `aggregation`, `config`, `save_name`)
- POST /set_model_config: Set model config (form: `name`, `config`)
- GET /get_model_config : Get model config (query `name`)
- GET /list_datasets    : List datasets from Google Drive `chekml_datasets` (if enabled)
- POST /set_cluster_config : Set a cluster-level config (form: `id`, `config`)
- POST /train_cluster   : Start training across a cluster (form: `id`, `model_name`, `aggregation`)
- POST /save_worker     : Persist a worker's last trained result into `global_models` and saved_models/ (form: `worker_id`, optional `save_name`)
- POST /save_aggregated : Placeholder to save aggregated model (can be used after cluster aggregation completes)
- GET /download_model/{name} : Download a model file or weights by name
- POST /assign         : Assign model to a worker (form: `worker_id`, `model_name`)
- POST /command_worker : Send arbitrary command to a worker (form fields depend on command)
- POST /command        : Global CLI-like commands from the UI

WebSockets
- Worker ↔ Server: workers connect and send JSON messages: `status`, `initial_weights`, `result`, `intermediate`.
- Client ↔ Server: UI connects to `/client_ws` to receive notifications to refresh the Control Panel.

Examples
--------
Set model config via curl:

```bash
curl -X POST -F "name=SimpleMLP" -F "config=$(cat config.json)" http://localhost:8080/set_model_config
```

Enable online aggregation for cluster via curl:

```bash
curl -X POST -F "id=cluster-123" -F "config=$(echo '{"online_aggregation":true,"aggregation":"my_online"}')" http://localhost:8080/set_cluster_config
```

Start cluster training via curl:

```bash
curl -X POST -F "id=cluster-123" -F "model_name=SimpleMLP" -F "aggregation=my_online" http://localhost:8080/train_cluster
```

Saving a worker's trained model (per-instance save):

```bash
curl -X POST -F "worker_id=worker_abc" -F "save_name=saved_worker_abc" http://localhost:8080/save_worker
```

Where things are stored
----------------------
- Model configs: `model_configs.json` (server-side)
- Model tree: `model_tree.json`
- Clusters: `model_clusters.json`
- Saved models (disk): `saved_models/*.pt`
- Drive models/datasets: stored under configured Google Drive folder names

Troubleshooting
---------------
- If dataset entries flicker or disappear, ensure the Control Panel is running the latest `server.py` which uses a persistent `datasets_panel` and updates its contents rather than re-creating the section.
- Workers only introspect shapes when they have a train loader that yields a sample. Ensure your worker dataset loader returns tensors.
- If `AggregationMethod.on_intermediate` raises exceptions, use logging in your plugin to diagnose issues.

Contributing
------------
- Add plugin files under `chekml_blackemperor/plugins` and register via `register_aggregations(registry)` or by defining `AggregationMethod` subclasses.
- Keep UI edits inside `server.py::index()`; the Control Panel is an inlined HTML/JS page.

Contact
-------
For questions or help on this repository, open an issue or request further changes.
# ChekML - Cross-Machine Training System

ChekML is a Python library for distributed and federated learning across multiple machines.

## Installation

```bash
pip install chekml
