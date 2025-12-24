# tbselenium-macos

Tor Browser automation with Selenium for macOS.

This is a complete port of [tor-browser-selenium](https://github.com/webfp/tor-browser-selenium) specifically designed for macOS. It handles the macOS `.app` bundle structure and provides a clean interface for automating Tor Browser.

## Features

- **macOS Native**: Designed specifically for macOS Tor Browser `.app` bundles
- **Selenium 4+ Support**: Full compatibility with modern Selenium
- **System Tor Integration**: Works with Homebrew-installed Tor
- **Stem Support**: Launch Tor from the browser bundle using Stem
- **Headless Mode**: Run Tor Browser without a visible window
- **Custom Profiles**: Support for persistent and temporary profiles
- **Security Controls**: Set Tor Browser security levels programmatically

## Requirements

- **macOS** (tested on macOS 12+)
- **Python 3.8+**
- **Tor Browser for macOS** ([download](https://www.torproject.org/download/))
- **geckodriver** (install with `brew install geckodriver`)
- **Tor** (for system Tor mode: `brew install tor && brew services start tor`)

## Installation
Download from PyPI:
```bash
pip install tbselenium-macos
```

Install manually:
```bash
git clone https://github.com/user/tbselenium-macos.git
cd tbselenium-macos
pip install -e .
```

## Quick Start

### Basic Usage

```python
from tbselenium_macos import TorBrowserDriver

# Using Tor Browser.app with system Tor
with TorBrowserDriver("/Applications/Tor Browser.app") as driver:
    driver.load_url("https://check.torproject.org")
    print(driver.title)
    print(driver.find_element_by("h1.on").text)
```

### With Stem (Launch Tor from Bundle)

```python
from tbselenium_macos import TorBrowserDriver, launch_tbb_tor_with_stem, USE_STEM

TBB_PATH = "/Applications/Tor Browser.app"

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
from tbselenium_macos import TorBrowserDriver

with TorBrowserDriver("/Applications/Tor Browser.app", headless=True) as driver:
    driver.load_url("https://check.torproject.org")
    driver.save_screenshot("screenshot.png")
```

### Custom Preferences

```python
from tbselenium_macos import TorBrowserDriver

# Disable images
pref_dict = {"permissions.default.image": 2}

with TorBrowserDriver("/Applications/Tor Browser.app", pref_dict=pref_dict) as driver:
    driver.load_url("https://example.com")
```

### Security Level

```python
from tbselenium_macos import TorBrowserDriver, set_security_level
from tbselenium_macos import TB_SECURITY_LEVEL_SAFEST

with TorBrowserDriver("/Applications/Tor Browser.app") as driver:
    set_security_level(driver, TB_SECURITY_LEVEL_SAFEST)
    driver.load_url("https://example.com")
```

## Configuration Options

### TorBrowserDriver Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tbb_path` | str | "" | Path to Tor Browser.app |
| `tor_cfg` | int | USE_RUNNING_TOR | Tor configuration mode |
| `tbb_fx_binary_path` | str | "" | Direct path to Firefox binary |
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

## macOS-Specific Notes

### .app Bundle Structure

Tor Browser on macOS uses an `.app` bundle structure:

```
Tor Browser.app/
├── Contents/
│   ├── MacOS/
│   │   └── firefox           # Firefox binary
│   ├── Resources/
│   │   ├── TorBrowser/
│   │   │   ├── Tor/
│   │   │   │   └── tor       # Tor binary
│   │   │   └── Data/
│   │   │       ├── Browser/
│   │   │       │   └── profile.default/
│   │   │       └── Tor/
│   │   └── browser/
│   └── Info.plist
```

### Custom Profile Permissions

When using `use_custom_profile=True`, Firefox writes lock files and cache data to the profile directory inside the `.app` bundle. This can cause permission errors if Tor Browser is installed in `/Applications/`, which is typically read-only for standard users.

**Before using stateful/custom profile mode:**

1. Copy `Tor Browser.app` to a user-writable location:
   ```bash
   cp -R "/Applications/Tor Browser.app" ~/Applications/
   # or
   cp -R "/Applications/Tor Browser.app" ~/Downloads/
   ```

2. Use the copied path in your code:
   ```python
   from tbselenium_macos import TorBrowserDriver

   # Use the user-writable copy
   with TorBrowserDriver("~/Applications/Tor Browser.app", use_custom_profile=True) as driver:
       driver.load_url("https://check.torproject.org")
   ```

### Environment Variables

Unlike Linux, this port uses:
- `DYLD_LIBRARY_PATH` instead of `LD_LIBRARY_PATH`
- No `FONTCONFIG_PATH` (not needed on macOS)

### Installing Dependencies with Homebrew

```bash
# Install geckodriver
brew install geckodriver

# Install and start system Tor (for USE_RUNNING_TOR mode)
brew install tor
brew services start tor

# Verify Tor is running
nc -z 127.0.0.1 9050 && echo "Tor is running"
```

## Running Tests

```bash
# Set the TBB path
export TBB_PATH="/Applications/Tor Browser.app"

# Make sure Tor is running
brew services start tor

# Run tests
pytest tbselenium_macos/test/ -v

# Run with coverage
pytest tbselenium_macos/test/ -v --cov=tbselenium_macos
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

### Exceptions

- `TBDriverPathError` - Invalid path configuration
- `TBDriverPortError` - Port not available
- `TBDriverConfigError` - Invalid configuration
- `StemLaunchError` - Failed to launch Tor with Stem

## Troubleshooting

### "SOCKS port is not listening"

Make sure Tor is running:
```bash
brew services start tor
nc -z 127.0.0.1 9050 && echo "Tor is running"
```

### "Invalid Firefox binary"

Verify the Tor Browser path:
```bash
ls -la "/Applications/Tor Browser.app/Contents/MacOS/firefox"
```

### geckodriver not found

Install with Homebrew:
```bash
brew install geckodriver
```

### Browser crashes on start

Try updating Tor Browser and geckodriver to latest versions.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Original [tor-browser-selenium](https://github.com/webfp/tor-browser-selenium) project
- [Tor Project](https://www.torproject.org/) for Tor Browser
- [Selenium](https://www.selenium.dev/) project
