# GeoViz - Sistema de Diseño

## 🎨 Paleta de Colores

La aplicación utiliza un sistema de diseño moderno y profesional inspirado en las mejores prácticas de UI/UX:

### Colores Principales
- **Primary**: `#3984c6` - Azul principal para acciones y elementos interactivos
- **Background Dark**: `#13191f` - Fondo oscuro principal
- **Surface Dark**: `#1b232b` - Superficies y tarjetas
- **Text Primary**: `#f8fafc` - Texto principal (claro)
- **Text Secondary**: `#9bafbf` - Texto secundario
- **Border Dark**: `#3c4e5d` - Bordes y divisores

## 📐 Componentes de Diseño

### 1. Glass Cards (Tarjetas de Cristal)
Tarjetas con efecto de cristal esmerilado que usan:
- `backdrop-filter: blur(10px)` para efecto glassmorphism
- Bordes semi-transparentes
- Transiciones suaves al hacer hover
- Elevación sutil con sombras

```css
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
}
```

### 2. Metric Cards (Tarjetas de Métricas)
Tarjetas para mostrar KPIs y estadísticas importantes:
- Título descriptivo en texto secundario
- Valor grande y prominente
- Efecto hover interactivo

### 3. Navegación en Sidebar
- Logo personalizado con gradiente
- Navegación por radio buttons estilizados
- Controles de parámetros con sliders modernos

## 🔤 Tipografía

**Fuente Principal**: Space Grotesk
- Moderna y geométrica
- Excelente legibilidad en pantallas
- Pesos: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semi-bold), 700 (Bold), 900 (Black)

### Jerarquía de Títulos
- **H1**: 2.5rem, peso 900, tracking -0.033em (Títulos principales)
- **H2**: 1.5rem, peso 700 (Secciones)
- **H3**: 1.125rem, peso 700 (Subsecciones)
- **Body**: 1rem, peso 400 (Texto normal)
- **Caption**: 0.875rem, peso 400 (Texto secundario)

## 🎯 Características del Diseño

### Modo Oscuro Profesional
- Fondo oscuro que reduce la fatiga visual
- Alto contraste para elementos importantes
- Colores vibrantes pero no excesivos

### Animaciones y Transiciones
- Transiciones suaves (0.3s ease) para todos los elementos interactivos
- Efecto de elevación al hacer hover
- Indicador de estado con animación de pulso

### Iconografía
Usa Material Symbols Outlined de Google:
```html
<span class="material-symbols-outlined">icon_name</span>
```

Íconos disponibles:
- `gas_meter` - Reservorios de gas
- `waves` - Acuíferos
- `layers` - Capas geológicas
- `landscape` - Paisaje/Bunter
- `water_drop` - Agua/Salinas
- `bar_chart_4_bars` - Simulaciones

## 📱 Estructura de Navegación

### Páginas Principales
1. **🏠 Inicio**: Página de bienvenida con tarjetas de categorías
2. **🗺️ Bunter**: Visualización de reservorio Bunter (CO₂ + Propiedades)
3. **💧 Salinas**: Acuíferos salinas (en desarrollo)
4. **📊 Simulaciones**: Dashboard de simulaciones con parámetros ajustables
5. **🔬 Propiedades**: Visualización detallada de propiedades geológicas

## 🛠️ Componentes Personalizados

### Status Indicator
Indicador de estado con punto animado:
```html
<p class="status-indicator">
    <span class="status-dot"></span>
    Simulación Activa
</p>
```

### Metric Card
```html
<div class="metric-card">
    <div class="metric-title">Título</div>
    <div class="metric-value">Valor</div>
</div>
```

## 🎨 Mejores Prácticas

1. **Espaciado Consistente**: Usa múltiplos de 0.5rem (8px) para padding y margins
2. **Border Radius**: 0.5rem para elementos pequeños, 1rem para tarjetas
3. **Transiciones**: Siempre incluye `transition: all 0.3s ease` en elementos interactivos
4. **Hover States**: Todos los elementos clickeables deben tener un estado hover visible
5. **Accesibilidad**: Mantén contraste mínimo de 4.5:1 para texto normal

## 🚀 Uso en Streamlit

El tema se aplica automáticamente al llamar `apply_geoviz_theme()` al inicio de la aplicación. Todos los componentes nativos de Streamlit están estilizados para coincidir con el sistema de diseño.

### Ejemplo de Tarjeta Personalizada
```python
st.markdown('''
<div class="glass-card">
    <span class="material-symbols-outlined" 
          style="font-size: 3rem; color: var(--primary);">
        icon_name
    </span>
    <h3>Título</h3>
    <p>Descripción</p>
</div>
''', unsafe_allow_html=True)
```

## 📊 Gráficos Plotly

Los gráficos de Plotly están configurados con:
- Fondo transparente que se integra con el tema oscuro
- Colormaps apropiados: 'Hot', 'Viridis', 'Plasma'
- Dimensiones responsivas

---

**Diseñado con ❤️ para visualización de datos geológicos**

