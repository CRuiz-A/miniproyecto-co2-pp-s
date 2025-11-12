import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re

st.set_page_config(page_title="CO₂ Viewer", page_icon="🧊", layout="wide")

BASE_DIR = Path(__file__).parent
TIMESTEPS_DIR = BASE_DIR / "timesteps_export"
CACHE_DIR = BASE_DIR / "outputs" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner=False)
def read_grdecl_property(filepath: str) -> np.ndarray:
    """Lee valores de un archivo GRDECL."""
    values: List[float] = []
    reading = False
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("--"):
                continue
            if any(key in line for key in ["YMFS", "SOIL", "SWAT", "SGAS", "PRESSURE"]):
                reading = True
                continue
            if line == "/" or line.startswith("/"):
                break
            if reading:
                parts = line.replace("/", "").split()
                for part in parts:
                    if "*" in part:
                        count_str, value_str = part.split("*")
                        try:
                            values.extend([float(value_str)] * int(count_str))
                        except Exception:
                            continue
                    else:
                        try:
                            values.append(float(part))
                        except Exception:
                            continue
    return np.array(values, dtype=float)


@st.cache_data(show_spinner=False)
def load_all_timesteps() -> Tuple[Dict[int, np.ndarray], List[int]]:
    """Carga todos los timesteps YMFS."""
    if not TIMESTEPS_DIR.exists():
        return {}, []

    files = sorted(TIMESTEPS_DIR.glob("YMFS_ts_*.GRDECL"))
    data: Dict[int, np.ndarray] = {}
    indices: List[int] = []

    for filepath in files:
        match = re.search(r"ts_(\d+)", filepath.name)
        if not match:
            continue
        timestep = int(match.group(1))
        data[timestep] = read_grdecl_property(str(filepath))
        indices.append(timestep)

    indices.sort()
    return data, indices


@st.cache_data(show_spinner=False)
def preprocess_all_data(ymfs_dict: Dict[int, np.ndarray], ts_indices: List[int], threshold: float) -> Dict:
    """Preprocesa todos los datos para JavaScript."""
    nx, ny, nz = 100, 100, 10
    x_min, x_max = 0.0, 10000.0
    y_min, y_max = 0.0, 10000.0
    z_top, z_bottom = -2500.0, -2700.0
    
    cell_size_x = (x_max - x_min) / (nx - 1)
    cell_size_y = (y_max - y_min) / (ny - 1)
    cell_size_z = (z_bottom - z_top) / (nz - 1)
    
    # Pozos inyectores (fijos)
    wells = [
        (2500.0, 2500.0, -2500.0),
        (2500.0, 7500.0, -2500.0),
        (7500.0, 2500.0, -2500.0),
        (7438.0, 7438.0, -2500.0),
    ]
    
    cube_size = 200.0
    half = cube_size / 2.0
    
    injector_vertices = []
    injector_faces = []
    vertex_offset = 0
    
    for cx, cy, cz in wells:
        vertices = [
            [cx - half, cy - half, cz - half],
            [cx + half, cy - half, cz - half],
            [cx + half, cy + half, cz - half],
            [cx - half, cy + half, cz - half],
            [cx - half, cy - half, cz + half],
            [cx + half, cy - half, cz + half],
            [cx + half, cy + half, cz + half],
            [cx - half, cy + half, cz + half],
        ]
        injector_vertices.extend(vertices)
        
        faces = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
            [0, 3, 7], [0, 7, 4], [1, 5, 6], [1, 6, 2],
        ]
        for face in faces:
            injector_faces.append([vertex_offset + face[0], vertex_offset + face[1], vertex_offset + face[2]])
        vertex_offset += 8
    
    # Datos por timestep (solo índices y valores de celdas > threshold)
    timestep_data = {}
    
    for ts in ts_indices:
        ymfs_values = ymfs_dict[ts]
        total = nx * ny * nz
        if len(ymfs_values) < total:
            padded = np.zeros(total, dtype=float)
            padded[:len(ymfs_values)] = ymfs_values
            ymfs_values = padded
        elif len(ymfs_values) > total:
            ymfs_values = ymfs_values[:total]
        
        # Solo guardamos índices de celdas activas (> threshold)
        active_cells = []
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    idx = i + j * nx + k * nx * ny
                    value = ymfs_values[idx]
                    if value >= threshold:
                        x = x_min + i * cell_size_x
                        y = y_min + j * cell_size_y
                        z = z_top + k * cell_size_z
                        active_cells.append({
                            'x': float(x),
                            'y': float(y),
                            'z': float(z),
                            'value': float(value)
                        })
        
        timestep_data[str(ts)] = {
            'cells': active_cells,
            'count': len(active_cells)
        }
    
    return {
        'timesteps': ts_indices,
        'data': timestep_data,
        'injectors': {
            'vertices': injector_vertices,
            'faces': injector_faces
        },
        'grid': {
            'cell_size_x': float(cell_size_x),
            'cell_size_y': float(cell_size_y),
            'cell_size_z': float(cell_size_z)
        },
        'bounds': {
            'x': [float(x_min), float(x_max)],
            'y': [float(y_min), float(y_max)],
            'z': [float(z_bottom), float(z_top)]
        }
    }


