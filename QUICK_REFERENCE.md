# 🚀 GeoViz - Guía de Referencia Rápida

## ⚡ Inicio Rápido

```bash
# Iniciar aplicación
streamlit run app.py

# URL: http://localhost:8501
```

## 🎨 Tema de Colores

| Color | Hex | Uso |
|-------|-----|-----|
| 🔵 Primary | `#3984c6` | Botones, enlaces, highlights |
| ⬛ Background | `#13191f` | Fondo principal |
| ⬛ Surface | `#1b232b` | Tarjetas, sidebar |
| ⬜ Text Primary | `#f8fafc` | Texto principal |
| 🔘 Text Secondary | `#9bafbf` | Subtítulos, captions |

## 📍 Navegación

| Página | Atajos | Descripción |
|--------|--------|-------------|
| 🏠 Inicio | - | Landing page con categorías |
| 🗺️ Bunter | `CO₂` + `Propiedades` | Visualización completa |
| 💧 Salinas | - | En desarrollo |
| 📊 Simulaciones | Parámetros en sidebar | Dashboard configurable |
| 🔬 Propiedades | Individual/Paralelo | Análisis geológico |

## 🎮 Controles Principales

### Viewer CO₂

| Control | Función |
|---------|---------|
| **Slider Timestep** | Navegar entre momentos temporales |
| **▶ Play** | Reproducir animación |
| **◀ ▶** | Anterior/Siguiente timestep |
| **Z Scale** | Ajustar escala vertical (1-20) |
| **☑ Inyectores** | Mostrar/ocultar pozos |
| **Umbral YMFS** | Filtrar celdas (0.0-1.0) |

### Propiedades Geológicas

| Control | Función |
|---------|---------|
| **Corte X** | Plano YZ (0 a nx-1) |
| **Corte Y** | Plano XZ (0 a ny-1) |
| **Corte Z** | Plano XY (0 a nz-1) |
| **Colormap** | 12 opciones (Hot, Viridis, etc.) |
| **☑ Escala log** | Transformación log10 |
| **Modo** | Individual o Paralelo |

## 📊 Propiedades Disponibles

| Propiedad | Archivo | Colormap | Escala |
|-----------|---------|----------|--------|
| Permeabilidad | `permeability.npy` | Hot | Log ✓ |
| Porosidad | `porosity.npy` | Viridis | Lineal |
| Facies | `facies.npy` | Discreto | - |

### Facies

- **2** = Shalty (Marrón `#8b5a2b`)
- **3** = Sand (Dorado `#ffd700`)

## 🎯 Casos de Uso Rápidos

### 1. Ver Evolución CO₂
```
Bunter → Viewer CO₂ → ▶ Play
```

### 2. Comparar Propiedades
```
Propiedades → Paralelo → Ajustar cortes
```

### 3. Configurar Simulación
```
Simulaciones → Sidebar (ajustar) → Ver resultado
```

### 4. Analizar Facies
```
Propiedades → Facies → Leer estadísticas
```

## 🔧 Parámetros de Simulación

| Parámetro | Rango | Default | Unidad |
|-----------|-------|---------|--------|
| Profundidad | 1000-4000 | 2500 | m |
| Presión | 50-300 | 150 | bar |
| Saturación CO₂ | 0-100 | 85 | % |
| Tiempo | 1-100 | 50 | años |

## 💾 Estructura de Archivos

```
data/geosx/          → Archivos .npy
timesteps_export/    → YMFS, PRESSURE, etc.
outputs/cache/       → Caché automático
outputs/html/        → Visualizaciones exportadas
```

## 📏 Dimensiones Típicas

### Grid
- **X**: 100 celdas
- **Y**: 100 celdas
- **Z**: 10 capas
- **Total**: 100,000 celdas

### Dominio
- **X**: 0 - 10,000 m
- **Y**: 0 - 10,000 m
- **Z**: -2,500 a -2,700 m (200m espesor)

## 🎨 Componentes HTML Personalizados

### Glass Card
```html
<div class="glass-card">
  <!-- contenido -->
</div>
```

### Metric Card
```html
<div class="metric-card">
  <div class="metric-title">Título</div>
  <div class="metric-value">1234</div>
</div>
```

### Status Indicator
```html
<p class="status-indicator">
  <span class="status-dot"></span>
  Activo
</p>
```

