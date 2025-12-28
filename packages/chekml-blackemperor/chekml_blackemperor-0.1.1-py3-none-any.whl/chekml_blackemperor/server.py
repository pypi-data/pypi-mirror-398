import asyncio, json, base64, io, torch, os, sys, time
from collections import defaultdict
from aiohttp import web
import importlib.util
import uuid
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
        # model-tree edges: list of {from, to, aggregation, config, state}
        self.model_tree_edges = []
        self.model_tree_file = os.path.join(os.getcwd(), 'model_tree.json')

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
        # If google drive client is present, register drive models with registry for discovery
        try:
            if self.google_drive_client:
                try:
                    drive_models = self.google_drive_client.list_models() or []
                    for m in drive_models:
                        self.model_registry.register_drive_model(m, self.google_drive_client)
                        logger.info(f"Registered drive model {m} in ModelRegistry")
                except Exception as e:
                    logger.debug(f"Failed to register drive models: {e}")
        except Exception:
            pass
        # Load persisted model-tree if present
        try:
            self._load_model_tree()
        except Exception:
            pass
        # Load persisted clusters if present
        self.model_clusters = []
        self.cluster_links = []
        self.model_clusters_file = os.path.join(os.getcwd(), 'model_clusters.json')
        try:
            self._load_model_clusters()
        except Exception:
            pass
        # model-specific hyperparameter configs
        self.model_configs = {}
        self.model_configs_file = os.path.join(os.getcwd(), 'model_configs.json')
        try:
            self._load_model_configs()
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
    def _init_google_drive(self):
        """Initialize Google Drive client if configured in ServerConfig."""
        try:
            if getattr(self.config, 'google_drive_enabled', False):
                creds = getattr(self.config, 'google_drive_credentials', None)
                folder = getattr(self.config, 'google_drive_folder', 'chekml_models')
                self.google_drive_client = GoogleDriveClient(credentials_file=creds, folder_name=folder)
                logger.info("Google Drive client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive client: {e}")
    async def index(self, request):
        """Main web interface with full controls"""
        import json

        # Header (fixed HTML structure and inlined CSS)
        body = f"""
        <html>
        <head>
            <title>ChekML Control Panel</title>
            <style>
                body {{ background: #f4ecd8; font-family: Georgia, 'Times New Roman', serif; color:#2b2b2b; }}
                h1 {{ font-family: 'Palatino Linotype', Georgia, serif; color:#3b2b1f; }}
                .worker {{ border: 1px solid #d3c6a3; padding: 15px; margin: 10px 0; border-radius: 6px; background: #fffaf0; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }} 
                .controls {{ background: linear-gradient(180deg,#fbf6e6,#f4ecd8); padding: 15px; border-radius: 8px; border:1px solid #e2d4b3; }}
                button {{ padding: 8px 15px; margin: 5px; cursor: pointer; background:#8b5e3c;color:#fff;border-radius:4px;border:1px solid #6d452a; }}
                button:hover{{ opacity:0.95 }}
                select, input {{ padding: 6px; margin: 5px; border:1px solid #cdbd9a; border-radius:4px; }}
                #model_tree_container {{ background: linear-gradient(180deg,#fbf6e6,#efe6c9); padding:12px; border:1px solid #e0cfac; border-radius:8px; }}
                .node-select {{ transform: scale(1.1); }}
                h2::before, h3::before {{ content: "⚜"; margin-right:8px; color:#6d452a; font-size:18px; vertical-align:middle; }}
                .node-icon {{ display:inline-block; width:28px; height:28px; border-radius:50%; background:#e9d9b6; color:#6d452a; text-align:center; line-height:28px; margin-right:8px; border:1px solid #d1bfa0; box-shadow: inset 0 -2px 0 rgba(0,0,0,0.05); }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
        </head>
        <body>
        <h1>ChekML Control Panel</h1>
        <h2>Connected Workers: {len(self.workers)}</h2>
        """

        
        # Aggregation and training controls rendered as table with per-worker actions
        body += """
        <div class="controls">
            <h2>Training Controls</h2>
            <form id="start_all_form" method="POST" action="/command" style="margin-bottom:12px;">
                <label><strong>Model:</strong></label>
                <select name="model_name">
        """

        for m in self.list_available_models():
            body += f'<option value="{m.get("name")}">{m.get("name")} ({m.get("source","")})</option>'
        body += '</select>'
        # Start All Idle will use Model Tree rules for aggregation; Mode/Aggregation controls removed.
        body += '&nbsp;&nbsp;<button type="submit" name="action" value="start_model" style="background:#4CAF50;color:white;padding:8px 12px;">Start Selected Model Idle</button>'
        body += '&nbsp;&nbsp;<button type="submit" name="action" value="start_assigned" style="background:#2196F3;color:white;padding:8px 12px;">Start All Assigned Idle</button>'
        body += '</form>'

        # Per-worker table
        body += """
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr><th style="text-align:left;padding:6px;border-bottom:1px solid #ccc;">Worker</th><th style="text-align:left;padding:6px;border-bottom:1px solid #ccc;">Model</th><th style="text-align:left;padding:6px;border-bottom:1px solid #ccc;">Status</th><th style="text-align:left;padding:6px;border-bottom:1px solid #ccc;">Device</th><th style="text-align:left;padding:6px;border-bottom:1px solid #ccc;">Last Acc</th><th style="text-align:left;padding:6px;border-bottom:1px solid #ccc;">Actions</th></tr></thead>
                <tbody>
        """

        # render each worker as a row with assign and start buttons (start uses assigned model)
        for worker_id, info in self.workers.items():
            status = info.get('status', 'idle')
            model = info.get('model') or ''
            device = info.get('device','')
            history = info.get('history',[])
            last_acc = history[-1] if history else 0.0
            display_label = (info.get('worker_id') or worker_id) + (f" / {info.get('instance_id')}" if info.get('instance_id') else '')
            # build assign select options
            opts = ''
            for m in self.list_available_models():
                opts += f'<option value="{m.get("name")}">{m.get("name")}</option>'

            row = f'''
                <tr>
                    <td style="padding:6px;border-bottom:1px solid #eee;">{display_label}</td>
                    <td style="padding:6px;border-bottom:1px solid #eee;">{model}</td>
                    <td style="padding:6px;border-bottom:1px solid #eee;">{status}</td>
                    <td style="padding:6px;border-bottom:1px solid #eee;">{device}</td>
                    <td style="padding:6px;border-bottom:1px solid #eee;">{last_acc:.4f}</td>
                    <td style="padding:6px;border-bottom:1px solid #eee;">
                        <form method="POST" action="/assign" style="display:inline;"> 
                            <input type="hidden" name="worker_id" value="{worker_id}"> 
                            <select name="model_name">{opts}</select>
                            <button type="submit" style="margin-left:6px;">Assign</button>
                        </form>
                        <form onsubmit="startWorker(event,'{worker_id}')" style="display:inline;margin-left:6px;"> 
                            <input type="hidden" name="worker_id" value="{worker_id}"> 
                            <button type="submit" style="margin-left:6px;">Start</button>
                        </form>
                    </td>
                </tr>
            '''
            body += row

        body += """
                </tbody>
            </table>
            <script>
            async function startWorker(e, workerId){
                e.preventDefault();
                const form = e.target;
                const fm = new FormData(form);
                fm.append('worker_id', workerId);
                try{
                    const resp = await fetch('/command_worker', { method: 'POST', body: fm });
                    if(!resp.ok){ console.error('Failed to start worker', await resp.text()); }
                    else{ console.log('Started', workerId); setTimeout(()=>refreshModelTree(), 500); }
                }catch(err){ console.error(err); }
            }
            
            </script>
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

        <h2>Model Hyperparameters</h2>
        <div style="margin-bottom:12px;">
            <label>Select model:</label>
            <select id="config_model_select">
"""
        for model_info in self.list_available_models():
            name = model_info.get('name')
            body += f'<option value="{name}">{name}</option>'
        body += """
            </select>
            <button onclick="loadModelConfig()" style="margin-left:8px;">Load</button>
        </div>
        <div>
            <textarea id="model_config_text" rows="6" style="width:100%;font-family:monospace;">"""
        # initial fill with first model config if present
        if self.model_configs:
            first = next(iter(self.model_configs.keys()))
            body += json.dumps(self.model_configs.get(first, {}), indent=2)
        else:
            body += '{}'
        body += """</textarea>
            <div style="margin-top:8px;"> <label style="font-weight:600;">Model I/O (JSON):</label>
                <textarea id="model_io_text" rows="4" style="width:100%;font-family:monospace;margin-top:6px;">{}</textarea>
            </div>
            <div style="margin-top:8px;"><button onclick="saveModelConfig()">Save Hyperparameters & I/O</button></div>
        </div>

        <script>
        async function loadModelConfig(){
            const sel = document.getElementById('config_model_select');
            const name = sel.value;
            try{
                const resp = await fetch('/get_model_config?name='+encodeURIComponent(name));
                if(resp.ok){ const j = await resp.json(); document.getElementById('model_config_text').value = JSON.stringify(j, null, 2); 
                    // populate I/O textarea if available
                    const io = {};
                    if(j && (j.input_shape || j.output_shape || j.handlers)){
                        if(j.input_shape) io.input_shape = j.input_shape;
                        if(j.output_shape) io.output_shape = j.output_shape;
                        if(j.handlers) io.handlers = j.handlers;
                        document.getElementById('model_io_text').value = JSON.stringify(io, null, 2);
                    } else { document.getElementById('model_io_text').value = '{}'; }
                }
                else{ alert('No config'); document.getElementById('model_config_text').value='{}'; document.getElementById('model_io_text').value='{}'; }
            }catch(e){ alert('Failed to load config: '+e); }
        }
        async function saveModelConfig(){
            const sel = document.getElementById('config_model_select');
            const name = sel.value;
            let txt = document.getElementById('model_config_text').value;
            let io_txt = document.getElementById('model_io_text').value;
            // merge I/O JSON into config JSON
            let cfg_obj = {};
            try{ cfg_obj = JSON.parse(txt || '{}'); }catch(e){ alert('Invalid JSON in hyperparameters'); return; }
            try{ const io_obj = JSON.parse(io_txt || '{}'); Object.assign(cfg_obj, io_obj); }catch(e){ alert('Invalid JSON in Model I/O'); return; }
            const fm = new FormData(); fm.append('name', name); fm.append('config', JSON.stringify(cfg_obj));
            const r = await fetch('/set_model_config', { method:'POST', body: fm });
            if(r.ok){ alert('Saved'); try{ await refreshModelTree(); }catch(e){} } else { alert('Save failed: '+ await r.text()); }
        }
        </script>

        <h3>Model I/O Shapes</h3>
        <div id="model_io_div" style="font-family:monospace;white-space:pre-wrap;background:#fffaf0;padding:8px;border:1px solid #e2d4b3;border-radius:6px;margin-bottom:12px;">
        </div>
        <script>
        (function(){
            try{
                const configs = __MODEL_CONFIGS_JSON__;
                const el = document.getElementById('model_io_div');
                let out = '';
                Object.keys(configs||{}).forEach(k=>{
                    const c = configs[k] || {};
                    out += `Model: ${k}\n`;
                    if(c.input_shape) out += `  input_shape: ${JSON.stringify(c.input_shape)}\n`;
                    if(c.output_shape) out += `  output_shape: ${JSON.stringify(c.output_shape)}\n`;
                    if(c.handlers) out += `  handlers: ${JSON.stringify(c.handlers)}\n`;
                    out += '\n';
                });
                if(!out) out = '(no models registered with I/O shapes)';
                el.innerText = out;
            }catch(e){ console.warn('Failed to render model I/O shapes', e); }
        })();
        </script>

        <h2>Model Tree</h2>
        <div id="datasets_panel" style="margin-bottom:12px;padding:8px;border:1px solid #e0cfac;border-radius:6px;background:#fffef8;">
            <!-- persistent Datasets panel (updated in-place) -->
            <h3 style="margin:0 0 6px 0;">Datasets</h3>
            <div id="drive_datasets_list">(loading datasets...)</div>
            <div id="worker_datasets_list" style="margin-top:8px;">(loading worker dataset statuses...)</div>
        </div>
        <div id="model_tree_container" style="position:relative;min-height:240px;display:flex;gap:12px;flex-wrap:wrap;">
            <!-- nodes will be injected here -->
        </div>

        <div style="margin-top:12px;">
            <!-- Link creation UI hidden per user preference; kept in DOM (hidden) so JS can populate selects if needed -->
            <form id="add_edge" method="POST" action="/model_tree" style="display:none;gap:8px;align-items:center;">
                <label>From:</label>
                <select name="from_node" id="from_node"></select>
                <label>To:</label>
                <select name="to_node" id="to_node"></select>
                <label>Aggregation:</label>
                <select name="aggregation" id="edge_aggregation"></select>
                <input name="config" id="edge_config" placeholder='{"weights":[1,1]}' style="width:200px;">
                <button type="submit">Add Link</button>
            </form>
        </div>

        <!-- Aggregation controls moved into Cluster workflow below -->

        <script>
        async function refreshModelTree(){
            try{
                const resp = await fetch('/model_tree');
                const data = await resp.json();
                const container = document.getElementById('model_tree_container');
                // if user is actively editing inside the container, skip refresh to avoid wiping edits
                const active = document.activeElement;
                if(active && container.contains(active)){
                    console.log('Skipping model tree refresh; user is editing');
                    return;
                }
                container.innerHTML = '';

                // populate selects
                const fromSel = document.getElementById('from_node');
                const toSel = document.getElementById('to_node');
                const aggSel = document.getElementById('edge_aggregation');
                fromSel.innerHTML = '';
                toSel.innerHTML = '';
                aggSel.innerHTML = '';

                data.nodes.forEach(n=>{
                    const div = document.createElement('div');
                    div.style.border='1px solid #ccc';
                    div.style.padding='8px';
                    div.style.width='180px';
                    div.style.borderRadius='6px';
                    // color by status
                    const color = n.status==='working'?'#FFA500':(n.status==='idle'?'#ddd':(n.status==='done'?'#8BC34A':'#f44336'));
                    div.style.background=color;
                    const displayPid = n.worker_id ? `${n.worker_id}` : '';
                    const displayInst = n.instance_id ? ` / ${n.instance_id}` : '';
                    // set a safe DOM id for layout calculations
                    const safeId = ('node_'+n.id).replace(/[^a-zA-Z0-9_-]/g,'_');
                    div.id = safeId;
                    div.style.minWidth = '180px';
                    // status badge color mapping
                    const statusColor = n.status==='working' ? '#FFA500' : (n.status==='idle' ? '#ddd' : (n.status==='done' ? '#8BC34A' : '#f44336'));
                    // include a selection checkbox for joining
                    // include dataset info if available
                    const dsinfo = n.dataset || {};
                    let dsHtml = '';
                    try{
                        if(dsinfo && dsinfo.name){
                            const dtype = dsinfo.dtype ? dsinfo.dtype : '';
                            const xsh = dsinfo.x_shape ? JSON.stringify(dsinfo.x_shape) : '';
                            const ysh = dsinfo.y_shape ? JSON.stringify(dsinfo.y_shape) : '';
                            dsHtml = `<div style="margin-top:6px;color:#333;font-size:13px;"><strong>dataset:</strong> ${dsinfo.name} ${dsinfo.source?('('+dsinfo.source+')'):''} ${dtype?(' dtype:'+dtype):''} ${xsh?(' x:'+xsh):''} ${ysh?(' y:'+ysh):''}</div>`;
                        }
                    }catch(e){ dsHtml = ''; }

                    div.innerHTML = `<input type="checkbox" class="node-select" data-nodeid="${n.id}" style="position:absolute;right:8px;top:8px;">` +
                                    `<strong style="display:block;margin-bottom:4px">${n.id}</strong><div><span style="display:inline-block;width:10px;height:10px;background:${statusColor};border-radius:50%;margin-right:6px;vertical-align:middle;"></span><strong>status:</strong> ${n.status}</div><div><strong>pid:</strong> ${displayPid}${displayInst}</div><div>model: ${n.model}</div><div>device: ${n.device}</div><div>acc: ${n.last_accuracy.toFixed(3)}</div>` + dsHtml;
                    // make container relative to allow absolute checkbox inside
                    div.style.position='relative';
                    // add Save Trained Model button (per-instance)
                    try{
                        const saveBtn = document.createElement('button'); saveBtn.innerText = 'Save Trained Model'; saveBtn.style.marginTop='8px';
                        saveBtn.onclick = async ()=>{
                            if(!confirm('Save latest trained model from '+(n.worker_id||n.id)+'?')) return;
                            const fm = new FormData(); fm.append('worker_id', n.id);
                            const resp = await fetch('/save_worker', { method:'POST', body: fm });
                            if(resp.ok){ alert('Saved worker model'); refreshModelTree(); } else { alert('Save failed: '+ await resp.text()); }
                        };
                        div.appendChild(saveBtn);
                    }catch(e){}
                    container.appendChild(div);
                    // add small sparkline for history if available (inline)
                    try{
                        const hist = Array.isArray(n.history) ? n.history : [];
                        if(hist.length){
                            const cvs = document.createElement('canvas');
                            cvs.width = 160; cvs.height = 40; cvs.style.display='block'; cvs.style.marginTop='6px';
                            div.appendChild(cvs);
                            try{
                                new Chart(cvs.getContext('2d'), {
                                    type: 'line',
                                    data: { labels: hist.map((_,i)=>i+1), datasets: [{ data: hist, fill: false, borderColor: '#1976d2', tension: 0.3, pointRadius:0 }] },
                                    options: { responsive: false, plugins: { legend: { display: false } }, scales: { x: { display:false }, y: { display:false } }, elements: { line: { borderWidth: 2 } } }
                                });
                            }catch(err){ console.error('chart failed', err); }
                        }
                    }catch(err){ /* ignore sparkline errors */ }

                    // (no hover tooltips by user request)

                    const opt1 = document.createElement('option'); opt1.value = n.id; opt1.text = (n.worker_id || n.id) + (n.instance_id ? (' ('+n.instance_id+')') : ''); fromSel.appendChild(opt1);
                    const opt2 = document.createElement('option'); opt2.value = n.id; opt2.text = (n.worker_id || n.id) + (n.instance_id ? (' ('+n.instance_id+')') : ''); toSel.appendChild(opt2);
                });

                // edges exist in model_tree but edge-level aggregation UI is hidden per user preference

                // render clusters list and controls
                const clustersDivId = 'clusters_list_div';
                let clustersDiv = document.getElementById(clustersDivId);
                if(clustersDiv) clustersDiv.remove();
                clustersDiv = document.createElement('div');
                clustersDiv.id = clustersDivId;
                clustersDiv.style.marginTop = '12px';
                clustersDiv.style.padding = '8px';
                clustersDiv.style.borderTop = '1px dashed #cdbd9a';
                const clusterHeader = document.createElement('div');
                clusterHeader.innerHTML = '<h3>Clusters</h3>';
                clustersDiv.appendChild(clusterHeader);

                // create cluster controls
                const createDiv = document.createElement('div');
                createDiv.style.display='flex'; createDiv.style.gap='8px'; createDiv.style.alignItems='center';
                const nameInput = document.createElement('input'); nameInput.placeholder='cluster_name'; nameInput.id='create_cluster_name';
                const createBtn = document.createElement('button'); createBtn.innerText='Create Cluster from Selected'; createBtn.onclick = async function(){
                    const checked = Array.from(document.querySelectorAll('.node-select')).filter(c=>c.checked).map(c=>c.dataset.nodeid);
                    if(!checked.length){ alert('No nodes selected'); return; }
                    const fm = new FormData(); fm.append('nodes', checked.join(',')); fm.append('name', document.getElementById('create_cluster_name').value || '');
                    const r = await fetch('/create_cluster', { method:'POST', body: fm });
                    if(r.ok){ alert('Cluster created'); refreshModelTree(); } else { alert('Create failed: '+ await r.text()); }
                };
                createDiv.appendChild(nameInput); createDiv.appendChild(createBtn);
                // combined clusters save control
                const combineDiv = document.createElement('div'); combineDiv.style.marginTop='8px'; combineDiv.style.display='flex'; combineDiv.style.gap='8px';
                const combineBtn = document.createElement('button'); combineBtn.innerText='Save Combined Clusters (selected)';
                combineBtn.onclick = async ()=>{
                    const checked = Array.from(document.querySelectorAll('.cluster-checkbox')).filter(c=>c.checked).map(c=>c.dataset.clusterid);
                    if(!checked.length){ alert('No clusters selected'); return; }
                    // collect nodes from selected clusters
                    const selectedClusters = data.clusters.filter(c=>checked.includes(c.id));
                    const nodes = [].concat(...selectedClusters.map(c=>c.members||[]));
                    if(!nodes.length){ alert('No nodes in selected clusters'); return; }
                    const agg = prompt('Aggregation (name):','federated') || 'federated';
                    const saveName = prompt('Save name (optional):','') || '';
                    const fm = new FormData(); fm.append('nodes', nodes.join(',')); fm.append('aggregation', agg); if(saveName) fm.append('save_name', saveName);
                    const r = await fetch('/join_nodes', { method:'POST', body: fm });
                    if(r.ok){ alert('Combined saved'); refreshModelTree(); } else { alert('Save failed: '+await r.text()); }
                };
                combineDiv.appendChild(combineBtn);
                clustersDiv.appendChild(combineDiv);
                clustersDiv.appendChild(createDiv);

                // list clusters
                const listDiv = document.createElement('div'); listDiv.style.marginTop='8px';
                (data.clusters||[]).forEach(c=>{
                    const cdiv = document.createElement('div'); cdiv.style.padding='6px'; cdiv.style.border='1px solid #d0c2a0'; cdiv.style.margin='6px 0';
                    cdiv.innerHTML = `<input type="checkbox" class="cluster-checkbox" data-clusterid="${c.id}" style="margin-right:8px;">` +
                                     `<strong>${c.name}</strong> <span style="color:#666;margin-left:8px;font-size:12px;">(${c.id})</span> <em style="margin-left:8px;color:#2b6e2b">status: ${c.status||'unknown'}</em><div style="font-size:12px;color:#333;margin-top:6px;">Members: ${ (c.members||[]).join(', ') }</div>`;
                    // show mode (online/offline) if cluster config present
                    try{
                        const mode = (c.config && c.config.online_aggregation) ? 'online' : 'offline';
                        const modeDiv = document.createElement('div'); modeDiv.style.marginTop='6px'; modeDiv.style.fontSize='13px'; modeDiv.innerHTML = `<strong>mode:</strong> ${mode}`;
                        cdiv.appendChild(modeDiv);
                    }catch(e){}
                    // remove linking UI per user request; provide delete button instead
                    const deleteBtn = document.createElement('button'); deleteBtn.innerText='Delete'; deleteBtn.style.marginLeft='8px'; deleteBtn.style.background='#c63c3c';
                    deleteBtn.onclick = async ()=>{
                        if(!confirm('Delete cluster "'+c.name+'"?')) return;
                        const fm = new FormData(); fm.append('id', c.id);
                        const r = await fetch('/delete_cluster', { method:'POST', body: fm });
                        if(r.ok){ alert('Deleted'); refreshModelTree(); } else { alert('Delete failed: '+await r.text()); }
                    };
                    // aggregation select + config + save button for this cluster
                    const sel = document.createElement('select'); sel.style.marginLeft='8px';
                    data.available_aggregations.forEach(a=>{ const o=document.createElement('option'); o.value=a; o.text=a; sel.appendChild(o); });
                    const cfg = document.createElement('input'); cfg.placeholder='{}'; cfg.style.marginLeft='8px'; cfg.style.width='180px';
                    const saveBtn = document.createElement('button'); saveBtn.innerText='Save Cluster Model'; saveBtn.style.marginLeft='8px';
                    saveBtn.onclick = async ()=>{
                        const saveName = prompt('Save name for cluster model (optional):','') || '';
                        const fm = new FormData(); fm.append('target', c.id); fm.append('aggregation', sel.value); fm.append('config', cfg.value || '{}'); if(saveName) fm.append('save_name', saveName);
                        const r = await fetch('/aggregate_flow', { method:'POST', body: fm }); if(r.ok){ alert('Cluster aggregated'); refreshModelTree(); } else { alert('Aggregate failed: '+await r.text()); }
                    };
                    cdiv.appendChild(deleteBtn);
                    // disable online aggregation button if enabled
                    try{
                        if(c.config && c.config.online_aggregation){
                            const disableBtn = document.createElement('button'); disableBtn.innerText='Disable Online'; disableBtn.style.marginLeft='8px'; disableBtn.style.background='#b05b5b';
                            disableBtn.onclick = async ()=>{
                                if(!confirm('Disable online aggregation for cluster '+c.name+'?')) return;
                                const fm = new FormData(); fm.append('id', c.id); fm.append('config', JSON.stringify({online_aggregation:false}));
                                const r = await fetch('/set_cluster_config', { method:'POST', body: fm });
                                if(r.ok){ alert('Disabled online aggregation'); refreshModelTree(); } else { alert('Failed: '+await r.text()); }
                            };
                            cdiv.appendChild(disableBtn);
                        }
                    }catch(e){}
                    cdiv.appendChild(sel); cdiv.appendChild(cfg); cdiv.appendChild(saveBtn);
                    // Train Cluster button (only this button triggers cluster training)
                    try{
                        const trainBtn = document.createElement('button'); trainBtn.innerText = 'Train Cluster'; trainBtn.style.marginLeft='8px'; trainBtn.style.background='#2b6ea3';
                        trainBtn.onclick = async ()=>{
                            const modelName = prompt('Model name to train for this cluster (required):','');
                            if(!modelName){ alert('Model name required'); return; }
                            const agg = prompt('Aggregation method (optional):','federated') || 'federated';
                            if(!confirm('Start cluster training for '+c.name+' on model '+modelName+'?')) return;
                            const fm = new FormData(); fm.append('id', c.id); fm.append('model_name', modelName); fm.append('aggregation', agg);
                            const r = await fetch('/train_cluster', { method:'POST', body: fm });
                            if(r.ok){ alert('Cluster training started'); refreshModelTree(); } else { alert('Train failed: '+ await r.text()); }
                        };
                        cdiv.appendChild(trainBtn);
                    }catch(e){}
                    listDiv.appendChild(cdiv);
                });
                clustersDiv.appendChild(listDiv);
                container.appendChild(clustersDiv);

                // Advanced Aggregation: allow enabling online aggregation for a selected model
                const advDivId = 'advanced_aggregation_div';
                let advDiv = document.getElementById(advDivId);
                if(advDiv) advDiv.remove();
                advDiv = document.createElement('div'); advDiv.id = advDivId; advDiv.style.marginTop='12px'; advDiv.style.padding='8px';
                advDiv.innerHTML = '<h3>Advanced Aggregation</h3><div style="margin-bottom:8px;">Enable online aggregation (during training) for a specific cluster. Select cluster and aggregator, then click Enable.</div>';
                const clusterSel = document.createElement('select'); clusterSel.id='adv_cluster_select'; clusterSel.style.marginRight='8px';
                (data.clusters||[]).forEach(c=>{ const o=document.createElement('option'); o.value=c.id; o.text=c.name+' ('+c.id+')'; clusterSel.appendChild(o); });
                const aggSel2 = document.createElement('select'); aggSel2.id='adv_agg_select'; aggSel2.style.marginRight='8px';
                (data.available_aggregations||[]).forEach(a=>{ const o=document.createElement('option'); o.value=a; o.text=a; aggSel2.appendChild(o); });
                const enableBtn = document.createElement('button'); enableBtn.innerText='Enable Online Aggregation for Selected Cluster'; enableBtn.onclick = async ()=>{
                    const selCluster = document.getElementById('adv_cluster_select');
                    if(!selCluster) { alert('No cluster selector present'); return; }
                    const clusterId = selCluster.value;
                    if(!clusterId){ alert('Select a cluster first'); return; }
                    const aggName = document.getElementById('adv_agg_select').value;
                    if(!aggName){ alert('Select aggregation'); return; }
                    try{
                        // fetch cluster info (not strictly necessary), then post cluster config
                        const cfg = { online_aggregation: true, aggregation: aggName };
                        const fm = new FormData(); fm.append('id', clusterId); fm.append('config', JSON.stringify(cfg));
                        const r2 = await fetch('/set_cluster_config', { method:'POST', body: fm });
                        if(r2.ok){ alert('Enabled online aggregation for cluster '+clusterId); refreshModelTree(); }
                        else { alert('Failed to enable: '+ await r2.text()); }
                    }catch(e){ alert('Failed: '+e); }
                };
                advDiv.appendChild(clusterSel); advDiv.appendChild(aggSel2); advDiv.appendChild(enableBtn);
                container.appendChild(advDiv);

                // Update persistent Datasets panel (drive list + per-worker dataset info)
                try{
                    // Drive files
                    const driveEl = document.getElementById('drive_datasets_list');
                    if(driveEl){
                        try{
                            const resp = await fetch('/list_datasets');
                            if(resp.ok){ const j = await resp.json(); const arr = j.datasets || []; if(arr.length){ let html = '<strong>Drive (chekml_datasets):</strong><ul>'; arr.forEach(f=>{ html += `<li>${f}</li>`; }); html += '</ul>'; driveEl.innerHTML = html; } else { driveEl.innerHTML = '<strong>Drive (chekml_datasets):</strong> (no datasets found)'; } }
                            else { driveEl.innerHTML = '<strong>Drive (chekml_datasets):</strong> (drive list failed)'; }
                        }catch(e){ driveEl.innerHTML = '<strong>Drive (chekml_datasets):</strong> (drive list error)'; }
                    }
                }catch(e){}

                try{
                    const wdsEl = document.getElementById('worker_datasets_list');
                    if(wdsEl){
                        let html = '<strong>Workers:</strong><ul>';
                        data.nodes.forEach(n=>{
                            const ds = n.dataset || {};
                            let details = ds.name ? ds.name : '(none)';
                            if(ds.source) details += ' ('+ds.source+')';
                            if(ds.x_shape) details += ' x:'+JSON.stringify(ds.x_shape);
                            if(ds.y_shape) details += ' y:'+JSON.stringify(ds.y_shape);
                            if(ds.dtype) details += ' dtype:'+ds.dtype;
                            html += `<li>${(n.worker_id||n.id)}: ${details}</li>`;
                        });
                        html += '</ul>';
                        wdsEl.innerHTML = html;
                    }
                }catch(e){}

                // aggregation options
                data.available_aggregations.forEach(a=>{ const o=document.createElement('option'); o.value=a; o.text=a; aggSel.appendChild(o); });

                // aggregation options
                data.available_aggregations.forEach(a=>{ const o=document.createElement('option'); o.value=a; o.text=a; aggSel.appendChild(o); });
            }catch(err){ console.error('Failed to refresh model tree', err); }
                // draw hierarchical layout with curved edges
            try{
                const drawModelTree = ()=>{
                    const svgId = 'model_tree_svg';
                    let old = document.getElementById(svgId);
                    if(old) old.remove();
                    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
                    svg.setAttribute('id', svgId);
                    svg.style.position='absolute';
                    svg.style.top='0';
                    svg.style.left='0';
                    svg.style.width='100%';
                    svg.style.height='100%';
                    svg.style.pointerEvents='none';
                    container.insertBefore(svg, container.firstChild);

                    // layout nodes using dagre for nicer automated positioning
                    const padding = 20;
                    const nodeW = 180;
                    const nodeH = 120;
                    try{
                        if(window.dagre && window.dagre.graphlib){
                            const g = new dagre.graphlib.Graph();
                            g.setGraph({ rankdir: 'LR', nodesep: 30, ranksep: 60 });
                            g.setDefaultEdgeLabel(function(){ return {}; });
                            // add nodes
                            data.nodes.forEach(n=>{ g.setNode(n.id, { width: nodeW, height: nodeH }); });
                            // add edges
                            (data.edges||[]).forEach(e=>{ try{ g.setEdge(e.from, e.to); }catch(err){} });
                            // compute layout
                            dagre.layout(g);
                            // apply positions
                            g.nodes().forEach(function(k){
                                const nodeMeta = g.node(k);
                                if(!nodeMeta) return;
                                const el = document.getElementById(('node_'+k).replace(/[^a-zA-Z0-9_-]/g,'_'));
                                if(!el) return;
                                el.style.position='absolute';
                                const left = Math.round(nodeMeta.x - nodeW/2 + padding);
                                const top = Math.round(nodeMeta.y - nodeH/2 + padding);
                                el.style.left = left + 'px';
                                el.style.top = top + 'px';
                                el.style.width = nodeW + 'px';
                                el.style.minHeight = nodeH + 'px';
                            });
                        } else {
                            // fallback to simple hierarchical placement if dagre not available
                            const nodes = {};
                            data.nodes.forEach(n=>{ nodes[n.id]=n; });
                            const adj = {};
                            const indeg = {};
                            Object.keys(nodes).forEach(k=>{ adj[k]=[]; indeg[k]=0; });
                            data.edges.forEach(e=>{
                                if(!adj[e.from]) adj[e.from]=[];
                                adj[e.from].push(e.to);
                                indeg[e.to] = (indeg[e.to]||0) + 1;
                            });
                            const roots = Object.keys(nodes).filter(k=>!indeg[k]);
                            const level = {};
                            const q = [];
                            if(roots.length){ roots.forEach(r=>{ level[r]=0; q.push(r); }); }
                            else { Object.keys(nodes).forEach((k,i)=>{ level[k]=0; q.push(k); }); }
                            while(q.length){
                                const cur = q.shift();
                                const curLevel = level[cur]||0;
                                (adj[cur]||[]).forEach(nbr=>{
                                    const nl = (level[nbr]===undefined)? curLevel+1 : Math.max(level[nbr], curLevel+1);
                                    if(level[nbr] === undefined) q.push(nbr);
                                    level[nbr] = nl;
                                });
                            }
                            const groups = {}; let maxLevel = 0;
                            Object.keys(level).forEach(k=>{ const lv = level[k]||0; maxLevel = Math.max(maxLevel, lv); if(!groups[lv]) groups[lv]=[]; groups[lv].push(k); });
                            const cr = container.getBoundingClientRect();
                            const colCount = Math.max(1, maxLevel+1);
                            const colWidth = Math.max(nodeW+20, (cr.width - padding*2) / colCount);
                            const vgap = 18;
                            Object.keys(groups).forEach(lv=>{
                                const list = groups[lv];
                                list.forEach((nid, idx)=>{
                                    const el = document.getElementById(('node_'+nid).replace(/[^a-zA-Z0-9_-]/g,'_'));
                                    if(!el) return;
                                    el.style.position='absolute';
                                    const left = Math.round(padding + lv * colWidth + (colWidth - nodeW)/2);
                                    const top = Math.round(padding + idx * (nodeH + vgap));
                                    el.style.left = left + 'px';
                                    el.style.top = top + 'px';
                                    el.style.width = nodeW + 'px';
                                    el.style.minHeight = nodeH + 'px';
                                });
                            });
                        }
                    }catch(e){ console.error('Layout failed', e); }

                    // draw curved edges
                    data.edges.forEach(e=>{
                        try{
                            const fromEl = document.getElementById(('node_'+e.from).replace(/[^a-zA-Z0-9_-]/g,'_'));
                            const toEl = document.getElementById(('node_'+e.to).replace(/[^a-zA-Z0-9_-]/g,'_'));
                            if(!fromEl || !toEl) return;
                            const r1 = fromEl.getBoundingClientRect();
                            const r2 = toEl.getBoundingClientRect();
                            const containerRect = container.getBoundingClientRect();
                            const x1 = r1.left + r1.width/2 - containerRect.left;
                            const y1 = r1.top + r1.height/2 - containerRect.top;
                            const x2 = r2.left + r2.width/2 - containerRect.left;
                            const y2 = r2.top + r2.height/2 - containerRect.top;
                            const dx = Math.max(40, Math.abs(x2-x1)/2);
                            const path = document.createElementNS('http://www.w3.org/2000/svg','path');
                            const d = `M ${x1} ${y1} C ${x1+dx} ${y1} ${x2-dx} ${y2} ${x2} ${y2}`;
                            path.setAttribute('d', d);
                            const col = e.state === 'processing' ? '#2196F3' : (e.state === 'done' ? '#4CAF50' : '#999');
                            path.setAttribute('stroke', col);
                            path.setAttribute('stroke-width','3');
                            path.setAttribute('fill','none');
                            path.setAttribute('stroke-opacity','0.95');
                            svg.appendChild(path);
                        }catch(err){ }
                    });
                };
                setTimeout(drawModelTree, 120);
            }catch(err){ console.error('Tree draw failed', err); }
        }

        // submit add edge form via fetch to avoid reload (guarded in case form is hidden)
        (function(){
            const addEdgeForm = document.getElementById('add_edge');
            if(!addEdgeForm) return;
            addEdgeForm.addEventListener('submit', async (e)=>{
                e.preventDefault();
                const form = e.target;
                const data = new FormData(form);
                try{
                    const resp = await fetch(form.action, { method:'POST', body: data });
                    if(resp.ok) { await refreshModelTree(); form.reset(); }
                    else { console.error('Failed to add edge', await resp.text()); }
                }catch(err){ console.error(err); }
            });
        })();

        setInterval(function(){ if(window.location.pathname === '/') { refreshModelTree(); } }, 5000);
        window.addEventListener('load', refreshModelTree);
        // client websocket to receive server-side change notifications and refresh UI immediately
        (function(){
            try{
                const proto = (location.protocol === 'https:') ? 'wss://' : 'ws://';
                const ws = new WebSocket(proto + location.host + '/client_ws');
                ws.onopen = function(){ console.log('client_ws connected'); };
                ws.onmessage = function(ev){
                    try{
                        const payload = JSON.parse(ev.data);
                        // refresh for any notification type
                        refreshModelTree();
                    }catch(e){ refreshModelTree(); }
                };
                ws.onclose = function(){ console.log('client_ws closed'); };
            }catch(e){ console.warn('client_ws init failed', e); }
        })();
        // join selected handler
        document.addEventListener('click', function(e){
            if(e.target && e.target.id === 'join_selected'){
                e.preventDefault();
                const checked = Array.from(document.querySelectorAll('.node-select')).filter(c=>c.checked).map(c=>c.dataset.nodeid);
                if(!checked.length){ alert('No nodes selected'); return; }
                const agg = document.getElementById('join_aggregation').value;
                const name = document.getElementById('join_name').value || '';
                const fm = new FormData();
                fm.append('nodes', checked.join(','));
                fm.append('aggregation', agg);
                if(name) fm.append('save_name', name);
                fetch('/join_nodes', { method: 'POST', body: fm }).then(async r=>{
                    if(r.ok){ alert('Operation successful'); setTimeout(()=>refreshModelTree(),400); }
                    else { const t = await r.text(); alert('Operation failed: '+t); }
                }).catch(err=>{ alert('Join error: '+err); });
            }
        });
        </script>

        <script>
        // removed full page reload to preserve user operations; refreshModelTree handles updates
        </script>
        </body>
        </html>
        """

        # inject model_configs JSON into the page placeholder
        body = body.replace('__MODEL_CONFIGS_JSON__', json.dumps(self.model_configs))
        return web.Response(text=body, content_type='text/html')

    async def model_tree_get(self, request):
        """Return JSON representing current workers (nodes) and configured edges."""
        nodes = []
        for wid, info in self.workers.items():
            nodes.append({
                'id': wid,
                'worker_id': info.get('worker_id'),
                'instance_id': info.get('instance_id'),
                'model': info.get('model'),
                'status': info.get('status'),
                'device': info.get('device'),
                'last_accuracy': (info.get('history')[-1] if info.get('history') else 0.0),
                'history': list(info.get('history') or []),
                'dataset': info.get('dataset') or info.get('dataset_info')
            })

        edges = list(self.model_tree_edges)
        clusters = list(self.model_clusters)
        cluster_links = list(self.cluster_links)
        # compute cluster readiness status
        for c in clusters:
            members = c.get('members', [])
            ready = True
            for m in members:
                w = self.workers.get(m)
                if not w or not w.get('last_result'):
                    ready = False
                    break
            c['status'] = 'ready' if ready else 'pending'
        # include available aggregation names for UI
        available_aggs = self.aggregation_registry.list()

        return web.json_response({'nodes': nodes, 'edges': edges, 'available_aggregations': available_aggs, 'clusters': clusters, 'cluster_links': cluster_links})

    async def get_model_config(self, request):
        name = request.rel_url.query.get('name')
        if not name:
            return web.json_response({}, status=400)
        cfg = self.model_configs.get(name) or {}
        return web.json_response(cfg)

    async def set_model_config(self, request):
        data = await request.post()
        name = data.get('name')
        cfg_raw = data.get('config') or '{}'
        if not name:
            return web.Response(text='Missing model name', status=400)
        try:
            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
        except Exception:
            return web.Response(text='Invalid JSON', status=400)
        self.model_configs[name] = cfg
        try:
            self._save_model_configs()
        except Exception:
            pass
        try:
            await self._notify_clients({'type':'model_configs_updated'})
        except Exception:
            pass
        return web.Response(text='OK', status=200)

    async def list_datasets(self, request):
        """List datasets from Google Drive folder 'chekml_datasets' if configured."""
        if not getattr(self.config, 'google_drive_enabled', False):
            return web.json_response({'datasets': []})
        try:
            creds = getattr(self.config, 'google_drive_credentials', None)
            client = GoogleDriveClient(credentials_file=creds, folder_name='chekml_datasets')
            ds = client.list_datasets()
            return web.json_response({'datasets': ds})
        except Exception as e:
            logger.exception(f"Failed to list datasets: {e}")
            return web.json_response({'datasets': []})

    async def set_cluster_config(self, request):
        """Set configuration for a specific cluster (by id). Expects form fields 'id' and 'config' (JSON)."""
        data = await request.post()
        cid = data.get('id')
        cfg_raw = data.get('config') or '{}'
        if not cid:
            return web.Response(text='Missing cluster id', status=400)
        try:
            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
        except Exception:
            return web.Response(text='Invalid JSON config', status=400)
        found = False
        for c in self.model_clusters:
            if c.get('id') == cid:
                c['config'] = cfg
                # expose quick flags for convenience
                if isinstance(cfg, dict) and cfg.get('online_aggregation'):
                    c['online_aggregation'] = True
                else:
                    c.pop('online_aggregation', None)
                found = True
                break
        if not found:
            return web.Response(text='Cluster not found', status=404)
        try:
            self._save_model_clusters()
        except Exception:
            pass
        try:
            await self._notify_clients({'type':'cluster_config_updated','id': cid})
        except Exception:
            pass
        return web.Response(text='OK', status=200)
    def _load_model_tree(self):
        """Load model-tree edges from disk (if exists)."""
        try:
            if os.path.exists(self.model_tree_file):
                with open(self.model_tree_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.model_tree_edges = data
                    else:
                        self.model_tree_edges = []
                logger.info(f"Loaded {len(self.model_tree_edges)} model-tree edges from {self.model_tree_file}")
        except Exception as e:
            logger.exception(f"Failed to load model_tree file: {e}")

    def _save_model_tree(self):
        """Persist model-tree edges to disk."""
        try:
            with open(self.model_tree_file, 'w') as f:
                json.dump(self.model_tree_edges, f, indent=2)
            logger.info(f"Saved {len(self.model_tree_edges)} model-tree edges to {self.model_tree_file}")
        except Exception as e:
            logger.exception(f"Failed to save model_tree file: {e}")

    def _load_model_clusters(self):
        try:
            if os.path.exists(self.model_clusters_file):
                with open(self.model_clusters_file, 'r') as f:
                    data = json.load(f)
                    self.model_clusters = data.get('clusters', [])
                    self.cluster_links = data.get('links', [])
            logger.info(f"Loaded {len(self.model_clusters)} clusters and {len(self.cluster_links)} links")
        except Exception as e:
            logger.exception(f"Failed to load clusters file: {e}")

    def _save_model_clusters(self):
        try:
            obj = {'clusters': self.model_clusters, 'links': self.cluster_links}
            with open(self.model_clusters_file, 'w') as f:
                json.dump(obj, f, indent=2)
            logger.info(f"Saved {len(self.model_clusters)} clusters and {len(self.cluster_links)} links to {self.model_clusters_file}")
        except Exception as e:
            logger.exception(f"Failed to save clusters file: {e}")

    def _load_model_configs(self):
        try:
            if os.path.exists(self.model_configs_file):
                with open(self.model_configs_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.model_configs = data
            logger.info(f"Loaded {len(self.model_configs)} model configs from {self.model_configs_file}")
        except Exception as e:
            logger.exception(f"Failed to load model configs: {e}")

    def _save_model_configs(self):
        try:
            with open(self.model_configs_file, 'w') as f:
                json.dump(self.model_configs, f, indent=2)
            logger.info(f"Saved {len(self.model_configs)} model configs to {self.model_configs_file}")
        except Exception as e:
            logger.exception(f"Failed to save model configs: {e}")

    def _edge_matches(self, edge: dict, workers: list) -> bool:
        """Return True if the edge's 'from' specification matches the provided worker list.

        Supports simple single-from matching, comma-separated lists, and JSON `config` with a
        `rule` key: 'any' (default), 'all', or 'group' (explicit group list in config).
        """
        try:
            # Normalize from field into list
            frm = edge.get('from') or ''
            if isinstance(frm, list):
                from_list = frm
            else:
                # allow comma-separated
                from_list = [x.strip() for x in str(frm).split(',') if x.strip()]

            # Try parsing config JSON for explicit rules
            cfg_raw = edge.get('config') or '{}'
            try:
                cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
            except Exception:
                cfg = {}

            rule = (cfg.get('rule') or cfg.get('match') or 'any').lower()

            if rule == 'group':
                # require explicit group list in config.groups or config.group
                group = cfg.get('group') or cfg.get('groups') or cfg.get('members')
                if not group:
                    # fallback to from_list
                    group = from_list
                return all(g in workers for g in group)

            if rule == 'all':
                # all from_list elements must be present in workers
                return all(f in workers for f in from_list)

            # default 'any'
            for f in from_list:
                if f in workers:
                    return True
            return False
        except Exception:
            return False

    async def model_tree_post(self, request):
        """Add a model-tree edge (from_node, to_node, aggregation, config)."""
        data = await request.post()
        action = data.get('action', 'add')
        if action == 'delete':
            edge_id = data.get('edge_id')
            if not edge_id:
                return web.Response(text='Missing edge_id', status=400)
            before = len(self.model_tree_edges)
            self.model_tree_edges = [e for e in self.model_tree_edges if e.get('id') != edge_id]
            self._save_model_tree()
            logger.info(f"Deleted edge {edge_id}, {before}->{len(self.model_tree_edges)}")
            try:
                await self._notify_clients({'type':'model_tree_updated'})
            except Exception:
                pass
            return web.Response(text='OK', status=200)
        elif action == 'update':
            edge_id = data.get('edge_id')
            if not edge_id:
                return web.Response(text='Missing edge_id', status=400)
            for e in self.model_tree_edges:
                if e.get('id') == edge_id:
                    # update fields
                    if 'aggregation' in data:
                        e['aggregation'] = data.get('aggregation')
                    if 'config' in data:
                        e['config'] = data.get('config')
                    if 'state' in data:
                        e['state'] = data.get('state')
                    self._save_model_tree()
                    try:
                        await self._notify_clients({'type':'model_tree_updated'})
                    except Exception:
                        pass
                    logger.info(f"Updated edge {edge_id}: {e}")
                    return web.Response(text='OK', status=200)
            return web.Response(text='Edge not found', status=404)
        else:
            frm = data.get('from_node')
            to = data.get('to_node')
            agg = data.get('aggregation')
            cfg = data.get('config')
            # basic validation
            if not frm or not to or not agg:
                return web.Response(text='Missing field', status=400)

            edge = {'id': str(uuid.uuid4()), 'from': frm, 'to': to, 'aggregation': agg, 'config': cfg or '{}', 'state': 'waiting'}
            self.model_tree_edges.append(edge)
            self._save_model_tree()
            try:
                await self._notify_clients({'type':'model_tree_updated'})
            except Exception:
                pass
            logger.info(f"Added model-tree edge: {edge}")
            return web.Response(text='OK', status=200)

    async def command_worker(self, request):
        """Start training on a specific worker by id."""
        data = await request.post()
        worker_id = data.get('worker_id')
        model_name = data.get('model_name')
        mode = data.get('mode', 'federated')
        aggregation = data.get('aggregation')

        if worker_id not in self.workers:
            return web.Response(text='Worker not found', status=404)

        info = self.workers[worker_id]
        if info.get('status') != 'idle':
            return web.Response(text='Worker not idle', status=400)

        # If no model_name provided, use the worker's assigned model
        if not model_name:
            model_name = info.get('model')
        if not model_name:
            return web.Response(text='No model specified and worker has no assigned model', status=400)

        # ensure global model exists
        if model_name not in self.global_models:
            return web.Response(text='No global model for requested name', status=400)

        # send model and train
        try:
            buf = io.BytesIO()
            torch.save(self.global_models[model_name], buf)
            payload = base64.b64encode(buf.getvalue()).decode('utf-8')

            ws = info['ws']
            await ws.send_json({'type': 'update_model', 'payload': payload})
            await ws.send_json({'type': 'train', 'mode': mode})
            info['status'] = 'working'

            # setup aggregation tracking for this single-worker job (record worker)
            self.ongoing_aggregations[model_name] = {
                'mode': mode,
                'aggregation': aggregation or mode,
                'expected': 1,
                'received': 0,
                'results': [],
                'config': {},
                'workers': [worker_id]
            }

            return web.Response(text='ok', status=200)
        except Exception as e:
            logger.exception(f"Failed to start training for {worker_id}: {e}")
            return web.Response(text=f'Error: {e}', status=500)
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
        action = data.get('action')
        model_name = data.get('model_name', 'simplecnn')

        if action == 'start_assigned':
            # Start training for all idle workers that have an assigned model (grouped by model)
            counts = {}
            started_total = 0
            # collect unique models among idle assigned workers
            models = set()
            for wid, info in self.workers.items():
                if info.get('model') and info.get('status') == 'idle':
                    models.add(info.get('model'))

            for m in models:
                c = await self.start_training(m)
                counts[m] = c
                started_total += c

            html = f"""
            <html><body style="font-family: Arial; padding: 20px;">
                <h1>✅ Training Started (Assigned Models)</h1>
                <p><strong>Workers started:</strong> {started_total}</p>
                <ul>
            """
            for m, c in counts.items():
                html += f"<li>{m}: {c} workers</li>"
            html += f"""
                </ul>
                <p><a href=\"/\">← Back to Control Panel</a></p>
                <script>setTimeout(function() {{ window.location.href = '/'; }}, 3000);</script>
            </body></html>
            """
            return web.Response(text=html, content_type='text/html')

        # default: start for selected model name
        count = await self.start_training(model_name)
        html = f"""
        <html><body style="font-family: Arial; padding: 20px;">
            <h1>✅ Training Started</h1>
            <p><strong>Model:</strong> {model_name}</p>
            <p><strong>Workers:</strong> {count} workers started training</p>
            <p><a href=\"/\">← Back to Control Panel</a></p>
            <script>setTimeout(function() {{ window.location.href = '/'; }}, 3000);</script>
        </body></html>
        """
        return web.Response(text=html, content_type='text/html')

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
        worker_key = data.get("worker_id")
        save_name = data.get("save_name") or None

        if not worker_key or worker_key not in self.workers:
            return web.Response(text='Worker not found', status=404)

        info = self.workers[worker_key]
        last = info.get('last_result')
        if not last or not last.get('result'):
            return web.Response(text='No result available to save for this worker', status=400)

        model_name = info.get('model') or f"worker_{worker_key}"
        if not save_name:
            save_name = f"saved_{model_name}_{worker_key}"

        # store weights in global_models
        try:
            self.global_models[save_name] = last['result']
            drive_msg = 'Google Drive not configured'

            # persist to disk under saved_models/
            try:
                saved_dir = os.path.join(os.getcwd(), 'saved_models')
                os.makedirs(saved_dir, exist_ok=True)
                save_path = os.path.join(saved_dir, f"{save_name}.pt")
                torch.save(last['result'], save_path)
                disk_msg = f'Saved to disk: {save_path}'
            except Exception as e:
                logger.warning(f"Failed to save {save_name} to disk: {e}")
                disk_msg = f'Disk save failed: {e}'

            # optionally persist to Google Drive
            if self.google_drive_client:
                try:
                    await self._save_model_to_drive(save_name)
                    drive_msg = 'Saved to Google Drive'
                except Exception as e:
                    logger.warning(f"Failed to save {save_name} to Drive: {e}")
                    drive_msg = f'Google Drive save failed: {e}'

            html = f"""
            <html><body style=\"font-family: Arial; padding:20px;\">
                <h1>Saved Worker Model</h1>
                <p>Saved <strong>{save_name}</strong> from worker <strong>{worker_key}</strong> into <strong>global_models</strong> (in-memory).</p>
                <p>{disk_msg}</p>
                <p>{drive_msg}</p>
                <p><a href=\"/\">← Back to Control Panel</a></p>
            </body></html>
            """
            logger.info(f"Saved worker model {save_name} from {worker_key} -> {save_path}")
            return web.Response(text=html, content_type='text/html')
        except Exception as e:
            logger.exception(f"Failed to save worker model: {e}")
            return web.Response(text=f'Error: {e}', status=500)
    
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

    def _average_weights(self, models: list):
        """Naive averaging for torch state-dict-like objects or tensors."""
        import time
        if not models:
            raise ValueError('No models to aggregate')
        first = models[0]
        try:
            if isinstance(first, dict):
                result = {}
                for k in first.keys():
                    try:
                        tensors = [m[k].float() for m in models]
                        stacked = torch.stack(tensors, dim=0)
                        result[k] = torch.mean(stacked, dim=0)
                    except Exception:
                        # fallback: take first
                        result[k] = first[k]
                return result
            else:
                # assume tensor-like
                stacked = torch.stack([m for m in models], dim=0)
                return torch.mean(stacked, dim=0)
        except Exception as e:
            raise

    async def join_nodes(self, request):
        """Join selected nodes by aggregating their latest models.

        Expects form fields: nodes (comma-separated ids), aggregation (optional), save_name (optional)
        """
        data = await request.post()
        nodes_raw = data.get('nodes') or ''
        agg = data.get('aggregation') or 'average'
        save_name = data.get('save_name') or None

        node_ids = [n.strip() for n in nodes_raw.split(',') if n.strip()]
        if not node_ids:
            return web.Response(text='No nodes selected', status=400)

        models = []
        missing = []
        for nid in node_ids:
            info = self.workers.get(nid)
            if not info:
                missing.append(nid); continue
            last = info.get('last_result')
            if last and last.get('result'):
                models.append(last['result'])
                continue
            # try assigned model name
            mname = info.get('model')
            if mname and mname in self.global_models:
                models.append(self.global_models[mname]); continue
            missing.append(nid)

        if missing:
            return web.Response(text=f'Missing models for nodes: {missing}', status=400)

        # use registered aggregator if available
        agg_name = data.get('aggregation') or 'federated'
        cfg_raw = data.get('aggregation_config') or data.get('config') or '{}'
        try:
            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
        except Exception:
            cfg = {}

        try:
            # convert state-dicts/tensors into per-layer lists
            def to_layer_lists(models):
                if isinstance(models[0], dict):
                    keys = list(models[0].keys())
                    local_results = []
                    for m in models:
                        local_results.append([m[k].float() if hasattr(m[k],'float') else m[k] for k in keys])
                    global_weights = [models[0][k].float() if hasattr(models[0][k],'float') else models[0][k] for k in keys]
                    return keys, global_weights, local_results
                else:
                    # tensor-only models
                    return None, [models[0]], [[m] for m in models]

            keys, global_weights, local_results = to_layer_lists(models)
            aggregator = self.aggregation_registry.get(agg_name)
            if aggregator:
                aggregated_layers = aggregator.aggregate(global_weights, local_results, cfg)
            else:
                # fallback to naive average
                aggregated_layers = self._average_weights(models)

            # reconstruct aggregated model
            if keys is not None and isinstance(aggregated_layers, list):
                agg_state = {}
                for k, t in zip(keys, aggregated_layers):
                    agg_state[k] = t
                agg_result = agg_state
            else:
                # aggregator returned tensor or unsupported structure
                agg_result = aggregated_layers
        except Exception as e:
            logger.exception(f"Aggregation failed: {e}")
            return web.Response(text=f'Aggregation failed: {e}', status=500)

        if not save_name:
            save_name = f"joined_{'_'.join(node_ids)}_{int(time.time())}"

        # store and persist
        try:
            self.global_models[save_name] = agg_result
            saved_dir = os.path.join(os.getcwd(), 'saved_models')
            os.makedirs(saved_dir, exist_ok=True)
            save_path = os.path.join(saved_dir, f"{save_name}.pt")
            torch.save(agg_result, save_path)
            drive_msg = 'Google Drive not configured'
            if self.google_drive_client:
                try:
                    await self._save_model_to_drive(save_name)
                    drive_msg = 'Saved to Google Drive'
                except Exception as e:
                    drive_msg = f'Drive save failed: {e}'

            html = f"""
            <html><body style=\"font-family: Arial; padding:20px;\">
                <h1>Joined Models</h1>
                <p>Created <strong>{save_name}</strong> from nodes: {', '.join(node_ids)}</p>
                <p>Saved to disk: {save_path}</p>
                <p>{drive_msg}</p>
                <p><a href=\"/\">← Back to Control Panel</a></p>
            </body></html>
            """
            logger.info(f"Joined nodes {node_ids} -> {save_name} ({save_path})")
            return web.Response(text=html, content_type='text/html')
        except Exception as e:
            logger.exception(f"Failed to save joined model: {e}")
            return web.Response(text=f'Error: {e}', status=500)

    async def create_cluster(self, request):
        data = await request.post()
        nodes_raw = data.get('nodes') or ''
        name = data.get('name') or f'cluster_{int(time.time())}'
        node_ids = [n.strip() for n in nodes_raw.split(',') if n.strip()]
        if not node_ids:
            return web.Response(text='No nodes specified', status=400)
        cluster_id = str(uuid.uuid4())
        cluster = {'id': cluster_id, 'name': name, 'members': node_ids}
        self.model_clusters.append(cluster)
        self._save_model_clusters()
        # notify clients
        try:
            await self._notify_clients({'type':'clusters_updated'})
        except Exception:
            pass
        return web.Response(text=f'Created cluster {name} ({cluster_id})', status=200)

    async def delete_cluster(self, request):
        """Delete a cluster by id or name"""
        data = await request.post()
        cid = data.get('id') or data.get('cluster_id') or data.get('name')
        if not cid:
            return web.Response(text='Missing cluster id', status=400)
        before = len(self.model_clusters)
        self.model_clusters = [c for c in self.model_clusters if c.get('id') != cid and c.get('name') != cid]
        if len(self.model_clusters) == before:
            return web.Response(text='Cluster not found', status=404)
        try:
            self._save_model_clusters()
        except Exception:
            pass
        try:
            await self._notify_clients({'type':'clusters_updated'})
        except Exception:
            pass
        return web.Response(text='OK', status=200)

    async def link_clusters(self, request):
        data = await request.post()
        frm = data.get('from')
        to = data.get('to')
        if not frm or not to:
            return web.Response(text='Missing from/to', status=400)
        link = {'from': frm, 'to': to}
        self.cluster_links.append(link)
        self._save_model_clusters()
        try:
            await self._notify_clients({'type':'clusters_updated'})
        except Exception:
            pass
        return web.Response(text='OK', status=200)

    async def aggregate_flow(self, request):
        data = await request.post()
        target = data.get('target')
        save_name = data.get('save_name') or None
        aggregation = data.get('aggregation') or None
        cfg_raw = data.get('config') or '{}'
        try:
            config = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
        except Exception:
            config = {}
        if not target:
            return web.Response(text='Missing target cluster id', status=400)

        # collect upstream clusters/nodes via reverse traversal
        to_visit = [target]
        visited = set()
        node_ids = set()
        while to_visit:
            cur = to_visit.pop(0)
            if cur in visited: continue
            visited.add(cur)
            # find cluster by id
            c = next((cc for cc in self.model_clusters if cc.get('id') == cur or cc.get('name') == cur), None)
            if c:
                for m in c.get('members',[]): node_ids.add(m)
            # find links where cur is 'to' and add their 'from'
            for lk in self.cluster_links:
                if lk.get('to') == cur:
                    to_visit.append(lk.get('from'))

        if not node_ids:
            return web.Response(text='No nodes found upstream for target', status=400)

        # reuse join_nodes aggregation over these node ids
        fm = {'nodes': ','.join(list(node_ids))}
        # build models list
        models = []
        missing = []
        for nid in node_ids:
            info = self.workers.get(nid)
            if info and info.get('last_result') and info.get('last_result').get('result'):
                models.append(info.get('last_result').get('result'))
                continue
            mname = info.get('model') if info else None
            if mname and mname in self.global_models:
                models.append(self.global_models[mname]); continue
            missing.append(nid)

        if missing:
            return web.Response(text=f'Missing models for nodes: {missing}', status=400)

        # use registered aggregator when possible
        agg_name = data.get('aggregation') or 'federated'
        cfg_raw = data.get('aggregation_config') or data.get('config') or '{}'
        try:
            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
        except Exception:
            cfg = {}

        try:
            # reuse conversion logic from join_nodes
            def to_layer_lists(models):
                if isinstance(models[0], dict):
                    keys = list(models[0].keys())
                    local_results = []
                    for m in models:
                        local_results.append([m[k].float() if hasattr(m[k],'float') else m[k] for k in keys])
                    global_weights = [models[0][k].float() if hasattr(models[0][k],'float') else models[0][k] for k in keys]
                    return keys, global_weights, local_results
                else:
                    return None, [models[0]], [[m] for m in models]

            keys, global_weights, local_results = to_layer_lists(models)
            aggregator = self.aggregation_registry.get(agg_name)
            if aggregator:
                aggregated_layers = aggregator.aggregate(global_weights, local_results, cfg)
            else:
                aggregated_layers = self._average_weights(models)

            if keys is not None and isinstance(aggregated_layers, list):
                agg_state = {}
                for k, t in zip(keys, aggregated_layers):
                    agg_state[k] = t
                agg_result = agg_state
            else:
                agg_result = aggregated_layers
        except Exception as e:
            logger.exception(f"Aggregation failed: {e}")
            return web.Response(text=f'Aggregation failed: {e}', status=500)

        if not save_name:
            save_name = f"flow_{target}_{int(time.time())}"

        try:
            self.global_models[save_name] = agg_result
            saved_dir = os.path.join(os.getcwd(), 'saved_models')
            os.makedirs(saved_dir, exist_ok=True)
            save_path = os.path.join(saved_dir, f"{save_name}.pt")
            torch.save(agg_result, save_path)
            self._save_model_clusters()
            try:
                await self._notify_clients({'type':'clusters_updated'})
            except Exception:
                pass
            return web.Response(text=f'Aggregated flow saved to {save_path}', status=200)
        except Exception as e:
            logger.exception(f"Failed to save flow aggregation: {e}")
            return web.Response(text=f'Error: {e}', status=500)

    async def save_edge(self, request):
        """Save the aggregated/target model for a model-tree edge"""
        data = await request.post()
        edge_id = data.get('edge_id')
        if not edge_id:
            return web.Response(text='Missing edge_id', status=400)

        edge = next((e for e in self.model_tree_edges if e.get('id') == edge_id), None)
        if not edge:
            return web.Response(text='Edge not found', status=404)

        # determine target model name
        cfg_raw = edge.get('config') or '{}'
        try:
            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
        except Exception:
            cfg = {}

        target_model = cfg.get('to_model')
        if not target_model:
            target_worker = edge.get('to')
            if target_worker and target_worker in self.workers:
                target_model = self.workers[target_worker].get('model')

        if not target_model:
            return web.Response(text='No target model determined for edge', status=400)

        if target_model not in self.global_models:
            return web.Response(text=f'Target model {target_model} not present in global models', status=404)

            # persist to disk as well
        try:
            saved_dir = os.path.join(os.getcwd(), 'saved_models')
            os.makedirs(saved_dir, exist_ok=True)
            save_path = os.path.join(saved_dir, f"{target_model}.pt")
            try:
                torch.save(self.global_models[target_model], save_path)
                disk_msg = f'Saved to disk: {save_path}'
            except Exception as e:
                logger.warning(f"Failed to save edge target {target_model} to disk: {e}")
                disk_msg = f'Disk save failed: {e}'

            drive_msg = 'Google Drive not configured'
            if self.google_drive_client:
                try:
                    await self._save_model_to_drive(target_model)
                    drive_msg = 'Saved to Google Drive'
                except Exception as e:
                    logger.warning(f"Failed to save edge target {target_model} to Drive: {e}")
                    drive_msg = f'Google Drive save failed: {e}'

            html = f"""
            <html><body style=\"font-family: Arial; padding:20px;\">
                <h1>Saved Edge Target</h1>
                <p>Target <strong>{target_model}</strong> is present in <strong>global_models</strong> (in-memory).</p>
                <p>{disk_msg}</p>
                <p>{drive_msg}</p>
                <p><a href=\"/\">← Back to Control Panel</a></p>
            </body></html>
            """
            logger.info(f"Saved edge target model {target_model} for edge {edge_id} -> {save_path}")
            return web.Response(text=html, content_type='text/html')
        except Exception as e:
            logger.exception(f"Failed to save edge target: {e}")
            return web.Response(text=f'Error: {e}', status=500)

    async def handle_websocket(self, request):
        """Handle WebSocket connections from workers"""
        ws = web.WebSocketResponse(max_msg_size=0)
        await ws.prepare(request)
        # assign a temporary connection key; will be rekeyed when worker sends its `instance_id`
        conn_key = f"conn_{uuid.uuid4().hex[:8]}"
        self.workers[conn_key] = {
            "ws": ws,
            "status": "idle",
            "model": None,
            "device": "unknown",
            "history": [],
            "last_result": None,
            "worker_id": None,      # persistent machine id (optional)
            "instance_id": None     # per-process id
        }

        worker_key = conn_key

        logger.info(f"[+] {worker_key} connected (temp)")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    # inspect status messages early to allow worker to supply a persistent id
                    try:
                        payload = json.loads(msg.data)
                    except Exception:
                        payload = {}

                    # If worker sends status with instance_id/worker_id, attach them to this connection
                    if payload.get('type') == 'status':
                        inst = payload.get('instance_id')
                        pers = payload.get('worker_id')

                        # If worker provided an instance id, rekey this connection to that instance id
                        if inst and inst != worker_key:
                            # remove any stale entry for this instance id
                            if inst in self.workers:
                                try:
                                    self.workers.pop(inst)
                                except Exception:
                                    pass
                            try:
                                self.workers[inst] = self.workers.pop(worker_key)
                                worker_key = inst
                                logger.info(f"Rekeyed connection to instance {worker_key}")
                            except Exception as e:
                                logger.exception(f"Failed to rekey to instance id: {e}")

                        # store persistent worker id on the connection info (do not rekey by persistent id)
                        try:
                            if pers:
                                self.workers[worker_key]['worker_id'] = pers
                        except Exception:
                            pass
                        try:
                            if inst:
                                self.workers[worker_key]['instance_id'] = inst
                        except Exception:
                            pass

                    await self._handle_worker_message(worker_key, msg.data)
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"[!] {worker_id} closed with exception: {ws.exception()}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler for {worker_id}: {e}")
        finally:
            logger.info(f"[-] {worker_key} disconnected")
            try:
                self.workers.pop(worker_key, None)
            except Exception:
                pass

        return ws
    
    async def handle_client_ws(self, request):
        """Handle WebSocket connections from browser clients for UI events"""
        ws = web.WebSocketResponse(max_msg_size=0)
        await ws.prepare(request)
        if not hasattr(self, 'client_ws'):
            self.client_ws = set()
        self.client_ws.add(ws)
        logger.info(f"[+] client_ws connected ({len(self.client_ws)})")
        try:
            async for msg in ws:
                # we don't expect messages, but keep the connection alive
                pass
        except Exception:
            pass
        finally:
            try:
                self.client_ws.discard(ws)
            except Exception:
                pass
            logger.info(f"[-] client_ws disconnected ({len(getattr(self,'client_ws',[]))})")
        return ws

    async def _notify_clients(self, payload: dict):
        """Send JSON payload to connected UI clients (ignore failures)."""
        try:
            if not hasattr(self, 'client_ws'):
                return
            dead = []
            for ws in list(self.client_ws):
                try:
                    await ws.send_str(json.dumps(payload))
                except Exception:
                    try:
                        dead.append(ws)
                    except Exception:
                        pass
            for d in dead:
                try:
                    self.client_ws.discard(d)
                except Exception:
                    pass
        except Exception:
            pass
    
    async def _handle_worker_message(self, worker_id: str, message: str):
        """Process messages from workers"""
        data = json.loads(message)
        msg_type = data.get("type")
        
        if msg_type == "status":
            await self._handle_status_update(worker_id, data)
        elif msg_type == 'intermediate':
            await self._handle_intermediate(worker_id, data)
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
        # dataset metadata (optional)
        if "dataset" in data and data.get('dataset'):
            self.workers[worker_id]['dataset'] = data.get('dataset')
        if "dataset_info" in data and data.get('dataset_info'):
            self.workers[worker_id]['dataset'] = data.get('dataset_info')
        # persist any ids sent by the worker (persistent machine id and per-process instance id)
        if "worker_id" in data and data.get("worker_id"):
            self.workers[worker_id]["worker_id"] = data.get("worker_id")
        if "instance_id" in data and data.get("instance_id"):
            self.workers[worker_id]["instance_id"] = data.get("instance_id")
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
            # Determine aggregation method; model-tree edges can override
            aggregation_name = agg_info.get("aggregation", mode)
            try:
                agg_workers = agg_info.get('workers', [])
                chosen_edge = None
                # choose an edge whose 'from' matches the participating workers
                for e in self.model_tree_edges:
                    try:
                        if self._edge_matches(e, agg_workers):
                            chosen_edge = e
                            break
                    except Exception:
                        continue
                if chosen_edge:
                    aggregation_name = chosen_edge.get('aggregation', aggregation_name)
                    chosen_edge['state'] = 'processing'
                    try:
                        self._save_model_tree()
                    except Exception:
                        pass
            except Exception:
                chosen_edge = None

            aggregator = self.aggregation_registry.get(aggregation_name)
            
            if aggregator:
                current_weights = self.global_models.get(model_name)
                new_weights = aggregator.aggregate(current_weights, agg_info["results"], agg_info.get("config", {}))
                self.global_models[model_name] = new_weights
                logger.info(f"[=] Aggregated {model_name} using {aggregation_name}")

                if chosen_edge:
                    try:
                        # If edge indicates a cross-model target, try storing into target model
                        chosen_edge['state'] = 'done'
                        # determine target model name: prefer explicit config.to_model, else lookup target worker
                        cfg_raw = chosen_edge.get('config') or '{}'
                        try:
                            cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw
                        except Exception:
                            cfg = {}

                        target_model = cfg.get('to_model')
                        if not target_model:
                            target_worker = chosen_edge.get('to')
                            if target_worker and target_worker in self.workers:
                                target_model = self.workers[target_worker].get('model')

                        if target_model:
                            # store aggregated weights into target global model (cross-model aggregation)
                            self.global_models[target_model] = new_weights
                            logger.info(f"[=] Cross-model aggregated into {target_model} via edge {chosen_edge.get('id')}")

                        self._save_model_tree()
                    except Exception:
                        pass
            
            # Save to Google Drive if enabled
            if self.google_drive_client:
                try:
                    await self._save_model_to_drive(model_name)
                except Exception as e:
                    logger.error(f"Failed to save model to Google Drive: {e}")
            
            del self.ongoing_aggregations[model_name]

    async def _handle_intermediate(self, worker_id: str, data: dict):
        """Handle intermediate messages from workers (online aggregation hooks)."""
        try:
            model_name = data.get('model')
            payload = data.get('payload')
            agg_name = data.get('aggregation') or None

            # pick aggregator: preference order
            # 1) aggregator provided in message
            # 2) cluster-level config for the worker (most specific)
            # 3) ongoing aggregation entry for model
            # 4) default 'federated'
            # check cluster-level overrides (worker-centric)
            try:
                if not agg_name:
                    # find clusters that include this worker
                    for c in (self.model_clusters or []):
                        members = c.get('members') or []
                        if isinstance(members, str):
                            members = [m.strip() for m in members.split(',') if m.strip()]
                        if worker_id in members:
                            cfg = c.get('config') or {}
                            if isinstance(cfg, dict) and cfg.get('online_aggregation'):
                                agg_name = cfg.get('aggregation') or agg_name
                                break
            except Exception:
                pass
            if not agg_name and model_name and model_name in self.ongoing_aggregations:
                agg_name = self.ongoing_aggregations[model_name].get('aggregation')
            if not agg_name:
                agg_name = 'federated'

            aggregator = self.aggregation_registry.get(agg_name)
            if not aggregator:
                logger.debug(f"No aggregator registered for {agg_name}; skipping intermediate handling")
                return

            # prepare global_weights as list if available
            global_weights = None
            if model_name and model_name in self.global_models:
                gw = self.global_models[model_name]
                if isinstance(gw, dict):
                    # convert dict to list
                    try:
                        global_weights = [gw[k] for k in sorted(gw.keys())]
                    except Exception:
                        global_weights = list(gw.values())
                else:
                    global_weights = gw

            # call aggregator hook
            try:
                res = None
                if hasattr(aggregator, 'on_intermediate'):
                    res = aggregator.on_intermediate(global_weights, payload, {})
                # if aggregator returns updated weights under 'weights', apply and broadcast
                if isinstance(res, dict) and 'weights' in res and model_name:
                    try:
                        new_weights = res['weights']
                        # accept both dict (state_dict) or list
                        self.global_models[model_name] = new_weights
                        # broadcast updated weights to all connected workers for this model
                        try:
                            buf = io.BytesIO()
                            torch.save(new_weights, buf)
                            payload_b = base64.b64encode(buf.getvalue()).decode('utf-8')
                            for wid, info in self.workers.items():
                                try:
                                    if info.get('model') == model_name and info.get('status') == 'idle':
                                        await info['ws'].send_json({'type':'update_model','payload':payload_b})
                                except Exception:
                                    continue
                        except Exception as e:
                            logger.exception(f"Failed to broadcast intermediate-updated weights: {e}")
                    except Exception as e:
                        logger.exception(f"Failed to apply intermediate result from aggregator: {e}")
            except Exception as e:
                logger.exception(f"Aggregator on_intermediate failed: {e}")
        except Exception as e:
            logger.exception(f"Error handling intermediate from {worker_id}: {e}")
    
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
        
        # Setup aggregation tracking (include participating workers)
        aggregation_name = aggregation or mode
        self.ongoing_aggregations[model_name] = {
            "mode": mode,
            "aggregation": aggregation_name,
            "expected": len(eligible_workers),
            "received": 0,
            "results": [],
            "config": config or {},
            "workers": eligible_workers
        }
        
        logger.info(f"[=] Started {mode} training for {model_name} with {len(eligible_workers)} workers")
        return len(eligible_workers)

    async def train_cluster(self, request):
        """Start training for members of a cluster.

        Expects form: id (cluster id), model_name (required), aggregation (optional), mode (optional)
        """
        data = await request.post()
        cid = data.get('id')
        model_name = data.get('model_name')
        agg = data.get('aggregation') or data.get('agg')
        mode = data.get('mode') or 'federated'

        if not cid:
            return web.Response(text='Missing cluster id', status=400)
        if not model_name:
            return web.Response(text='Missing model_name', status=400)

        # find cluster
        cluster = None
        for c in self.model_clusters:
            if c.get('id') == cid:
                cluster = c
                break
        if not cluster:
            return web.Response(text='Cluster not found', status=404)

        members = cluster.get('members') or []
        if isinstance(members, str):
            members = [m.strip() for m in members.split(',') if m.strip()]

        # ensure global model exists if possible
        if model_name not in self.global_models:
            logger.warning(f"Global model {model_name} not found; cluster training will proceed without broadcasting initial weights")

        # send update_model and train messages to each eligible member
        started = 0
        for wid in members:
            info = self.workers.get(wid)
            if not info:
                continue
            try:
                ws = info.get('ws')
                if not ws:
                    continue
                # only start on idle workers
                if info.get('status') != 'idle':
                    continue
                # send updated weights if available
                if model_name in self.global_models:
                    buf = io.BytesIO()
                    torch.save(self.global_models[model_name], buf)
                    payload = base64.b64encode(buf.getvalue()).decode('utf-8')
                    await ws.send_json({'type':'update_model','payload': payload})
                # instruct worker to train
                await ws.send_json({'type':'train','mode': mode})
                info['status'] = 'working'
                started += 1
            except Exception as e:
                logger.warning(f"Failed to start cluster train for worker {wid}: {e}")

        # setup aggregation tracking keyed by cluster id
        self.ongoing_aggregations[f'cluster:{cid}:{model_name}'] = {
            'mode': mode,
            'aggregation': agg or mode,
            'expected': started,
            'received': 0,
            'results': [],
            'config': {},
            'workers': members
        }

        logger.info(f"Started cluster training for cluster {cid} model {model_name} with {started} workers")
        return web.Response(text=f'Started {started}', status=200)
    
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
        app.router.add_get("/model_tree", self.model_tree_get)
        app.router.add_post("/model_tree", self.model_tree_post)
        app.router.add_post("/command_worker", self.command_worker)
        app.router.add_post("/load_model", self.load_model)
        app.router.add_post("/save_edge", self.save_edge)
        app.router.add_post("/join_nodes", self.join_nodes)
        app.router.add_post("/create_cluster", self.create_cluster)
        app.router.add_post("/link_clusters", self.link_clusters)
        app.router.add_post("/aggregate_flow", self.aggregate_flow)
        app.router.add_get('/client_ws', self.handle_client_ws)
        app.router.add_post('/delete_cluster', self.delete_cluster)
        app.router.add_get('/get_model_config', self.get_model_config)
        app.router.add_post('/set_model_config', self.set_model_config)
        app.router.add_post('/set_cluster_config', self.set_cluster_config)
        app.router.add_post('/train_cluster', self.train_cluster)
        app.router.add_get('/list_datasets', self.list_datasets)
        
        # theme image removed (no /theme.png route)
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