def create_viewer_html(data_json: str) -> str:
    """Crea el HTML del viewer con Plotly."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; }}
        #plot {{ width: 100vw; height: 100vh; }}
        #controls {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            z-index: 1000;
            max-width: 250px;
        }}
        .control-group {{
            margin-bottom: 12px;
        }}
        label {{
            display: block;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 4px;
            color: #333;
        }}
        input[type="range"] {{
            width: 100%;
        }}
        button {{
            padding: 8px 16px;
            margin: 4px 2px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        button:hover {{
            background: #0056b3;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .info {{
            font-size: 11px;
            color: #666;
            margin-top: 8px;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 20px;
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div id="loading">Cargando datos...</div>
    <div id="controls" style="display:none;">
        <div class="control-group">
            <label>Timestep: <span id="ts-label">0</span></label>
            <input type="range" id="ts-slider" min="0" max="0" value="0" step="1">
        </div>
        <div style="text-align: center;">
            <button id="play-btn" onclick="togglePlay()">▶ Play</button>
            <button onclick="previousTimestep()">◀</button>
            <button onclick="nextTimestep()">▶</button>
        </div>
        <div class="control-group">
            <label>Z Scale: <span id="zscale-label">1</span></label>
            <input type="range" id="zscale-slider" min="1" max="20" value="1" step="1">
        </div>
        <div class="control-group">
            <label>
                <input type="checkbox" id="injectors-check" checked onchange="toggleInjectors()">
                Mostrar inyectores
            </label>
        </div>
        <div class="info">
            <div>Celdas activas: <span id="cell-count">0</span></div>
            <div>FPS: <span id="fps">0</span></div>
        </div>
    </div>
    <div id="plot"></div>

    <script>
        const DATA = {data_json};
        let currentTimestepIndex = 0;
        let isPlaying = false;
        let playInterval = null;
        let showInjectors = true;
        let lastFrameTime = Date.now();
        let frameCount = 0;
        let fps = 0;

        function updateFPS() {{
            frameCount++;
            const now = Date.now();
            if (now - lastFrameTime >= 1000) {{
                fps = frameCount;
                document.getElementById('fps').textContent = fps;
                frameCount = 0;
                lastFrameTime = now;
            }}
        }}

        function buildMesh(cells, cellSize) {{
            if (!cells || cells.length === 0) {{
                return {{
                    x: [], y: [], z: [],
                    i: [], j: [], k: [],
                    intensity: []
                }};
            }}

            const x = [], y = [], z = [];
            const i = [], j = [], k = [];
            const intensity = [];
            
            const dx = cellSize.x;
            const dy = cellSize.y;
            const dz = cellSize.z;

            let vertexIndex = 0;
            
            cells.forEach(cell => {{
                const x0 = cell.x, y0 = cell.y, z0 = cell.z;
                
                // 8 vértices del cubo
                x.push(x0, x0+dx, x0+dx, x0, x0, x0+dx, x0+dx, x0);
                y.push(y0, y0, y0+dy, y0+dy, y0, y0, y0+dy, y0+dy);
                z.push(z0, z0, z0, z0, z0+dz, z0+dz, z0+dz, z0+dz);
                
                // 12 triángulos (6 caras × 2 triángulos)
                const faces = [
                    [0,1,2],[0,2,3], [4,6,5],[4,7,6],
                    [0,4,5],[0,5,1], [2,6,7],[2,7,3],
                    [0,3,7],[0,7,4], [1,5,6],[1,6,2]
                ];
                
                faces.forEach(face => {{
                    i.push(vertexIndex + face[0]);
                    j.push(vertexIndex + face[1]);
                    k.push(vertexIndex + face[2]);
                    intensity.push(cell.value);
                }});
                
                vertexIndex += 8;
            }});

            return {{ x, y, z, i, j, k, intensity }};
        }}

        function buildInjectorMesh() {{
            const vertices = DATA.injectors.vertices;
            const faces = DATA.injectors.faces;
            
            const x = vertices.map(v => v[0]);
            const y = vertices.map(v => v[1]);
            const z = vertices.map(v => v[2]);
            
            const i = [], j = [], k = [];
            faces.forEach(face => {{
                i.push(face[0]);
                j.push(face[1]);
                k.push(face[2]);
            }});
            
            return {{ x, y, z, i, j, k }};
        }}

        function updatePlot() {{
            const ts = DATA.timesteps[currentTimestepIndex];
            const tsData = DATA.data[ts];
            const zScale = parseInt(document.getElementById('zscale-slider').value);
            
            document.getElementById('ts-label').textContent = ts;
            document.getElementById('cell-count').textContent = tsData.count;
            
            const cellSize = DATA.grid;
            const mesh = buildMesh(tsData.cells, {{
                x: cellSize.cell_size_x,
                y: cellSize.cell_size_y,
                z: cellSize.cell_size_z
            }});
            
            const traces = [];
            
            if (mesh.x.length > 0) {{
                traces.push({{
                    type: 'mesh3d',
                    x: mesh.x, y: mesh.y, z: mesh.z,
                    i: mesh.i, j: mesh.j, k: mesh.k,
                    intensity: mesh.intensity,
                    colorscale: 'Hot',
                    cmin: 0.1,
                    cmax: 1.0,
                    showscale: true,
                    flatshading: false,
                    lighting: {{
                        ambient: 0.6,
                        diffuse: 0.7,
                        specular: 0.2
                    }},
                    name: 'YMFS'
                }});
            }}
            
            if (showInjectors) {{
                const injMesh = buildInjectorMesh();
                traces.push({{
                    type: 'mesh3d',
                    x: injMesh.x, y: injMesh.y, z: injMesh.z,
                    i: injMesh.i, j: injMesh.j, k: injMesh.k,
                    color: 'blue',
                    opacity: 0.9,
                    flatshading: true,
                    showscale: false,
                    name: 'Inyectores'
                }});
            }}
            
            const layout = {{
                title: `CO₂ (YMFS) - Timestep ${{ts}}`,
                scene: {{
                    xaxis: {{ title: 'X (m)', range: DATA.bounds.x }},
                    yaxis: {{ title: 'Y (m)', range: DATA.bounds.y }},
                    zaxis: {{ title: 'Z (m)', range: DATA.bounds.z }},
                    aspectmode: 'manual',
                    aspectratio: {{ x: 1, y: 1, z: zScale }},
                    camera: {{
                        eye: {{ x: 1.5, y: 1.5, z: 1.2 }}
                    }}
                }},
                margin: {{ l: 0, r: 0, t: 40, b: 0 }},
                paper_bgcolor: '#f8f9fa'
            }};
            
            Plotly.react('plot', traces, layout, {{ responsive: true }});
            updateFPS();
        }}

        function nextTimestep() {{
            if (currentTimestepIndex < DATA.timesteps.length - 1) {{
                currentTimestepIndex++;
                document.getElementById('ts-slider').value = currentTimestepIndex;
                updatePlot();
            }}
        }}

        function previousTimestep() {{
            if (currentTimestepIndex > 0) {{
                currentTimestepIndex--;
                document.getElementById('ts-slider').value = currentTimestepIndex;
                updatePlot();
            }}
        }}

        function togglePlay() {{
            isPlaying = !isPlaying;
            const btn = document.getElementById('play-btn');
            
            if (isPlaying) {{
                btn.textContent = '⏸ Pause';
                playInterval = setInterval(() => {{
                    if (currentTimestepIndex < DATA.timesteps.length - 1) {{
                        nextTimestep();
                    }} else {{
                        currentTimestepIndex = 0;
                        document.getElementById('ts-slider').value = 0;
                        updatePlot();
                    }}
                }}, 500);
            }} else {{
                btn.textContent = '▶ Play';
                if (playInterval) {{
                    clearInterval(playInterval);
                    playInterval = null;
                }}
            }}
        }}

        function toggleInjectors() {{
            showInjectors = document.getElementById('injectors-check').checked;
            updatePlot();
        }}

        // Event listeners
        document.getElementById('ts-slider').addEventListener('input', (e) => {{
            currentTimestepIndex = parseInt(e.target.value);
            updatePlot();
        }});

        document.getElementById('zscale-slider').addEventListener('input', (e) => {{
            document.getElementById('zscale-label').textContent = e.target.value;
            updatePlot();
        }});

        // Inicializar
        window.addEventListener('load', () => {{
            document.getElementById('loading').style.display = 'none';
            document.getElementById('controls').style.display = 'block';
            
            const slider = document.getElementById('ts-slider');
            slider.max = DATA.timesteps.length - 1;
            
            updatePlot();
        }});
    </script>
</body>
</html>
"""


