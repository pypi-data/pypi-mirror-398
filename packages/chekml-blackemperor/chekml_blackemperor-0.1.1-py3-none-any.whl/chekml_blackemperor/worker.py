import asyncio, websockets, json, os, sys, importlib.util, inspect
import uuid
import torch, torch.nn as nn, torch.optim as optim
from torchvision import datasets, transforms
import io, base64, logging
from typing import Optional, Dict, Any
import aiohttp

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .utils import GoogleDriveClient, ensure_model_file, get_available_gpus
    from .config import WorkerConfig
    from .models import ModelLoader
except ImportError:
    from utils import GoogleDriveClient, ensure_model_file, get_available_gpus
    from config import WorkerConfig
    from models import ModelLoader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChekMLWorker:
    def __init__(self, config_path: str = None):
        # Load config from file if provided, otherwise from environment
        if config_path:
            try:
                self.config = WorkerConfig.from_file(config_path)
            except Exception:
                self.config = WorkerConfig.from_env()
        else:
            try:
                self.config = WorkerConfig.from_env()
            except Exception:
                self.config = WorkerConfig()
        self.model_loader = ModelLoader()
        self.google_drive_client = None
        self.device_info = ""
        # persistent worker id: env override, or load/save to .chekml_worker_id
        self.worker_id = os.getenv('CHEKML_WORKER_ID')
        if not self.worker_id:
            try:
                id_path = os.path.join(os.getcwd(), '.chekml_worker_id')
                if os.path.exists(id_path):
                    with open(id_path, 'r') as f:
                        self.worker_id = f.read().strip()
                else:
                    self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"
                    with open(id_path, 'w') as f:
                        f.write(self.worker_id)
            except Exception:
                self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        
        # per-process instance id to distinguish multiple worker processes on same host
        try:
            self.instance_id = f"inst_{uuid.uuid4().hex[:8]}_{os.getpid()}"
        except Exception:
            self.instance_id = f"inst_{uuid.uuid4().hex[:8]}"
        # Setup device
        self._setup_device()
        
        # Initialize model and optimizer
        self.model = None
        self.optimizer = None
        self.loss_fn = nn.NLLLoss()
        
        # Data loaders
        self.train_loader = None
        self.test_loader = None
        self._setup_data_loaders()
        
        # WebSocket connection
        self.ws = None
        
        # Load Google Drive client if configured
        if self.config.google_drive_enabled:
            self.google_drive_client = GoogleDriveClient(
                credentials_file=self.config.google_drive_credentials,
                folder_name=self.config.google_drive_folder
            )
    
    def _setup_device(self):
        """Setup GPU/CPU device with automatic detection"""
        gpus = get_available_gpus()
        
        if gpus:
            if len(gpus) > 1:
                self.device = torch.device("cuda:0")
                self.device_info = f"cuda:0 (multi-gpu available: {len(gpus)})"
            else:
                self.device = torch.device("cuda")
                self.device_info = "cuda"
            logger.info(f"Using GPU: {gpus}")
        else:
            self.device = torch.device("cpu")
            self.device_info = "cpu"
            logger.info("Using CPU")
    
    def _setup_data_loaders(self):
        """Setup data loaders for training and testing"""
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])
        # Diagnostic: read dataset config and Drive availability
        try:
            ds_name = getattr(self.config, 'dataset_name', None)
            ds_source = getattr(self.config, 'dataset_source', 'local')
            gd_enabled = getattr(self.config, 'google_drive_enabled', False)
        except Exception:
            ds_name = None; ds_source = 'local'; gd_enabled = False

        logger.info(f"Dataset config: name={ds_name}, source={ds_source}, google_drive_enabled={gd_enabled}")

        if ds_name and ds_source == 'drive':
            if not self.google_drive_client:
                logger.warning('dataset_source=drive but GoogleDriveClient not initialized; check CHEKML_GOOGLE_DRIVE_ENABLED and credentials')
                try:
                    self.dataset_info = {'name': ds_name, 'source': 'drive', 'downloaded': False}
                except Exception:
                    self.dataset_info = {'name': ds_name, 'source': 'drive'}
                self._setup_mnist_loaders(transform)
                return

            try:
                ds_client = self.google_drive_client
                if getattr(ds_client, 'folder_name', None) != 'chekml_datasets':
                    ds_client = GoogleDriveClient(credentials_file=self.config.google_drive_credentials, folder_name='chekml_datasets')
                logger.info(f"Using Drive folder: {getattr(ds_client,'folder_name',None)} id={getattr(ds_client,'folder_id',None)}")
                logger.info(f"Attempting to download dataset from Drive: {ds_name}")
                data_bytes = ds_client.download_dataset(ds_name)
                if not data_bytes:
                    logger.warning(f"Dataset {ds_name} not found in Drive folder {ds_client.folder_name}")
                    try:
                        self.dataset_info = {'name': ds_name, 'source': 'drive', 'downloaded': False}
                    except Exception:
                        self.dataset_info = {'name': ds_name, 'source': 'drive'}
                    self._setup_mnist_loaders(transform)
                    return

                logger.info(f"Downloaded dataset {ds_name}: {len(data_bytes)} bytes")

                # attempt to interpret common formats
                import numpy as np
                if ds_name.endswith('.pt') or ds_name.endswith('.pth'):
                    buf = io.BytesIO(data_bytes)
                    dataset_obj = torch.load(buf, map_location='cpu')
                elif ds_name.endswith('.npz'):
                    dataset_obj = np.load(io.BytesIO(data_bytes))
                elif ds_name.endswith('.npy'):
                    dataset_obj = np.load(io.BytesIO(data_bytes))
                elif ds_name.endswith('.csv'):
                    import pandas as pd
                    dataset_obj = pd.read_csv(io.BytesIO(data_bytes))
                else:
                    path = os.path.join(os.getcwd(), ds_name)
                    with open(path, 'wb') as f:
                        f.write(data_bytes)
                    dataset_obj = None

                # If dataset_obj is found and is array-like, wrap into TensorDataset
                try:
                    if isinstance(dataset_obj, dict) and 'x' in dataset_obj and 'y' in dataset_obj:
                        x = torch.tensor(dataset_obj['x']).float()
                        y = torch.tensor(dataset_obj['y']).long()
                        self.train_loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x,y), batch_size=self.config.batch_size, shuffle=True)
                        self.test_loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x,y), batch_size=1000, shuffle=False)
                        try:
                            self.dataset_info = {'name': ds_name, 'source': 'drive', 'dtype': str(x.dtype), 'x_shape': list(x.shape), 'y_shape': list(y.shape)}
                        except Exception:
                            self.dataset_info = {'name': ds_name, 'source': 'drive'}
                    elif hasattr(dataset_obj, 'shape'):
                        arr = dataset_obj
                        if getattr(arr, 'dtype', None) is not None and getattr(arr, 'shape', None) is not None:
                            x = torch.tensor(arr).float()
                            y = None
                            try:
                                if x.dim() == 2:
                                    y = x[:, -1].long()
                                    x = x[:, :-1]
                            except Exception:
                                pass
                            if y is not None:
                                self.train_loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x,y), batch_size=self.config.batch_size, shuffle=True)
                                self.test_loader = torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x,y), batch_size=1000, shuffle=False)
                                try:
                                    self.dataset_info = {'name': ds_name, 'source': 'drive', 'dtype': str(x.dtype), 'x_shape': list(x.shape), 'y_shape': list(y.shape)}
                                except Exception:
                                    self.dataset_info = {'name': ds_name, 'source': 'drive'}
                    else:
                        raise Exception('Unsupported dataset object from Drive')
                except Exception as e:
                    logger.warning(f"Drive dataset parsing failed: {e}; falling back to MNIST")
                    self._setup_mnist_loaders(transform)
                    return
            except Exception as e:
                logger.warning(f"Failed to load dataset from Drive: {e}; falling back to MNIST")
                self._setup_mnist_loaders(transform)
                return

        # default to MNIST loaders
        self._setup_mnist_loaders(transform)

    def _setup_mnist_loaders(self, transform):
        self.train_loader = torch.utils.data.DataLoader(
            datasets.MNIST('.', train=True, download=True, transform=transform),
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.config.num_workers
        )

        self.test_loader = torch.utils.data.DataLoader(
            datasets.MNIST('.', train=False, transform=transform),
            batch_size=1000,
            shuffle=False,
            num_workers=self.config.num_workers
        )
    
    async def connect(self):
        """Connect to server"""
        server_url = self.config.server_url
        
        if not server_url:
            logger.error("No server URL configured. Set CHEKML_EMPEROR or CHEKML_SERVER_URL environment variable.")
            return
        
        logger.info(f"Connecting to {server_url}")
        
        try:
            self.ws = await websockets.connect(
                server_url,
                max_size=None,
                ping_interval=20,
                ping_timeout=60
            )
            
            # Send initial status
            await self.send_status("idle")
            logger.info("Connected to server")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def send_status(self, status: str, model_name: str = None):
        """Send status update to server"""
        message = {
            "type": "status",
            "status": status,
            "device": self.device_info
        }
        # include persistent worker id so server can re-associate reconnects
        try:
            message['worker_id'] = self.worker_id
        except Exception:
            pass
        # include ephemeral instance id for this process so server can distinguish multiple
        try:
            message['instance_id'] = self.instance_id
        except Exception:
            pass
        
        if model_name:
            message["model"] = model_name

        # include dataset metadata if available
        try:
            if hasattr(self, 'dataset_info') and self.dataset_info:
                message['dataset'] = self.dataset_info
        except Exception:
            pass
        
        await self.ws.send(json.dumps(message))
    
    # In worker.py, update the load_model method
    async def load_model(self, model_name: str):
        """Load model from local file or Google Drive"""
        logger.info(f"Loading model: {model_name}")
        
        try:
            # Try local first
            model_class = self.model_loader.load_local_model(model_name)
            if model_class:
                self.model = model_class().to(self.device)
                logger.info(f"Loaded model {model_name} from local file")
            else:
                # Try Google Drive via direct Drive client if configured
                if self.google_drive_client and self.google_drive_client.service:
                    logger.info(f"Attempting to load {model_name} from Google Drive")
                    model_class = await self.model_loader.load_drive_model(
                        model_name, self.google_drive_client
                    )
                    if model_class:
                        self.model = model_class().to(self.device)
                        logger.info(f"Loaded model {model_name} from Google Drive")

                # If still not available, try to download from server HTTP endpoint
                if not self.model:
                    # derive HTTP base from websocket server_url
                    server_ws = self.config.server_url
                    http_base = None
                    if server_ws:
                        if server_ws.startswith('ws://'):
                            http_base = 'http://' + server_ws.split('://',1)[1]
                        elif server_ws.startswith('wss://'):
                            http_base = 'https://' + server_ws.split('://',1)[1]
                        # strip trailing /ws if present
                        if http_base.endswith('/ws'):
                            http_base = http_base[:-3]

                    if http_base:
                        dl_url = f"{http_base}/download_model/{model_name}"
                        logger.info(f"Attempting to download model from server: {dl_url}")
                        try:
                            async with aiohttp.ClientSession() as sess:
                                async with sess.get(dl_url, timeout=30) as resp:
                                    if resp.status == 200:
                                        data = await resp.read()
                                        # Try to load as torch weights
                                        try:
                                            buf = io.BytesIO(data)
                                            weights = torch.load(buf, map_location='cpu')
                                            # We have weights but need a model class locally
                                            model_class = self.model_loader.load_local_model(model_name)
                                            if model_class:
                                                self.model = model_class().to(self.device)
                                                # load weights into model
                                                for p, w in zip(self.model.parameters(), weights):
                                                    p.data.copy_(w.to(self.device))
                                                logger.info(f"Loaded weights for {model_name} from server")
                                            else:
                                                logger.error(f"Weights downloaded but no local model class for {model_name}")
                                        except Exception:
                                            # treat as source code, save and import
                                            try:
                                                models_dir = os.path.join(os.getcwd(), 'drive_models')
                                                os.makedirs(models_dir, exist_ok=True)
                                                path = os.path.join(models_dir, f"{model_name}.py")
                                                with open(path, 'wb') as f:
                                                    f.write(data)
                                                # import
                                                spec = importlib.util.spec_from_file_location(f"drive_model_{model_name}", path)
                                                mod = importlib.util.module_from_spec(spec)
                                                spec.loader.exec_module(mod)
                                                for name, obj in inspect.getmembers(mod):
                                                    if inspect.isclass(obj) and issubclass(obj, nn.Module) and obj != nn.Module:
                                                        self.model = obj().to(self.device)
                                                        logger.info(f"Loaded model class {name} from server-sent source {path}")
                                                        break
                                            except Exception as e:
                                                logger.error(f"Failed to load downloaded model source: {e}")
                                    else:
                                        logger.info(f"Server returned {resp.status} when fetching model")
                        except Exception as e:
                            logger.error(f"Failed to download model from server: {e}")

                if not self.model:
                    logger.error(f"Model {model_name} not found locally, in Google Drive, or on server")
                    return False
            
            # Setup optimizer
            self.optimizer = optim.SGD(self.model.parameters(), lr=self.config.learning_rate)
            
            # Try to fetch per-model config from server (so worker can enable online aggregation)
            self.model_config = {}
            try:
                server_ws = self.config.server_url
                http_base = None
                if server_ws:
                    if server_ws.startswith('ws://'):
                        http_base = 'http://' + server_ws.split('://',1)[1]
                    elif server_ws.startswith('wss://'):
                        http_base = 'https://' + server_ws.split('://',1)[1]
                    if http_base.endswith('/ws'):
                        http_base = http_base[:-3]
                if http_base:
                    cfg_url = f"{http_base}/get_model_config?name={model_name}"
                    try:
                        async with aiohttp.ClientSession() as sess:
                            async with sess.get(cfg_url, timeout=5) as resp:
                                if resp.status == 200:
                                    try:
                                        self.model_config = await resp.json()
                                        logger.info(f"Loaded model config for {model_name}: {self.model_config}")
                                    except Exception:
                                        self.model_config = {}
                    except Exception:
                        pass
            except Exception:
                pass

            # record current model name for later reference
            try:
                self.current_model_name = model_name
            except Exception:
                self.current_model_name = None

            # Attempt to introspect model input/output shapes using a sample from the train loader
            try:
                input_shape = None
                output_shape = None
                sample = None
                if hasattr(self, 'train_loader') and self.train_loader is not None:
                    try:
                        it = iter(self.train_loader)
                        batch = next(it)
                        if isinstance(batch, (list, tuple)):
                            sample = batch[0]
                        else:
                            sample = batch
                        # take single example
                        if isinstance(sample, torch.Tensor):
                            sample = sample[:1]
                    except Exception:
                        sample = None
                if sample is not None and isinstance(sample, torch.Tensor):
                    sample = sample.to(self.device)
                    self.model.eval()
                    with torch.no_grad():
                        out = self.model(sample)
                    try:
                        input_shape = list(sample.shape[1:])
                    except Exception:
                        input_shape = None
                    try:
                        output_shape = list(out.shape[1:]) if hasattr(out, 'shape') else None
                    except Exception:
                        output_shape = None
                # push I/O shapes to server by merging into model config
                if (input_shape or output_shape) and http_base:
                    merged = dict(self.model_config or {})
                    if input_shape:
                        merged['input_shape'] = input_shape
                    if output_shape:
                        merged['output_shape'] = output_shape
                    try:
                        post_url = f"{http_base}/set_model_config"
                        async with aiohttp.ClientSession() as sess:
                            fm = aiohttp.FormData()
                            fm.add_field('name', model_name)
                            fm.add_field('config', json.dumps(merged))
                            async with sess.post(post_url, data=fm, timeout=5) as presp:
                                if presp.status == 200:
                                    logger.info(f"Pushed I/O shapes for {model_name} to server")
                    except Exception as e:
                        logger.warning(f"Failed to push model I/O shapes: {e}")
            except Exception:
                pass

            # Send initial weights to server
            await self.send_initial_weights(model_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    async def send_initial_weights(self, model_name: str):
        """Send initial model weights to server"""
        buf = io.BytesIO()
        torch.save([p.detach().cpu() for p in self.model.parameters()], buf)
        payload = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        message = {
            "type": "initial_weights",
            "model": model_name,
            "payload": payload
        }
        
        await self.ws.send(json.dumps(message))
    
    def evaluate(self):
        """Evaluate model on test set"""
        self.model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                pred = output.argmax(dim=1)
                correct += pred.eq(target).sum().item()
                total += target.size(0)
        
        return correct / total
    
    async def train_epoch(self, mode: str = "federated"):
        """Train for one epoch"""
        logger.info(f"Starting training in {mode} mode")
        
        if mode == "distributed":
            # Compute gradients without updating weights
            self.model.train()
            data, target = next(iter(self.train_loader))
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.loss_fn(output, target)
            loss.backward()
            
            # Return gradients
            result = [p.grad.detach().cpu() for p in self.model.parameters()]
        else:
            # Full epoch training (federated)
            self.model.train()
            
            for batch_idx, (data, target) in enumerate(self.train_loader):
                if batch_idx >= self.config.max_batches:
                    break

                data, target = data.to(self.device), target.to(self.device)

                self.optimizer.zero_grad()
                output = self.model(data)
                loss = self.loss_fn(output, target)
                loss.backward()
                self.optimizer.step()

                # verbose logging per interval if enabled
                try:
                    if getattr(self.config, 'verbose', False) and (batch_idx % max(1, getattr(self.config, 'verbose_interval', 10)) == 0):
                        logger.info(f"[train] batch {batch_idx} loss={loss.item():.4f}")
                except Exception:
                    pass
                # send intermediate payload for online aggregation if enabled in model_config
                try:
                    online = bool(self.model_config.get('online_aggregation')) if hasattr(self, 'model_config') else False
                except Exception:
                    online = False
                if online:
                    try:
                        # compute simple grad norms as small payload
                        grad_norms = []
                        for p in self.model.parameters():
                            try:
                                g = p.grad
                                grad_norms.append(float(g.norm().item()) if g is not None else 0.0)
                            except Exception:
                                grad_norms.append(0.0)
                        msg = {
                            'type': 'intermediate',
                            'model': getattr(self, 'current_model_name', None),
                            'stage': 'after_backward',
                            'payload': { 'grad_norms': grad_norms },
                            'aggregation': self.model_config.get('aggregation') if isinstance(self.model_config, dict) else None
                        }
                        await self.ws.send(json.dumps(msg))
                    except Exception:
                        pass
            
            # Return updated weights
            result = [p.detach().cpu() for p in self.model.parameters()]
        
        # Package results
        buf = io.BytesIO()
        torch.save(result, buf)
        payload = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        # Evaluate
        accuracy = self.evaluate()
        
        return {
            "type": "result",
            "mode": mode,
            "payload": payload,
            "accuracy": accuracy
        }
    
    async def handle_server_message(self, task: Dict[str, Any]):
        """Handle messages from server"""
        task_type = task.get("type")
        
        if task_type == "assign_model":
            model_name = task["model_name"].lower()
            success = await self.load_model(model_name)
            
            if success:
                await self.send_status("idle", model_name)
            else:
                await self.ws.send(json.dumps({
                    "type": "error",
                    "msg": f"Failed to load model {model_name}"
                }))
        
        elif task_type == "update_model":
            # Update model with weights from server
            buf = io.BytesIO(base64.b64decode(task["payload"]))
            weights = torch.load(buf, map_location=self.device)
            
            for param, weight in zip(self.model.parameters(), weights):
                param.data.copy_(weight)
            
            logger.info("Model updated from global weights")
        
        elif task_type == "train":
            mode = task.get("mode", "federated")
            await self.send_status("working")
            
            # Train and send results
            result = await self.train_epoch(mode)
            await self.ws.send(json.dumps(result))
            
            # Update status
            await self.send_status("idle")
    
    async def run(self):
        """Main worker loop"""
        if not await self.connect():
            return
        
        try:
            async for message in self.ws:
                task = json.loads(message)
                await self.handle_server_message(task)
                
        except websockets.ConnectionClosed:
            logger.info("Disconnected from server")
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
        finally:
            if self.ws:
                await self.ws.close()

def main():
    """Entry point for worker"""
    worker = ChekMLWorker()
    asyncio.run(worker.run())

if __name__ == "__main__":
    main()
