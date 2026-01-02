# drop_email

<p align="center">
  <img src="doc/example.png" alt="example email" width="600"/>
</p>

A Python package to send data (dictionaries, lists, pandas DataFrames) as beautiful HTML emails.

## Features

- 📧 Send data as beautiful HTML emails
- 📊 Beautiful pandas DataFrame rendering
- ⚙️ Configurable sender and receiver emails
- 🎨 Modern, responsive HTML templates

## Installation

```bash
pip install drop_email
```

Or install in development mode:

```bash
git clone <repository>
cd drop_email
pip install -e .
```

### Post-Installation: Initialize Configuration

Before using drop_email, you need to initialize the configuration file:

```bash
drop_email init
```

This creates a default configuration file. Then edit it with your email settings.

**Other CLI commands:**

```bash
# View configuration file path
drop_email config

# Show help
drop_email --help
```

## Quick Start

```python
import drop_email as de
import pandas as pd

# Create a sample DataFrame
df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['New York', 'London', 'Tokyo']
})

# Send the DataFrame as an email
de.send(df, subject="My Data Report")
```

## Configuration

### Configuration File Location

The package uses the following priority to locate the configuration file:

1. **Environment variable `DROP_EMAIL_CONFIG`** (recommended for stability)
   - Set to an absolute path for a fixed location that doesn't depend on home directory
   - Example: `export DROP_EMAIL_CONFIG="/path/to/drop_email/config.yaml"`

2. **XDG Standard location** (default)
   - `$XDG_CONFIG_HOME/drop_email/config.yaml` (if XDG_CONFIG_HOME is set)
   - `~/.config/drop_email/config.yaml` (fallback)

### Initial Setup

After installation, initialize the configuration file:

```bash
drop_email init
```

This creates the configuration file at the default location `~/.config/drop_email/config.yaml`. Then edit this file to configure:

- **Sender email**: Your email address and password (use App Password for Gmail)
- **SMTP settings**: SMTP server and port
- **Receiver emails**: List of recipient email addresses

### Use Environment Variable for Fixed Path

For maximum stability (especially if your home directory may change), set an environment variable:

```bash
# Linux/Mac
export DROP_EMAIL_CONFIG="/PATH_TO_YOUR/config.yaml"

# Windows (PowerShell)
$env:DROP_EMAIL_CONFIG="C:\path\to\drop_email\config.yaml"
```

Add this to your shell profile (`.bashrc`, `.zshrc`, etc.) to make it persistent.

### Example Configuration

```yaml
email:
  sender:
    address: "your_email@example.com"
    password: "your_app_password"
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
  receivers:
    - "receiver1@example.com"
    - "receiver2@example.com"
```

### View Configuration Path

To see where your configuration file is located:

```bash
drop_email config
```

## License

MIT