def main() -> None:
    st.title("🧊 CO₂ Optimized Viewer")
    st.caption("Viewer optimizado con un solo HTML y datos en JavaScript")

    threshold = st.sidebar.slider("Umbral mínimo YMFS", 0.0, 1.0, 0.10, 0.01)

    # Cargar datos
    with st.spinner("Cargando timesteps..."):
        ymfs_by_ts, ts_indices = load_all_timesteps()

    if not ts_indices:
        st.error("❌ No se encontraron archivos YMFS en timesteps_export/")
        return

    st.success(f"✅ {len(ts_indices)} timesteps cargados")

    # Preprocesar datos
    cache_file = CACHE_DIR / f"data_thr{threshold:.2f}.json"
    
    if cache_file.exists():
        with st.spinner("Cargando datos preprocesados..."):
            with open(cache_file, "r") as f:
                processed_data = json.load(f)
    else:
        with st.spinner("Preprocesando datos (solo la primera vez)..."):
            processed_data = preprocess_all_data(ymfs_by_ts, ts_indices, threshold)
            with open(cache_file, "w") as f:
                json.dump(processed_data, f)

    st.info(f"📊 Total de celdas activas en todos los timesteps: {sum(processed_data['data'][str(ts)]['count'] for ts in ts_indices)}")

    # Crear HTML
    html_content = create_viewer_html(json.dumps(processed_data))
    
    # Mostrar
    components.html(html_content, height=900, scrolling=False)


if __name__ == "__main__":
    main()
