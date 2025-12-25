import asyncio, websockets, json, os, sys, importlib.util, inspect
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
        self.config = WorkerConfig(config_path)
        self.model_loader = ModelLoader()
        self.google_drive_client = None
        self.device_info = ""
        
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
        
        if model_name:
            message["model"] = model_name
        
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
