import streamlit as st
import numpy as np
import plotly.graph_objects as go
import re
from pathlib import Path

st.set_page_config(page_title="CO2 Frames (Client-side)", page_icon="⚡", layout="wide")


def read_grdecl_property(filepath: str) -> np.ndarray:
    values = []
    reading = False
    with open(filepath, 'r') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('--'):
                continue
            if any(k in line for k in ['YMFS', 'SOIL', 'SWAT', 'SGAS', 'PRESSURE']):
                reading = True
                continue
            if line == '/' or line.startswith('/'):
                break
            if reading:
                parts = line.replace('/', '').split()
                for p in parts:
                    if '*' in p:
                        cnt, val = p.split('*')
                        try:
                            values.extend([float(val)] * int(cnt))
                        except Exception:
                            continue
                    else:
                        try:
                            values.append(float(p))
                        except Exception:
                            continue
    return np.array(values)


def build_voxels_from_values(ymfs_values: np.ndarray, threshold: float,
                             nx: int = 100, ny: int = 100, nz: int = 10):
    x_min, x_max = 0, 10000
    y_min, y_max = 0, 10000
    z_top, z_bottom = -2500, -2700

    cell_size_x = (x_max - x_min) / (nx - 1)
    cell_size_y = (y_max - y_min) / (ny - 1)
    cell_size_z = (z_bottom - z_top) / (nz - 1)

    total = nx * ny * nz
    if len(ymfs_values) < total:
        full = np.zeros(total)
        full[:len(ymfs_values)] = ymfs_values
        ymfs_values = full

    voxel_x, voxel_y, voxel_z = [], [], []
    voxel_i, voxel_j, voxel_k = [], [], []
    voxel_colors = []
    vtx_count = 0

    for k in range(nz - 1):
        for j in range(ny - 1):
            for i in range(nx - 1):
                idx = i + j * nx + k * nx * ny
                if ymfs_values[idx] >= threshold:
                    val = ymfs_values[idx]
                    x0 = x_min + i * cell_size_x
                    y0 = y_min + j * cell_size_y
                    z0 = z_top + k * cell_size_z
                    verts = [
                        [x0, y0, z0],
                        [x0 + cell_size_x, y0, z0],
                        [x0 + cell_size_x, y0 + cell_size_y, z0],
                        [x0, y0 + cell_size_y, z0],
                        [x0, y0, z0 + cell_size_z],
                        [x0 + cell_size_x, y0, z0 + cell_size_z],
                        [x0 + cell_size_x, y0 + cell_size_y, z0 + cell_size_z],
                        [x0, y0 + cell_size_y, z0 + cell_size_z]
                    ]
                    voxel_x.extend([v[0] for v in verts])
                    voxel_y.extend([v[1] for v in verts])
                    voxel_z.extend([v[2] for v in verts])
                    base = vtx_count
                    faces = [
                        [0,1,2],[0,2,3], [4,6,5],[4,7,6],
                        [0,4,5],[0,5,1], [2,6,7],[2,7,3],
                        [0,3,7],[0,7,4], [1,5,6],[1,6,2]
                    ]
                    for f in faces:
                        voxel_i.append(base + f[0])
                        voxel_j.append(base + f[1])
                        voxel_k.append(base + f[2])
                        voxel_colors.append(val)
                    vtx_count += 8
    return voxel_x, voxel_y, voxel_z, voxel_i, voxel_j, voxel_k, voxel_colors


def build_injector_cubes():
    wells = [
        (2500, 2500, -2500),
        (2500, 7500, -2500),
        (7500, 2500, -2500),
        (7438, 7438, -2500)
    ]
    cube_size = 200.0
    half = cube_size / 2.0
    all_x, all_y, all_z = [], [], []
    all_i, all_j, all_k = [], [], []
    base = 0
    faces = [
        [0,1,2],[0,2,3], [4,6,5],[4,7,6],
        [0,4,5],[0,5,1], [2,6,7],[2,7,3],
        [0,3,7],[0,7,4], [1,5,6],[1,6,2]
    ]
    for (cx, cy, cz) in wells:
        verts = [
            [cx - half, cy - half, cz - half],
            [cx + half, cy - half, cz - half],
            [cx + half, cy + half, cz - half],
            [cx - half, cy + half, cz - half],
            [cx - half, cy - half, cz + half],
            [cx + half, cy - half, cz + half],
            [cx + half, cy + half, cz + half],
            [cx - half, cy + half, cz + half]
        ]
        all_x.extend([v[0] for v in verts])
        all_y.extend([v[1] for v in verts])
        all_z.extend([v[2] for v in verts])
        for f in faces:
            all_i.append(base + f[0])
            all_j.append(base + f[1])
            all_k.append(base + f[2])
        base += 8
    return all_x, all_y, all_z, all_i, all_j, all_k


def load_all_timesteps():
    base = Path(__file__).parent
    tdir = base / 'timesteps_export'
    if not tdir.exists():
        return {}, []
    files = sorted(tdir.glob('YMFS_ts_*.GRDECL'))
    data = {}
    idxs = []
    for fp in files:
        m = re.search(r'ts_(\d+)', fp.name)
        if not m:
            continue
        ts = int(m.group(1))
        arr = read_grdecl_property(str(fp))
        data[ts] = arr
        idxs.append(ts)
    idxs.sort()
    return data, idxs


