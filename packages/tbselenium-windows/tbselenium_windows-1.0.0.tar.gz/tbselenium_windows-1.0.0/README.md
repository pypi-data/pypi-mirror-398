# tbselenium-windows

Tor Browser automation with Selenium for Windows.

This is a complete port of [tor-browser-selenium](https://github.com/webfp/tor-browser-selenium) specifically designed for Windows. It handles the Windows directory structure and provides a clean interface for automating Tor Browser.

## Features

- **Windows Native**: Designed specifically for the Windows Tor Browser layout
- **Selenium 4+ Support**: Full compatibility with modern Selenium
- **System Tor Integration**: Works with system Tor installations
- **Stem Support**: Launch Tor from the browser bundle using Stem
- **Headless Mode**: Run Tor Browser without a visible window
- **Custom Profiles**: Support for persistent and temporary profiles
- **Security Controls**: Set Tor Browser security levels programmatically

## Requirements

- **Windows** (tested on Windows 10+)
- **Python 3.8+**
- **Tor Browser for Windows** ([download](https://www.torproject.org/download/))
- **geckodriver** (download from [Mozilla releases](https://github.com/mozilla/geckodriver/releases))
- **Tor** (for system Tor mode: install via Chocolatey or use Tor Browser's bundled Tor)

## Installation

Download from PyPI:
```bash
pip install tbselenium-windows
```

Install manually:
```bash
git clone https://github.com/maximilianromer/tbselenium-windows.git
cd tbselenium-windows
pip install -e .
```

## Quick Start

### Basic Usage

```python
from tbselenium_windows import TorBrowserDriver

# Using Tor Browser with system Tor
with TorBrowserDriver(r"C:\Users\YourName\Desktop\Tor Browser") as driver:
    driver.load_url("https://check.torproject.org")
    print(driver.title)
    print(driver.find_element_by("h1.on").text)
```

### With Stem (Launch Tor from Bundle)

```python
from tbselenium_windows import TorBrowserDriver, launch_tbb_tor_with_stem, USE_STEM

TBB_PATH = r"C:\Users\YourName\Desktop\Tor Browser"

# Launch Tor using Stem
tor_process = launch_tbb_tor_with_stem(tbb_path=TBB_PATH)

# Use the browser with Stem-launched Tor
with TorBrowserDriver(TBB_PATH, tor_cfg=USE_STEM) as driver:
    driver.load_url("https://check.torproject.org")
    print(driver.title)

# Clean up
tor_process.kill()
```

### Headless Mode

```python
from tbselenium_windows import TorBrowserDriver

with TorBrowserDriver(r"C:\Users\YourName\Desktop\Tor Browser", headless=True) as driver:
    driver.load_url("https://check.torproject.org")
    driver.save_screenshot("screenshot.png")
```

### Custom Preferences

```python
from tbselenium_windows import TorBrowserDriver

# Disable images
pref_dict = {"permissions.default.image": 2}

with TorBrowserDriver(r"C:\Users\YourName\Desktop\Tor Browser", pref_dict=pref_dict) as driver:
    driver.load_url("https://example.com")
```

### Security Level

```python
from tbselenium_windows import TorBrowserDriver, set_security_level
from tbselenium_windows import TB_SECURITY_LEVEL_SAFEST

with TorBrowserDriver(r"C:\Users\YourName\Desktop\Tor Browser") as driver:
    set_security_level(driver, TB_SECURITY_LEVEL_SAFEST)
    driver.load_url("https://example.com")
```

## Configuration Options

### TorBrowserDriver Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tbb_path` | str | "" | Path to Tor Browser directory |
| `tor_cfg` | int | USE_RUNNING_TOR | Tor configuration mode |
| `tbb_fx_binary_path` | str | "" | Direct path to firefox.exe |
| `tbb_profile_path` | str | "" | Custom profile path |
| `tbb_logfile_path` | str | "" | Path for browser logs |
| `tor_data_dir` | str | "" | Custom Tor data directory |
| `executable_path` | str | auto | Path to geckodriver |
| `pref_dict` | dict | {} | Custom Firefox preferences |
| `socks_port` | int | 9050 | SOCKS proxy port |
| `control_port` | int | 9051 | Tor control port |
| `extensions` | list | [] | List of .xpi files to install |
| `default_bridge_type` | str | "" | Tor bridge type |
| `headless` | bool | False | Run in headless mode |
| `use_custom_profile` | bool | False | Use persistent profile |
| `geckodriver_port` | int | 0 | geckodriver port (0=random) |
| `marionette_port` | int | 0 | Marionette port (0=don't set, only with use_custom_profile) |

### Tor Configuration Modes

- `USE_RUNNING_TOR` (default): Use system Tor running on port 9050
- `USE_STEM`: Use Tor launched via Stem library on port 9250

### Port Defaults

| Mode | SOCKS Port | Control Port |
|------|------------|--------------|
| System Tor | 9050 | 9051 |
| TBB Tor | 9150 | 9151 |
| Stem | 9250 | 9251 |

## Windows-Specific Notes

### Directory Structure

Tor Browser on Windows uses this structure:

```
Tor Browser/
├── Browser/
│   ├── firefox.exe           # Firefox binary
│   ├── TorBrowser/
│   │   ├── Tor/
│   │   │   ├── tor.exe       # Tor binary
│   │   │   └── *.dll         # Tor libraries
│   │   └── Data/
│   │       ├── Browser/
│   │       │   └── profile.default/
│   │       └── Tor/
│   └── fonts/
└── Start Tor Browser.lnk
```

### Custom Profile Permissions

When using `use_custom_profile=True`, Firefox writes lock files and cache data to the profile directory. If Tor Browser is installed under a protected location (for example `C:\Program Files\`), you may hit permission errors. Copy Tor Browser to a user-writable location (for example `C:\Users\YourName\Desktop\Tor Browser`) before using persistent profiles.

### Environment Variables

The driver automatically configures:
- `PATH`: Adds Tor and Browser directories for DLL loading
- `HOME`: Set to the Tor Browser directory

### Installing Dependencies with Chocolatey

```bash
# Install geckodriver
choco install geckodriver

# Install Tor (for USE_RUNNING_TOR mode)
choco install tor

# Verify Tor is running
netstat -an | findstr 9050
```

## Running Tests

```bash
# Set the TBB path (Command Prompt)
set TBB_PATH=C:\Users\YourName\Desktop\Tor Browser

# Run tests
pytest tbselenium_windows/test/ -v

# Run with coverage
pytest tbselenium_windows/test/ -v --cov=tbselenium_windows
```

You can also use the test runner helper:
```bash
python run_tests.py "C:\Users\YourName\Desktop\Tor Browser"
```

## API Reference

### Main Classes

- `TorBrowserDriver` - Main driver class extending Selenium's Firefox WebDriver

### Utility Functions

- `launch_tbb_tor_with_stem(tbb_path, torrc, tor_binary)` - Launch Tor using Stem
- `set_security_level(driver, level)` - Set browser security level
- `disable_js(driver)` - Disable JavaScript
- `enable_js(driver)` - Enable JavaScript

### Constants

- `USE_RUNNING_TOR` - Use system Tor
- `USE_STEM` - Use Stem-launched Tor
- `TB_SECURITY_LEVEL_STANDARD` - Standard security
- `TB_SECURITY_LEVEL_SAFER` - Safer security
- `TB_SECURITY_LEVEL_SAFEST` - Safest security (JS disabled)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Original [tor-browser-selenium](https://github.com/webfp/tor-browser-selenium) project
- [Tor Project](https://www.torproject.org/) for Tor Browser
- [Selenium](https://www.selenium.dev/) project