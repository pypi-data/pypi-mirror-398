# Installation

## Installation Methods

### 1. Direct installation from Git (Recommended for internal use)

```bash
pip install git+https://github.com/yourcompany/prestashop-webservice.git
```

### 2. Installation from Git with specific version

```bash
pip install git+https://github.com/yourcompany/prestashop-webservice.git@v0.1.0
```

### 3. Installation in development mode

```bash
git clone https://github.com/yourcompany/prestashop-webservice.git
cd prestashop-webservice
pip install -e .
```

### 4. Installation with development dependencies

```bash
pip install -e ".[dev]"
```

### 5. Using requirements.txt

Add to your `requirements.txt`:

```
git+https://github.com/yourcompany/prestashop-webservice.git@v0.1.0
```

Then install:

```bash
pip install -r requirements.txt
```

### 6. Using as Git submodule

```bash
# Add as submodule
git submodule add https://github.com/yourcompany/prestashop-webservice.git libs/prestashop-webservice

# Install
pip install -e libs/prestashop-webservice
```

## Verify installation

```python
import prestashop_webservice
print(prestashop_webservice.__version__)
```

## Requirements

- Python >= 3.10
- httpx >= 0.25.0
- cachetools >= 5.3.0
- loguru >= 0.7.0

## Troubleshooting

### Error: No module named 'prestashop_webservice'

Make sure you have installed the package correctly:

```bash
pip list | grep prestashop
```

### Permission errors

On some systems you will need to use `sudo` or install in a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install git+https://github.com/yourcompany/prestashop-webservice.git
```

### Update to latest version

```bash
pip install --upgrade git+https://github.com/yourcompany/prestashop-webservice.git
```
