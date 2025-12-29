# Mac Cleaner 🧹

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

<a href="https://www.buymeacoffee.com/nmlemus" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

[English](#english) | [Español](#español)

---

## English

A safe and intelligent disk cleaning utility for macOS that helps you reclaim disk space by identifying and removing temporary files, caches, and development artifacts.

### Features

- **Smart Categorization**: Organizes cleanable files into logical categories
- **Safety First**: Built-in protections prevent deletion of critical system files
- **Interactive Selection**: Choose exactly what to clean with an easy-to-use CLI
- **Dry-Run Mode**: Preview what will be deleted before making changes
- **Multi-language Support**: Automatically detects your system language (English/Spanish)
- **Developer-Friendly**: Finds and cleans node_modules, Docker data, build caches, and more

### What It Cleans

Mac Cleaner safely identifies and removes:

1. **Temporary Files**: System and application temporary files
2. **System Logs**: Log files from macOS and applications
3. **Homebrew Cache**: Downloaded packages and build artifacts
4. **Browser Cache**: Cache from Safari, Chrome, Firefox, Brave, Edge
5. **Node Modules**: `node_modules` directories in your projects
6. **User Caches**: Application caches (excluding Apple system caches)
7. **Development Caches**: Xcode, npm, pip, yarn, CocoaPods, Cargo, Gradle
8. **Docker Data**: Unused Docker images, containers, and volumes

### Installation

#### From PyPI (when published)

```bash
pip install mac-cleaner
```

#### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/mac-cleaner.git
cd mac-cleaner

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Usage

#### Basic Usage

```bash
mac-cleaner
```

This will:
1. Scan your system for cleanable files
2. Display categories with size information
3. Let you select what to clean
4. Ask for confirmation before deleting

#### Dry-Run Mode

Preview what will be deleted without making changes:

```bash
mac-cleaner --dry-run
```

#### Examples

**Clean everything:**
```bash
$ mac-cleaner
Scanning categories...
Categories found:
 1) Temporary Files               2.3 GB (4 items)
 2) System Log Files              856.2 MB (3 items)
 3) Browser Cache                 1.2 GB (5 items)
 4) Node Modules                  4.5 GB (12 items)
 5) Development Cache             3.1 GB (6 items)

Select categories (e.g., 1,3,5 or all):
> all
```

**Clean specific categories:**
```bash
Select categories (e.g., 1,3,5 or all):
> 3,4,5
```

### Safety Features

Mac Cleaner includes multiple layers of protection:

- ✅ **Whitelist approach**: Only cleans known safe locations
- ✅ **Critical path protection**: Prevents deletion of system directories
- ✅ **Apple file protection**: Skips files starting with `com.apple.`
- ✅ **Permission handling**: Gracefully handles permission-denied errors
- ✅ **macOS SIP protection**: Respects System Integrity Protection
- ✅ **User confirmation**: Always asks before deleting
- ✅ **Dry-run mode**: Test before committing to changes

### Requirements

- macOS 10.13 or later
- Python 3.8 or later
- Optional: Docker (for Docker cleanup feature)
- Optional: gettext (for translation compilation)

### Development

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/mac-cleaner.git
cd mac-cleaner

# Install with dev dependencies
pip install -e ".[dev]"
```

#### Running Tests

```bash
pytest
```

#### Code Formatting

```bash
black mac_cleaner/
```

#### Type Checking

```bash
mypy mac_cleaner/
```

#### Updating Translations

1. Edit `.po` files in `mac_cleaner/locales/*/LC_MESSAGES/`
2. Compile translations:
   ```bash
   python compile_translations.py
   ```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Disclaimer

While Mac Cleaner is designed with safety in mind, always ensure you have backups of important data. The authors are not responsible for any data loss.

---

## Español

Una utilidad segura e inteligente de limpieza de disco para macOS que te ayuda a recuperar espacio eliminando archivos temporales, cachés y artefactos de desarrollo.

### Características

- **Categorización Inteligente**: Organiza archivos limpiables en categorías lógicas
- **Seguridad Primero**: Protecciones integradas previenen la eliminación de archivos críticos del sistema
- **Selección Interactiva**: Elige exactamente qué limpiar con una CLI fácil de usar
- **Modo Simulación**: Previsualiza qué se eliminará antes de hacer cambios
- **Soporte Multi-idioma**: Detecta automáticamente el idioma de tu sistema (Inglés/Español)
- **Amigable para Desarrolladores**: Encuentra y limpia node_modules, datos de Docker, cachés de compilación, y más

### Qué Limpia

Mac Cleaner identifica y elimina de forma segura:

1. **Archivos Temporales**: Archivos temporales del sistema y aplicaciones
2. **Logs del Sistema**: Archivos de log de macOS y aplicaciones
3. **Caché de Homebrew**: Paquetes descargados y artefactos de compilación
4. **Caché de Navegadores**: Caché de Safari, Chrome, Firefox, Brave, Edge
5. **Node Modules**: Directorios `node_modules` en tus proyectos
6. **Cachés de Usuario**: Cachés de aplicaciones (excluyendo cachés del sistema de Apple)
7. **Cachés de Desarrollo**: Xcode, npm, pip, yarn, CocoaPods, Cargo, Gradle
8. **Datos de Docker**: Imágenes, contenedores y volúmenes de Docker no usados

### Instalación

#### Desde PyPI (cuando se publique)

```bash
pip install mac-cleaner
```

#### Desde el Código Fuente

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/mac-cleaner.git
cd mac-cleaner

# Instalar en modo desarrollo
pip install -e .

# O instalar normalmente
pip install .
```

### Uso

#### Uso Básico

```bash
mac-cleaner
```

Esto:
1. Escanea tu sistema buscando archivos limpiables
2. Muestra categorías con información de tamaño
3. Te permite seleccionar qué limpiar
4. Pide confirmación antes de eliminar

#### Modo Simulación

Previsualiza qué se eliminará sin hacer cambios:

```bash
mac-cleaner --dry-run
```

#### Ejemplos

**Limpiar todo:**
```bash
$ mac-cleaner
Escaneando categorías...
Categorías encontradas:
 1) Archivos Temporales          2.3 GB (4 items)
 2) Archivos de Log del Sistema  856.2 MB (3 items)
 3) Caché de Navegadores         1.2 GB (5 items)
 4) Node Modules                 4.5 GB (12 items)
 5) Caché de Desarrollo          3.1 GB (6 items)

Selecciona categorías (ej: 1,3,5 o all):
> all
```

**Limpiar categorías específicas:**
```bash
Selecciona categorías (ej: 1,3,5 o all):
> 3,4,5
```

### Características de Seguridad

Mac Cleaner incluye múltiples capas de protección:

- ✅ **Enfoque de lista blanca**: Solo limpia ubicaciones conocidas y seguras
- ✅ **Protección de rutas críticas**: Previene la eliminación de directorios del sistema
- ✅ **Protección de archivos Apple**: Omite archivos que comienzan con `com.apple.`
- ✅ **Manejo de permisos**: Maneja errores de permisos denegados de forma elegante
- ✅ **Protección SIP de macOS**: Respeta la Protección de Integridad del Sistema
- ✅ **Confirmación del usuario**: Siempre pide confirmación antes de eliminar
- ✅ **Modo simulación**: Prueba antes de comprometerte con los cambios

### Requisitos

- macOS 10.13 o posterior
- Python 3.8 o posterior
- Opcional: Docker (para la función de limpieza de Docker)
- Opcional: gettext (para compilar traducciones)

### Desarrollo

#### Configurar Entorno de Desarrollo

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/mac-cleaner.git
cd mac-cleaner

# Instalar con dependencias de desarrollo
pip install -e ".[dev]"
```

#### Ejecutar Tests

```bash
pytest
```

#### Formateo de Código

```bash
black mac_cleaner/
```

#### Verificación de Tipos

```bash
mypy mac_cleaner/
```

#### Actualizar Traducciones

1. Edita los archivos `.po` en `mac_cleaner/locales/*/LC_MESSAGES/`
2. Compila las traducciones:
   ```bash
   python compile_translations.py
   ```

### Contribuir

¡Las contribuciones son bienvenidas! No dudes en enviar un Pull Request.

### Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

### Descargo de Responsabilidad

Aunque Mac Cleaner está diseñado pensando en la seguridad, asegúrate siempre de tener copias de seguridad de datos importantes. Los autores no son responsables de ninguna pérdida de datos.
