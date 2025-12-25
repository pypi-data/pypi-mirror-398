import asyncio, json, base64, io, torch, os, sys
from collections import defaultdict
from aiohttp import web
import importlib.util
import glob
import logging
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .models import ModelRegistry
    from .aggregation import AggregationRegistry, FederatedAggregation, DistributedAggregation, HybridAggregation
    from .utils import GoogleDriveClient
    from .config import Config
except ImportError:
    from models import ModelRegistry
    from aggregation import AggregationRegistry, FederatedAggregation, DistributedAggregation, HybridAggregation
    from utils import GoogleDriveClient
    from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ChekMLServer:
    def __init__(self, config_path: str = None):
        # initialize basic components required by methods below
        self.config = Config(config_path)
        self.model_registry = ModelRegistry()
        self.aggregation_registry = AggregationRegistry()
        self.google_drive_client = None

        # Register built-in aggregations if available
        try:
            self.aggregation_registry.register('federated', FederatedAggregation())
            self.aggregation_registry.register('distributed', DistributedAggregation())
            self.aggregation_registry.register('hybrid', HybridAggregation())
        except Exception:
            # ignore if aggregation classes aren't available
            pass

        # State holders
        self.workers = {}
        self.global_models = {}
        self.ongoing_aggregations = {}

        # Load plugins and drive client if present
        try:
            if hasattr(self, '_load_custom_aggregations'):
                self._load_custom_aggregations()
        except Exception:
            pass

        try:
            if hasattr(self, '_init_google_drive'):
                self._init_google_drive()
        except Exception:
            pass
        # Add these methods to your ChekMLServer class

    def _load_custom_aggregations(self):
        """Load custom aggregation methods from plugins directory (package-relative)."""
        try:
            from aggregation.base import AggregationMethod
        except Exception:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        plugins_dir = os.path.join(base_dir, self.config.plugins_dir)
        if not os.path.isdir(plugins_dir):
            logger.debug(f"Plugins dir not found: {plugins_dir}")
            return

        for py_file in glob.glob(os.path.join(plugins_dir, "*.py")):
            try:
                module_name = os.path.splitext(os.path.basename(py_file))[0]
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # explicit registration function
                if hasattr(module, 'register_aggregations'):
                    try:
                        module.register_aggregations(self.aggregation_registry)
                        logger.info(f"Loaded aggregations from {module_name} via register_aggregations")
                    except Exception as e:
                        logger.warning(f"Plugin {module_name} register_aggregations failed: {e}")

                # Auto-discover AggregationMethod subclasses
                import re
                for name, obj in vars(module).items():
                    try:
                        if isinstance(obj, type) and issubclass(obj, AggregationMethod) and obj is not AggregationMethod:
                            instance = obj()
                            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', getattr(obj, '__name__', name))
                            reg_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
                            self.aggregation_registry.register(reg_name, instance)
                            logger.info(f"Auto-registered aggregation '{reg_name}' from {module_name}")
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Failed to load plugin {py_file}: {e}")
    async def index(self, request):
        """Main web interface with full controls"""
        import json

        # Header
        body = f"""
        <html>
        <head>
            <title>ChekML Control Panel</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .worker {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .controls {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                button {{ padding: 8px 15px; margin: 5px; cursor: pointer; }}
                select, input {{ padding: 5px; margin: 5px; }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
        <h1>ChekML Control Panel</h1>
        <h2>Connected Workers: {len(self.workers)}</h2>
        """

        # Worker list
        for worker_id, info in self.workers.items():
            status = info.get('status', 'idle')
            model = info.get('model', 'none')
            device = info.get('device', 'unknown')
            history = info.get('history', [])
            last_acc = history[-1] if history else 0.0

            body += f"""
            <div class="worker">
                <h3>{worker_id}: {status} | Model: {model} | Device: {device} | Last Acc: {last_acc:.4f}</h3>
                <form method="POST" action="/assign" style="display:inline;">
                    <input type="hidden" name="worker_id" value="{worker_id}">
                    <select name="model_name">
            """

            # worker model options
            for m in self.list_available_models():
                mname = m.get('name')
                sel = 'selected' if model == mname else ''
                body += f'<option value="{mname}" {sel}>{mname}</option>'

            body += """
                    </select>
                    <button type="submit">Assign Model</button>
                </form>
            """

            if info.get('last_result') and info['last_result'].get('mode') == 'federated':
                body += f"""
                <form method="POST" action="/save_worker" style="display:inline;">
                    <input type="hidden" name="worker_id" value="{worker_id}">
                    <button type="submit">Save Worker Model</button>
                </form>
                """

            # chart
            if history:
                rounds = list(range(1, len(history) + 1))
                body += f"""
                <div style="width:400px;height:200px;">
                    <canvas id="chart_{worker_id}"></canvas>
                </div>
                <script>
                new Chart(document.getElementById('chart_{worker_id}').getContext('2d'), {{
                    type: 'line',
                    data: {{ labels: {json.dumps(rounds)}, datasets: [{{ label: 'Accuracy', data: {json.dumps(history)}, borderColor: 'rgb(75,192,192)', tension:0.1 }}] }},
                    options: {{ scales: {{ y: {{ beginAtZero:true, max:1 }} }} }}
                }});
                </script>
                """

            body += "</div>"

        # Aggregation and training controls
        body += """
        <div class="controls">
            <h2>Training Controls</h2>
            <form method="POST" action="/command">
                <label><strong>Model:</strong></label>
        """

        # model select
        body += '<select name="model_name">'
        for m in self.list_available_models():
            body += f'<option value="{m.get("name")}">{m.get("name")} ({m.get("source","")})</option>'
        body += '</select><br><br>'

        # mode select
        body += """
                <label><strong>Mode:</strong></label>
                <select name="mode">
                    <option value="federated">Federated Learning</option>
                    <option value="distributed">Distributed Learning</option>
                    <option value="hybrid">Federated-Distributed Hybrid</option>
                </select><br><br>

                <label><strong>Aggregation:</strong></label>
        """

        # aggregation select
        body += '<select name="aggregation">'
        for agg in self.aggregation_registry.list():
            body += f'<option value="{agg}">{agg}</option>'
        body += '</select><br><br>'

        body += """
                <button type="submit" style="background:#4CAF50;color:white;padding:10px 20px;">Start Training</button>
            </form>
        </div>
        """

        # available models list
        body += """
        <h2>Available Models</h2>
        <ul>
        """
        for model_info in self.list_available_models():
            name = model_info.get('name')
            source = model_info.get('source', 'unknown')
            body += f'<li>{name} ({source}) '
            body += f'<form method="POST" action="/load_model" style="display:inline;margin-left:10px;"><input type="hidden" name="model_name" value="{name}"><button type="submit">Load</button></form></li>'

        body += """
        </ul>

        <script>
        setInterval(function(){ if(window.location.pathname === '/') location.reload(); }, 10000);
        </script>
        </body>
        </html>
        """

        return web.Response(text=body, content_type='text/html')
    async def load_model(self, request):
        """Load a model from Google Drive (or do local import) and set as global model if possible."""
        data = await request.post()
        model_name = data.get('model_name')
        if not model_name:
            return web.Response(text='Missing model_name', status=400)

        # If model already present, no-op
        if model_name in self.global_models:
            return web.Response(text=f'Model {model_name} already loaded', status=200)

        # Try local first
        local = self.model_registry.list_local_models()
        if model_name in local:
            # local model code available on server; we don't instantiate here
            return web.Response(text=f'Local model {model_name} is available on server', status=200)

        # Try Google Drive
        if not self.google_drive_client:
            return web.Response(text='Google Drive not configured on server', status=400)

        try:
            content = self.google_drive_client.download_model(model_name)
            if not content:
                return web.Response(text=f'Model {model_name} not found on Drive', status=404)

            # Try to load as torch weights
            try:
                buf = io.BytesIO(content)
                weights = torch.load(buf, map_location='cpu')
                self.global_models[model_name] = weights
                return web.Response(text=f'Model {model_name} loaded into global models (weights)', status=200)
            except Exception:
                # Not a weights file; assume Python source, save to disk for workers
                models_dir = os.path.join(os.getcwd(), 'drive_models')
                os.makedirs(models_dir, exist_ok=True)
                path = os.path.join(models_dir, f"{model_name}.py")
                with open(path, 'wb') as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    else:
                        f.write(content.encode())
                # Register location with model_registry (so workers can fetch if needed)
                # Try to import the saved module and register any nn.Module classes
                try:
                    spec = importlib.util.spec_from_file_location(f"drive_model_{model_name}", path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    imported = False
                    for name, obj in vars(mod).items():
                        try:
                            if isinstance(obj, type) and issubclass(obj, torch.nn.Module) and obj is not torch.nn.Module:
                                self.model_registry.local_models[name.lower()] = obj
                                logger.info(f"Registered drive model class {name} as local model")
                                imported = True
                        except Exception:
                            continue
                    if not imported:
                        # fallback: keep the file available for workers to download
                        logger.info(f"Saved model source {path} but no nn.Module class found inside")
                except Exception as e:
                    logger.error(f"Failed to import saved model {path}: {e}")

                return web.Response(text=f'Model source {model_name}.py saved to {path}', status=200)
        except Exception as e:
            logger.error(f"Failed to load model {model_name} from Drive: {e}")
            return web.Response(text=f'Error loading model: {e}', status=500)

    async def download_model(self, request):
        """Serve a model file to workers: either saved python source in drive_models/ or weights in global_models."""
        name = request.match_info.get('name')
        # Check for saved source file
        src_path = os.path.join(os.getcwd(), 'drive_models', f"{name}.py")
        if os.path.exists(src_path):
            return web.FileResponse(path=src_path, headers={'Content-Type': 'text/plain'})

        # Check if weights present in global_models
        if name in self.global_models:
            buf = io.BytesIO()
            torch.save(self.global_models[name], buf)
            buf.seek(0)
            return web.Response(body=buf.getvalue(), content_type='application/octet-stream')

        return web.Response(text='Model not found', status=404)
    async def command(self, request):
        """Handle training commands"""
        data = await request.post()
        model_name = data.get("model_name", "simplecnn")
        mode = data.get("mode", "federated")
        aggregation = data.get("aggregation")

        count = await self.start_training(model_name, mode, aggregation)

        html = f"""
        <html><body style="font-family: Arial; padding: 20px;">
            <h1>✅ Training Started</h1>
            <p><strong>Model:</strong> {model_name}</p>
            <p><strong>Mode:</strong> {mode}</p>
            <p><strong>Aggregation:</strong> {aggregation or mode}</p>
            <p><strong>Workers:</strong> {count} workers started training</p>
            <p><a href="/">← Back to Control Panel</a></p>
            <script>
            // Redirect back after 3 seconds
            setTimeout(function() {{ window.location.href = '/'; }}, 3000);
            </script>
        </body></html>
        """
        return web.Response(text=html, content_type="text/html")

    async def assign(self, request):
        """Assign model to worker"""
        data = await request.post()
        worker_id = data.get("worker_id")
        model_name = data.get("model_name")

        html = ""
        if worker_id in self.workers:
            try:
                await self.workers[worker_id]["ws"].send_json({
                    "type": "assign_model",
                    "model_name": model_name
                })
                self.workers[worker_id]["model"] = model_name
                logger.info(f"Assigned {model_name} to {worker_id}")
                html = f"""
                <html><body style="font-family: Arial; padding: 20px;">
                    <h1>✅ Model Assigned</h1>
                    <p>Assigned <strong>{model_name}</strong> to <strong>{worker_id}</strong></p>
                    <p><a href="/">← Back to Control Panel</a></p>
                </body></html>
                """
            except Exception as e:
                html = f"""
                <html><body style="font-family: Arial; padding: 20px;">
                    <h1>❌ Assignment Failed</h1>
                    <p>Error: {e}</p>
                    <p><a href="/">← Back to Control Panel</a></p>
                </body></html>
                """
        else:
            html = f"""
            <html><body style="font-family: Arial; padding: 20px;">
                <h1>❌ Worker Not Found</h1>
                <p>Worker {worker_id} is not connected</p>
                <p><a href="/">← Back to Control Panel</a></p>
            </body></html>
            """

        return web.Response(text=html, content_type="text/html")

    async def save_worker(self, request):
        """Save worker model"""
        data = await request.post()
        worker_id = data.get("worker_id")
        
        html = f"""
        <html><body>
            <h1>Save Worker Model</h1>
            <p>Worker save functionality placeholder.</p>
            <p><a href="/">Back to dashboard</a></p>
        </body></html>
        """
        return web.Response(text=html, content_type="text/html")
    
    async def save_aggregated(self, request):
        """Save aggregated model"""
        data = await request.post()
        model_name = data.get("model_name")
        
        html = f"""
        <html><body>
            <h1>Save Aggregated Model</h1>
            <p>Aggregated save functionality placeholder.</p>
            <p><a href="/">Back to dashboard</a></p>
        </body></html>
        """
        return web.Response(text=html, content_type="text/html")

    async def handle_websocket(self, request):
        """Handle WebSocket connections from workers"""
        ws = web.WebSocketResponse(max_msg_size=0)
        await ws.prepare(request)
        
        worker_id = f"worker_{len(self.workers) + 1}"
        self.workers[worker_id] = {
            "ws": ws,
            "status": "idle",
            "model": None,
            "device": "unknown",
            "history": [],
            "last_result": None
        }
        
        logger.info(f"[+] {worker_id} connected")
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self._handle_worker_message(worker_id, msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"[!] {worker_id} closed with exception: {ws.exception()}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler for {worker_id}: {e}")
        finally:
            logger.info(f"[-] {worker_id} disconnected")
            self.workers.pop(worker_id, None)
        
        return ws
    
    async def _handle_worker_message(self, worker_id: str, message: str):
        """Process messages from workers"""
        data = json.loads(message)
        msg_type = data.get("type")
        
        if msg_type == "status":
            await self._handle_status_update(worker_id, data)
        elif msg_type == "initial_weights":
            await self._handle_initial_weights(worker_id, data)
        elif msg_type == "result":
            await self._handle_training_result(worker_id, data)
        elif msg_type == "error":
            logger.error(f"Error from {worker_id}: {data.get('msg')}")
    
    async def _handle_status_update(self, worker_id: str, data: dict):
        """Handle worker status updates"""
        self.workers[worker_id]["status"] = data["status"]
        if "model" in data:
            self.workers[worker_id]["model"] = data["model"]
        if "device" in data:
            self.workers[worker_id]["device"] = data["device"]
        logger.info(f"[=] {worker_id}: {data['status']}, model: {data.get('model', 'none')}")
    
    async def _handle_initial_weights(self, worker_id: str, data: dict):
        """Handle initial weights from worker"""
        model_name = data["model"]
        if model_name not in self.global_models:
            buf = io.BytesIO(base64.b64decode(data["payload"]))
            weights = torch.load(buf, map_location="cpu")
            self.global_models[model_name] = weights
            logger.info(f"[=] Set initial global model for {model_name}")
    
    async def _handle_training_result(self, worker_id: str, data: dict):
        """Handle training results from workers"""
        self.workers[worker_id]["status"] = "idle"
        
        # Decode result
        buf = io.BytesIO(base64.b64decode(data["payload"]))
        result = torch.load(buf, map_location="cpu")
        
        self.workers[worker_id]["last_result"] = {
            "mode": data["mode"],
            "result": result
        }
        
        if "accuracy" in data:
            accuracy = float(data["accuracy"])
            self.workers[worker_id]["history"].append(accuracy)
            logger.info(f"[✓] {worker_id} accuracy: {accuracy:.4f}")
        
        # Trigger aggregation if needed
        model_name = self.workers[worker_id]["model"]
        if model_name in self.ongoing_aggregations:
            await self._aggregate_results(model_name, result, data["mode"])
    
    async def _aggregate_results(self, model_name: str, result: Any, mode: str):
        """Aggregate results from multiple workers"""
        agg_info = self.ongoing_aggregations[model_name]
        agg_info["received"] += 1
        agg_info["results"].append(result)
        
        if agg_info["received"] == agg_info["expected"]:
            # Get aggregation method
            aggregation_name = agg_info.get("aggregation", mode)
            aggregator = self.aggregation_registry.get(aggregation_name)
            
            if aggregator:
                current_weights = self.global_models.get(model_name)
                new_weights = aggregator.aggregate(current_weights, agg_info["results"], agg_info.get("config", {}))
                self.global_models[model_name] = new_weights
                logger.info(f"[=] Aggregated {model_name} using {aggregation_name}")
            
            # Save to Google Drive if enabled
            if self.google_drive_client:
                try:
                    await self._save_model_to_drive(model_name)
                except Exception as e:
                    logger.error(f"Failed to save model to Google Drive: {e}")
            
            del self.ongoing_aggregations[model_name]
    
    async def _save_model_to_drive(self, model_name: str):
        """Save model to Google Drive"""
        if model_name in self.global_models:
            buf = io.BytesIO()
            torch.save(self.global_models[model_name], buf)
            self.google_drive_client.save_model(model_name, buf.getvalue())
            logger.info(f"[=] Saved {model_name} to Google Drive")
    
    def list_available_models(self):
        """List all available models"""
        models = []
        
        # Local models
        for model_name in self.model_registry.list_local_models():
            models.append({
                "name": model_name,
                "type": "local",
                "source": "model.py"
            })
        
        # Google Drive models
        if self.google_drive_client:
            try:
                drive_models = self.google_drive_client.list_models()
                for model_name in drive_models:
                    models.append({
                        "name": model_name,
                        "type": "drive",
                        "source": "Google Drive"
                    })
            except Exception:
                pass
        
        return models
    
    async def start_training(self, model_name: str, mode: str = "federated", 
                           aggregation: str = None, config: dict = None):
        """Start training task for all idle workers with the specified model"""
        if model_name not in self.global_models:
            logger.error(f"No global model for {model_name}")
            return 0
        
        # Prepare global weights
        buf = io.BytesIO()
        torch.save(self.global_models[model_name], buf)
        payload = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        # Count eligible workers
        eligible_workers = []
        for worker_id, info in self.workers.items():
            if info["model"] == model_name and info["status"] == "idle":
                eligible_workers.append(worker_id)
        
        if not eligible_workers:
            return 0
        
        # Send training tasks
        for worker_id in eligible_workers:
            ws = self.workers[worker_id]["ws"]
            await ws.send_json({"type": "update_model", "payload": payload})
            await ws.send_json({"type": "train", "mode": mode})
            self.workers[worker_id]["status"] = "working"
        
        # Setup aggregation tracking
        aggregation_name = aggregation or mode
        self.ongoing_aggregations[model_name] = {
            "mode": mode,
            "aggregation": aggregation_name,
            "expected": len(eligible_workers),
            "received": 0,
            "results": [],
            "config": config or {}
        }
        
        logger.info(f"[=] Started {mode} training for {model_name} with {len(eligible_workers)} workers")
        return len(eligible_workers)
    
    def register_custom_aggregation(self, name: str, aggregator):
        """Register a custom aggregation method"""
        self.aggregation_registry.register(name, aggregator)

    async def _watch_local_models(self):
        """Background task: rescan local_models periodically to pick up new files."""
        while True:
            try:
                # Rebuild local model registry
                try:
                    self.model_registry._load_local_models()
                except Exception as e:
                    logger.warning(f"Local model scan failed: {e}")
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(5)
    
    async def run(self):
        """Run the server"""
        app = web.Application()
        
        # Setup ALL routes (not just /ws)
        app.router.add_get("/", self.index)
        app.router.add_get("/ws", self.handle_websocket)
        app.router.add_post("/load_model", self.load_model)
        app.router.add_get("/download_model/{name}", self.download_model)
        app.router.add_post("/command", self.command)
        app.router.add_post("/assign", self.assign)
        app.router.add_post("/save_worker", self.save_worker)
        app.router.add_post("/save_aggregated", self.save_aggregated)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config.host, self.config.port)
        
        logger.info(f"Server starting on {self.config.host}:{self.config.port}")
        logger.info(f"Web interface: http://{self.config.host}:{self.config.port}")
        await site.start()
        # start background watcher for local models
        try:
            self._local_watch_task = asyncio.create_task(self._watch_local_models())
        except Exception:
            self._local_watch_task = None
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        finally:
            if hasattr(self, '_local_watch_task') and self._local_watch_task:
                self._local_watch_task.cancel()
            await runner.cleanup() 