## 🔤 Iconos Material Symbols

| Icono | Código |
|-------|--------|
| ⛰️ | `landscape` |
| 💧 | `water_drop` |
| 📊 | `bar_chart_4_bars` |
| ⛽ | `gas_meter` |
| 🌊 | `waves` |
| 📐 | `layers` |
| 📁 | `upload_file` |
| 🌙 | `dark_mode` |

## ⌨️ Atajos de Teclado

| Tecla | Función |
|-------|---------|
| `R` | Rerun app (si está habilitado) |
| `C` | Clear cache |
| `/` | Buscar en sidebar |
| `ESC` | Cerrar modales |

## 📊 Métricas del Viewer CO₂

| Métrica | Descripción |
|---------|-------------|
| **Timesteps Totales** | Número de pasos temporales |
| **Celdas Activas** | Suma total de celdas con CO₂ |
| **Máx. Celdas** | Pico en un timestep |
| **Umbral YMFS** | Valor de corte actual |
| **FPS** | Frames por segundo (animación) |

## 🎨 Colormaps Recomendados

| Propiedad | Colormap | Razón |
|-----------|----------|-------|
| Permeabilidad | Hot | Contraste alto, intuitivo |
| Porosidad | Viridis | Perceptualmente uniforme |
| Facies | Discreto | Categorías claras |
| Presión | Plasma | Gradiente suave |
| Saturación | Turbo | Rango completo |

## 🐛 Solución Rápida de Problemas

| Problema | Solución |
|----------|----------|
| No carga datos | Verificar `data/geosx/` |
| Viewer lento | Aumentar umbral YMFS |
| Sin timesteps | Verificar `timesteps_export/` |
| Gráfico negro | Refrescar navegador (F5) |
| Sidebar oculto | Recargar app |

## 📚 Documentación Completa

| Documento | Contenido |
|-----------|-----------|
| `GEOVIZ_README.md` | Overview completo |
| `GUIA_USUARIO.md` | Manual detallado |
| `GEOVIZ_DESIGN.md` | Sistema de diseño |
| `INSTRUCCIONES_STREAMLIT.md` | Streamlit específico |
| `STRUCTURE.md` | Arquitectura |

## 🔗 Enlaces Útiles

- **Streamlit**: https://docs.streamlit.io/
- **Plotly**: https://plotly.com/python/
- **Material Icons**: https://fonts.google.com/icons
- **NumPy**: https://numpy.org/doc/

## 💡 Tips Pro

1. **Performance**: Usa umbrales >0.4 para cargas rápidas
2. **Exploración**: Modo paralelo para análisis holístico
3. **Exportación**: Click derecho en gráficos Plotly → Download
4. **Comparación**: Screenshots con diferentes parámetros
5. **Caché**: Primer acceso lento, siguientes instantáneos

## 🎯 Workflow Típico

```
1. Inicio → Seleccionar reservorio
2. Bunter → Viewer CO₂ → Ajustar umbral
3. Play animation → Observar evolución
4. Propiedades → Modo paralelo
5. Ajustar cortes → Identificar zonas
6. Simulaciones → Configurar parámetros
7. Exportar resultados
```

## 📊 Formato de Datos

### Archivos .npy
```python
# Shape esperado
(nz, ny, nx)         # 3D
(nt, nz, ny, nx)     # 4D con tiempo
```

### Archivos GRDECL
```
PROPIEDAD
  valores valores valores
  ...
/
```

## 🎨 Variables CSS

```css
--primary: #3984c6
--background-dark: #13191f
--surface-dark: #1b232b
--text-primary-dark: #f8fafc
--text-secondary-dark: #9bafbf
--border-dark: #3c4e5d
```

## 🚀 Comandos Útiles

```bash
# Instalar
pip install -r requirements.txt

# Ejecutar
streamlit run app.py

# Con auto-reload
streamlit run app.py --server.runOnSave true

# Puerto personalizado
streamlit run app.py --server.port 8080

# Limpiar caché
rm -rf outputs/cache/*
```

---

<div align="center">

**GeoViz Quick Reference v2.0**

[Inicio](#-geoviz---guía-de-referencia-rápida) • 
[Controles](#-controles-principales) • 
[Casos de Uso](#-casos-de-uso-rápidos) • 
[Tips](#-tips-pro)

</div>

