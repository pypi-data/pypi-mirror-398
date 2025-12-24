# Chloros Python SDK

Official Python SDK for MAPIR Chloros image processing software. Provides programmatic access to the Chloros API for automation, integration, and custom workflows.

## 🚀 Quick Start

```python
from chloros_sdk import ChlorosLocal

# Initialize SDK (auto-starts backend)
chloros = ChlorosLocal()

# Create project and import images
chloros.create_project("MyProject", camera="Survey3N_RGN")
chloros.import_images("C:/DroneImages/Flight001")

# Configure settings
chloros.configure(
    vignette_correction=True,
    reflectance_calibration=True,
    indices=["NDVI", "NDRE", "GNDVI"]
)

# Process images
chloros.process(mode="parallel", wait=True)
```

### One-Line Processing

```python
from chloros_sdk import process_folder

results = process_folder("C:/DroneImages/Flight001", indices=["NDVI", "NDRE"])
```

## 📋 Requirements

| Requirement          | Details                                                             |
|---------------------|---------------------------------------------------------------------|
| **Chloros Desktop** | Must be installed locally                                           |
| **License**         | **Chloros+ required** ([paid plan](https://cloud.mapir.camera/pricing)) |
| **Operating System**| Windows 10/11 (64-bit)                                              |
| **Python**          | Python 3.7 or higher                                                |
| **Memory**          | 8GB RAM minimum (16GB recommended)                                  |

> **⚠️ License Requirement**: The Chloros SDK requires an active Chloros+ subscription. Standard (free) plans do not have API access. Upgrade at [https://cloud.mapir.camera/pricing](https://cloud.mapir.camera/pricing)

## 📥 Installation

### From PyPI (Recommended)

```bash
pip install chloros-sdk
```

### From Source

```bash
git clone https://github.com/mapircamera/chloros-sdk.git
cd chloros-sdk
pip install -e .
```

### With Progress Monitoring

```bash
pip install chloros-sdk[progress]
```

## 📖 Documentation

Complete documentation available at: **https://docs.chloros.com/api-python-sdk**

## 🎯 Use Cases

### Research & Academia
```python
# Integrate Chloros into analysis pipelines
import chloros_sdk
import pandas as pd

chloros = chloros_sdk.ChlorosLocal()

results = []
for survey in field_surveys:
    chloros.process(survey.images)
    ndvi_data = chloros.get_index_values("NDVI")
    results.append({'chloros_ndvi': ndvi_data, 'biomass': survey.biomass})

df = pd.DataFrame(results)
correlation = df.corr()
```

### Batch Processing
```python
# Process multiple flights automatically
from chloros_sdk import ChlorosLocal

chloros = ChlorosLocal()

for flight in flight_database:
    chloros.create_project(flight.name)
    chloros.import_images(flight.folder)
    chloros.configure(indices=flight.requested_indices)
    chloros.process()
```

### Custom Workflows
```python
# Advanced progress monitoring
def progress_callback(progress, message):
    print(f"[{progress}%] {message}")

chloros = ChlorosLocal()
chloros.create_project("CustomWorkflow")
chloros.import_images("C:/Data")
chloros.configure(indices=["NDVI", "NDRE"])
chloros.process(progress_callback=progress_callback)
```

## 🔑 License Activation

The SDK uses the same license as Chloros Desktop:

1. Open Chloros Desktop GUI
2. Login with your Chloros+ credentials (one-time)
3. SDK automatically uses cached license
4. License persists across reboots (30-day offline support)

## 🛠️ API Reference

### ChlorosLocal Class

Main SDK class for local Chloros processing.

```python
chloros = ChlorosLocal(
    api_url="http://localhost:5000",     # Backend URL
    auto_start_backend=True,             # Auto-start if not running
    backend_exe=None,                    # Auto-detect backend path
    timeout=30                           # Request timeout (seconds)
)
```

### Methods

#### `create_project(project_name, camera=None)`
Create a new Chloros project.

#### `import_images(folder_path, recursive=False)`
Import images from a folder.

#### `configure(**settings)`
Configure processing settings.

#### `process(mode="parallel", wait=True, progress_callback=None)`
Start processing images.

#### `get_config()`
Get current project configuration.

#### `get_status()`
Get backend status.

## 🔐 Security

- **Proprietary Software**: Licensed under MAPIR proprietary license
- **Local Processing**: All processing happens locally (localhost API)
- **License Enforcement**: Requires active Chloros+ subscription
- **No Data Transmission**: Images never leave your computer

## 💡 Examples

See complete examples in the [documentation](https://docs.chloros.com/api-python-sdk#complete-examples).

## 🐛 Support

- **Email**: info@mapir.camera
- **Website**: [https://www.mapir.camera](https://www.mapir.camera)
- **Documentation**: [https://docs.chloros.com](https://docs.chloros.com)
- **Pricing**: [https://cloud.mapir.camera/pricing](https://cloud.mapir.camera/pricing)

## 📄 License

Copyright (c) 2025 MAPIR Inc. All rights reserved.

This is proprietary software requiring an active Chloros+ subscription.
Unauthorized use, distribution, or modification is prohibited.

## 🔄 Version History

### v1.0.0 (2025)
- Initial release
- Full API coverage for local processing
- Auto-backend startup
- Progress monitoring support
- Context manager support














