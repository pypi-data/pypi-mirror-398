# NetBox Optics Plugin

NetBox plugin for modeling Wavelength Division Multiplexing optical connections.

## Features

- **Optical Grid Types**: Define wavelength grid templates (DWDM, CWDM, FlexGrid)
- **Optical Grid Instances**: Create grid instances from templates
- **Wavelength Management**: Track individual wavelengths with their availability status
- **Optical Spans**: Model optical fiber connections between sites
- **Optical Connections**: Map interfaces to wavelengths on spans
- **Mux Device Support**: Map wavelengths to multiplexer ports
- **Validation**: Comprehensive validation of wavelength reservations and device assignments
- **REST API**: Full API support for automation

## Requirements

- Python 3.10 or higher
- NetBox 3.7.8 or later

## Installation

### From PyPI 

```bash
pip install netbox-optics
```

### From Source

```bash
# Build the package
pip install build
python -m build

# Install the wheel
pip install dist/netbox_optics-0.4.4-py3-none-any.whl
```

### From Git Repository

```bash
pip install git+https://github.com/dropbox/netbox-optics.git #todo url
```

### Configuration

Add to your NetBox `configuration.py`:

```python
PLUGINS = ['netbox_optics']

PLUGINS_CONFIG = {
    'netbox_optics': {}
}
```

Run database migrations:

```bash
python manage.py migrate netbox_optics
```

Restart NetBox services:

```bash
sudo systemctl restart netbox
```

## Usage

### Quick Start

1. **Define an Optical Grid Type** – Create a template with wavelength spacing (e.g., DWDM 50GHz, CWDM)
   - Navigate to: Plugins → Optical Grid Types → Add
   - Set spacing and add wavelengths

2. **Create an Optical Grid** – Instantiate a grid from a template
   - Navigate to: Plugins → Optical Grids → Add
   - Select a grid type

3. **Create an Optical Span** – Define fiber connection between sites
   - Navigate to: Plugins → Optical Spans → Add
   - Select sites A and B, assign a grid, set vendor circuit ID

4. **Create Optical Connections** – Link interfaces through wavelengths
   - Navigate to: Plugins → Optical Connections → Add
   - Select span, wavelength, and interfaces

5. **Optional: Map Mux Devices** – Assign wavelengths to multiplexer ports
   - Navigate to: Plugins → Mux Wavelength Maps → Add
   - Select mux device, port, and wavelength

### API Usage

```python
import requests

# Get all optical spans
response = requests.get(
    'https://netbox.example.com/api/plugins/optics/optical-spans/',
    headers={'Authorization': 'Token YOUR_TOKEN'}
)

# Create an optical connection
response = requests.post(
    'https://netbox.example.com/api/plugins/optics/optical-connections/',
    headers={'Authorization': 'Token YOUR_TOKEN'},
    json={
        'span': 1,
        'wavelength': 1000.00,
        'interface_a': 100,
        'interface_z': 200,
        'tx_power': 10
    }
)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/dropbox/netbox-optics.git #todo url
cd netbox-optics

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### NetBox Development Environment

```bash
# Clone NetBox (if not already available)
git clone https://github.com/netbox-community/netbox.git
cd netbox

# Install the plugin
pip install -e /path/to/netbox-optics

# Add to configuration.py
echo "PLUGINS = ['netbox_optics']" >> netbox/netbox/configuration.py

# Run migrations
python manage.py migrate netbox_optics

# Start development server
python manage.py runserver
```

### Code Quality

```bash
# Lint the code
flake8 netbox_optics/

# Format code
black netbox_optics/
```

### Testing

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests with NetBox API token
export netbox_token=your_token_here
pytest tests/e2e_tests/ -v -s
```

### Building

```bash
# Install build tool
pip install build

# Build distribution packages
python -m build

# Output: dist/netbox_optics-0.4.4.tar.gz and dist/netbox_optics-0.4.4-py3-none-any.whl
```

## Documentation

- **API Documentation**: Available at `/api/plugins/optics/` on your NetBox instance

## Support

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/dropbox/netbox-optics/issues) # todo url

## Acknowledgments

Thanks to Dropbox for supporting open source development!

## License

```
Copyright (c) 2025 Dropbox, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

See [LICENSE](LICENSE) file for full license text.