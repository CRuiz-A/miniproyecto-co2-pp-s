# 🌍 GeoViz - Visualizador Geológico de CO₂

![Version](https://img.shields.io/badge/version-2.0-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)
![Python](https://img.shields.io/badge/python-3.8+-green)

## 🎨 Descripción

**GeoViz** es una aplicación moderna de visualización geológica desarrollada con Streamlit, diseñada específicamente para el análisis de reservorios de CO₂ y propiedades geológicas. Presenta un diseño profesional inspirado en las mejores prácticas de UI/UX con un tema oscuro elegante y componentes interactivos.

## ✨ Características Principales

### 🎯 Nuevo Sistema de Diseño (v2.0)

- **Tema Oscuro Profesional** con paleta de colores moderna
- **Glass Cards** con efecto glassmorphism
- **Tipografía Space Grotesk** para máxima legibilidad
- **Animaciones suaves** y transiciones fluidas
- **Iconografía Material Symbols** de Google
- **Métricas interactivas** con tarjetas estilizadas

### 📊 Módulos de Visualización

#### 1. Viewer CO₂ 3D Interactivo
- Visualización en tiempo real de la pluma de CO₂
- Navegación por timesteps con animación automática
- Control de umbral YMFS configurable
- Métricas en vivo (celdas activas, timesteps, etc.)
- Zoom y escala Z ajustable
- Toggle de pozos inyectores

#### 2. Propiedades Geológicas
**Dos modos de visualización:**

**Modo Individual:**
- Visualización detallada de una propiedad a la vez
- 12 colormaps disponibles
- Escala logarítmica opcional
- Controles de corte en 3 ejes (X, Y, Z)

**Modo Paralelo:**
- Visualización simultánea de 3 propiedades
- Controles sincronizados
- Comparación lado a lado de:
  - Permeabilidad (colormap Hot)
  - Porosidad (colormap Viridis)
  - Facies (colores discretos)

#### 3. Simulaciones Avanzadas
- Dashboard con parámetros configurables:
  - Profundidad (1000-4000m)
  - Presión de inyección (50-300 bar)
  - Saturación de CO₂ (0-100%)
  - Escala temporal (1-100 años)
- Integración con viewer CO₂

#### 4. Navegación por Reservorios
- **Bunter**: Reservorios de gas vaciado
- **Salinas**: Acuíferos salinos
- **Otros Yacimientos**: Formaciones geológicas diversas

## 🚀 Inicio Rápido

### Requisitos Previos

```bash
# Python 3.8 o superior
python --version

# Dependencias (ver requirements.txt)
streamlit>=1.28.0
plotly>=5.14.0
numpy>=1.24.0
```

### Instalación

```bash
# Clonar o navegar al directorio
cd /home/spell/Desktop/pyvista

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

### Estructura de Datos

Coloca tus archivos de datos en las siguientes ubicaciones:

```
pyvista/
├── data/
│   └── geosx/
│       ├── permeability.npy  # Array 3D/4D de permeabilidad
│       ├── porosity.npy      # Array 3D/4D de porosidad
│       └── facies.npy        # Array 3D/4D de facies
└── timesteps_export/
    ├── YMFS_ts_0000.GRDECL   # Timesteps de CO₂
    ├── YMFS_ts_0001.GRDECL
    └── ...
```

## 📚 Documentación

### Archivos de Documentación

- **`GEOVIZ_DESIGN.md`**: Guía completa del sistema de diseño
  - Paleta de colores
  - Componentes UI
  - Tipografía
  - Mejores prácticas

- **`GUIA_USUARIO.md`**: Manual de usuario detallado
  - Navegación paso a paso
  - Casos de uso
  - Resolución de problemas
  - Consejos y trucos

- **`STRUCTURE.md`**: Estructura del proyecto
- **`INSTRUCCIONES_STREAMLIT.md`**: Instrucciones específicas de Streamlit

## 🎨 Sistema de Diseño

### Paleta de Colores

```css
--primary: #3984c6           /* Azul principal */
--background-dark: #13191f   /* Fondo oscuro */
--surface-dark: #1b232b      /* Superficies */
--text-primary-dark: #f8fafc /* Texto principal */
--text-secondary-dark: #9bafbf /* Texto secundario */
--border-dark: #3c4e5d       /* Bordes */
```

### Componentes Principales

#### Glass Card
```html
<div class="glass-card">
    <!-- Contenido -->
</div>
```

#### Metric Card
```html
<div class="metric-card">
    <div class="metric-title">Título</div>
    <div class="metric-value">Valor</div>
</div>
```

#### Status Indicator
```html
<p class="status-indicator">
    <span class="status-dot"></span>
    Estado Activo
</p>
```

## 🔧 Características Técnicas

### Tecnologías

- **Frontend**: Streamlit + HTML/CSS personalizado
- **Visualización 3D**: Plotly.js
- **Procesamiento**: NumPy
- **Caché**: JSON + Streamlit cache_data
- **Fonts**: Google Fonts (Space Grotesk)
- **Icons**: Material Symbols Outlined

### Optimizaciones

1. **Caché Inteligente**
   - Los datos procesados se cachean por umbral
   - Carga instantánea en visitas posteriores
   - Ubicación: `outputs/cache/`

2. **Renderizado Eficiente**
   - Solo se procesan celdas activas (> umbral)
   - Mesh triangular optimizado para Plotly
   - Lazy loading de propiedades geológicas

3. **Responsive Design**
   - Layout adaptativo
   - Gráficos con `use_container_width=True`
   - Sidebar colapsable

## 📊 Casos de Uso

### 1. Análisis Temporal de CO₂
```
Bunter → Viewer CO₂ → Ajustar umbral → Play animation
```
Observa cómo evoluciona la pluma de CO₂ en el reservorio.

### 2. Correlación de Propiedades
```
Propiedades → Modo Paralelo → Ajustar cortes X/Y/Z
```
Identifica relaciones entre permeabilidad, porosidad y facies.

### 3. Diseño de Inyección
```
Simulaciones → Ajustar parámetros → Observar resultado
```
Simula diferentes escenarios de inyección de CO₂.

### 4. Caracterización de Facies
```
Propiedades → Seleccionar facies → Analizar distribución
```
Cuantifica la proporción de Shalty vs Sand en el reservorio.

## 🎯 Roadmap

### ✅ Completado (v2.0)
- [x] Nuevo sistema de diseño GeoViz
- [x] Glass cards con glassmorphism
- [x] Navegación por páginas
- [x] Métricas interactivas
- [x] Modo paralelo para propiedades
- [x] Documentación completa

### 🚧 En Desarrollo
- [ ] Módulo de Salinas
- [ ] Exportación de reportes PDF
- [ ] Comparación entre reservorios
- [ ] Modo claro/oscuro toggle

### 🔮 Futuro
- [ ] Integración con bases de datos
- [ ] API REST para datos
- [ ] Machine Learning para predicciones
- [ ] Colaboración multi-usuario

## 📝 Logs de Cambios

### v2.0.0 (2025-11-21)
**🎨 Rediseño Completo - Sistema GeoViz**

**Nuevo:**
- Sistema de diseño moderno con tema oscuro
- Glass cards con efecto glassmorphism
- Tipografía Space Grotesk
- Navegación por páginas con radio buttons
- Métricas con tarjetas estilizadas
- Indicadores de estado animados
- Iconografía Material Symbols

**Mejorado:**
- UI/UX completamente renovado
- Mejor organización de contenido
- Controles más intuitivos
- Visualizaciones más claras
- Documentación exhaustiva

**Técnico:**
- CSS modular y mantenible
- Componentes reutilizables
- Caché optimizado
- Performance mejorada

### v1.x (Anterior)
- Viewer CO₂ básico
- Visualización de propiedades
- Tema oscuro simple

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Familiarízate con `GEOVIZ_DESIGN.md`
2. Sigue las convenciones de código
3. Mantén la consistencia visual
4. Documenta nuevas características
5. Prueba en diferentes navegadores

## 📄 Licencia

Este proyecto es parte de un sistema de visualización geológica para análisis de almacenamiento de CO₂.

## 🙏 Agradecimientos

- **Tailwind CSS**: Inspiración para el sistema de diseño
- **Material Design**: Iconografía y principios de diseño
- **Streamlit**: Framework de aplicaciones
- **Plotly**: Visualizaciones 3D interactivas

## 📞 Soporte

Para preguntas, issues o sugerencias:

- Revisa `GUIA_USUARIO.md` para ayuda con el uso
- Consulta `GEOVIZ_DESIGN.md` para guías de diseño
- Verifica `STRUCTURE.md` para entender la estructura

---

<div align="center">

**Desarrollado con ❤️ para la visualización de datos geológicos**

![GeoViz](https://img.shields.io/badge/GeoViz-Visualizador%20Geol%C3%B3gico-3984c6?style=for-the-badge)

[Inicio](#-geoviz---visualizador-geológico-de-co₂) • 
[Documentación](#-documentación) • 
[Casos de Uso](#-casos-de-uso) • 
[Roadmap](#-roadmap)

</div>

---

### 🌟 Características Destacadas

| Característica | Descripción | Estado |
|---------------|-------------|--------|
| 🎨 Tema Oscuro | Diseño profesional con glassmorphism | ✅ |
| 📊 Viewer CO₂ | Visualización 3D interactiva | ✅ |
| 🔬 Propiedades | Análisis geológico detallado | ✅ |
| 📈 Métricas | KPIs en tiempo real | ✅ |
| 🎯 Simulaciones | Parámetros configurables | ✅ |
| 💧 Salinas | Módulo de acuíferos | 🚧 |
| 📱 Responsive | Adaptable a pantallas | ✅ |
| ⚡ Performance | Caché y optimización | ✅ |


