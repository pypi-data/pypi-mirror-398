
# matrice\_streaming

**matrice\_streaming** is a high-performance, Cython-compiled Python package providing streaming, client, and deployment utilities for Matrice.ai services.
It offers ready-to-use streaming gateways, client management, camera handling, and deployment orchestration with complete type stubs for IDEs.

## Features

* **Cython Compiled** – Optimized performance via C extensions.
* **Streaming Gateway** – Real-time streaming and inference processing.
* **Client Management** – Deploy clients with streaming capabilities.
* **Camera Management** – Handle multiple camera streams and configurations.
* **Auto Streaming** – Automated streaming workflows with intelligent routing.
* **Deployment Tools** – Complete deployment and pipeline management.
* **Type Hints & Stubs** – `.pyi` stubs for full IDE autocomplete and docstring support.
* **Modular Design** – Clear separation of client, deployment, and streaming components.

## Installation

```bash
pip install --index-url https://test.pypi.org/simple/ matrice_streaming
```

## Example Usage

```python
from matrice_streaming import StreamingGateway, AutoStreaming
from matrice_streaming import CameraManager, Deployment

# Example: Create streaming gateway
gateway = StreamingGateway(
    model_input_type="video",
    input_config=input_config,
    output_config=output_config
)

# Example: Auto streaming setup
auto_stream = AutoStreaming()
auto_stream.start_streaming()
```