def build_figure_frames(ymfs_dict: dict, timestep_indices: list, threshold: float,
                        z_scale: int):
    frames = []
    first_ts = timestep_indices[0]
    x,y,z,i,j,k,intensity = build_voxels_from_values(ymfs_dict[first_ts], threshold)

    fig = go.Figure(
        data=[go.Mesh3d(
            x=x, y=y, z=z, i=i, j=j, k=k,
            intensity=intensity, colorscale='Hot', cmin=threshold, cmax=1.0,
            showscale=True, name=f'CO2 ts{first_ts}',
            flatshading=False, lighting=dict(ambient=0.7, diffuse=0.8, specular=0.2)
        )]
    )

    # Inyectores como trace fijo (index 1)
    inj_x, inj_y, inj_z, inj_i, inj_j, inj_k = build_injector_cubes()
    fig.add_trace(go.Mesh3d(
        x=inj_x, y=inj_y, z=inj_z, i=inj_i, j=inj_j, k=inj_k,
        color='blue', opacity=0.85, flatshading=True, name='Inyectores',
        showscale=False, visible=True
    ))

    for ts in timestep_indices:
        vx,vy,vz,vi,vj,vk,vcol = build_voxels_from_values(ymfs_dict[ts], threshold)
        frames.append(go.Frame(name=f"ts{ts}", data=[go.Mesh3d(
            x=vx, y=vy, z=vz, i=vi, j=vj, k=vk,
            intensity=vcol, colorscale='Hot', cmin=threshold, cmax=1.0,
            showscale=True, name=f'CO2 ts{ts}', flatshading=False,
            lighting=dict(ambient=0.7, diffuse=0.8, specular=0.2)
        )]))

    fig.frames = frames

    fig.update_layout(
        title=dict(text='CO2 (YMFS) - Control total en cliente', x=0.5),
        scene=dict(
            xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='Z (m)',
            aspectmode='manual', aspectratio=dict(x=1, y=1, z=z_scale),
            xaxis=dict(range=[0, 10000]), yaxis=dict(range=[0, 10000]),
            zaxis=dict(range=[-2700, -2500]),
            uirevision='fixed'
        ),
        width=1400, height=900, margin=dict(l=0, r=0, t=60, b=0),
        updatemenus=[
            # Play/Pause (solo una vez)
            dict(type='buttons', showactive=False, x=0.02, y=0.98,
                 buttons=[
                     dict(label='▶ Play', method='animate',
                          args=[None, dict(frame=dict(duration=300, redraw=True), fromcurrent=True,
                                           transition=dict(duration=0), repeat=False)]),
                     dict(label='⏸ Pause', method='animate',
                          args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate',
                                             transition=dict(duration=0))])
                 ]),
            # Escala Z (relayout, client-side)
            dict(type='buttons', direction='down', x=0.02, y=0.80, showactive=True,
                 buttons=[
                     dict(label='Z x1', method='relayout', args=[{'scene.aspectratio': {'x':1,'y':1,'z':1}}]),
                     dict(label='Z x5', method='relayout', args=[{'scene.aspectratio': {'x':1,'y':1,'z':5}}]),
                     dict(label='Z x8', method='relayout', args=[{'scene.aspectratio': {'x':1,'y':1,'z':8}}]),
                     dict(label='Z x10', method='relayout', args=[{'scene.aspectratio': {'x':1,'y':1,'z':10}}]),
                     dict(label='Z x15', method='relayout', args=[{'scene.aspectratio': {'x':1,'y':1,'z':15}}]),
                     dict(label='Z x20', method='relayout', args=[{'scene.aspectratio': {'x':1,'y':1,'z':20}}])
                 ]),
            # YMFS mínimo (cmin), client-side restyle del trace 0 (CO2)
            dict(type='buttons', direction='down', x=0.02, y=0.62, showactive=True,
                 buttons=[
                     dict(label='YMFS ≥ 0.05', method='restyle', args=[{'cmin': 0.05}, [0]]),
                     dict(label='YMFS ≥ 0.10', method='restyle', args=[{'cmin': 0.10}, [0]]),
                     dict(label='YMFS ≥ 0.15', method='restyle', args=[{'cmin': 0.15}, [0]]),
                     dict(label='YMFS ≥ 0.20', method='restyle', args=[{'cmin': 0.20}, [0]]),
                     dict(label='YMFS ≥ 0.30', method='restyle', args=[{'cmin': 0.30}, [0]])
                 ]),
            # Toggle inyectores (trace 1)
            dict(type='buttons', direction='down', x=0.02, y=0.44, showactive=True,
                 buttons=[
                     dict(label='Inyectores: ON', method='restyle', args=[{'visible': True}, [1]]),
                     dict(label='Inyectores: OFF', method='restyle', args=[{'visible': False}, [1]])
                 ]),
        ],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix='Timestep: ', visible=True),
            steps=[dict(method='animate', label=str(ts),
                        args=[[f"ts{ts}"], dict(mode='immediate', frame=dict(duration=0, redraw=True),
                                                 transition=dict(duration=0))])
                   for ts in timestep_indices]
        )]
    )
    return fig


def main():
    st.title("⚡ CO2 3D (Frames, sin reruns)")
    st.caption("Slider/Play, escala Z, YMFS mínimo y toggle de inyectores 100% en cliente (WebGL)")

    # Defaults: z=1
    threshold_default = 0.10
    z_scale_default = 1

    with st.spinner("Cargando timesteps..."):
        ymfs_by_ts, ts_indices = load_all_timesteps()
    if not ts_indices:
        st.error("No se encontraron timesteps en timesteps_export/YMFS_ts_*.GRDECL")
        return

    with st.spinner("Construyendo frames (única vez)..."):
        fig = build_figure_frames(ymfs_by_ts, ts_indices, threshold_default, z_scale_default)

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})


if __name__ == "__main__":
    main()
