# ACMS (Apple Container MCP Server)

[![Downloads](https://pepy.tech/badge/acms/month)](https://pepy.tech/project/acms)
[![PyPI Version](https://img.shields.io/pypi/v/acms.svg)](https://pypi.org/project/acms/)
[![Python version](https://img.shields.io/pypi/pyversions/acms.svg)](https://pypi.org/project/acms/)

**ACMS** is a Model Context Protocol (MCP) server that provides programmatic access to Apple's container CLI tool on macOS. ACMS can be run locally or accessed remotely via HTTP/S.

The point of ACMS is to bring attention to the [Containerization](https://github.com/apple/containerization) package and [Container cli](https://github.com/apple/container) efforts. Inspiration for ACMS came from [coderunner](https://github.com/instavm/coderunner).

## Prerequisites

- **Mac with Apple Silicon**
- **macOS 26+** - It can run on Sequoia with [limitations](https://github.com/apple/container/blob/main/docs/technical-overview.md#macos-15-limitations).
- **Xcode 26** - required to compile containerization
- **Apple Containerization Framework** - (required for container functionality)
- **Apple Container Cli** - installed and in PATH

## Quick Start

### Install

Either clone the repository or `pip install acms` in a venv.

### Start Apple Container Services
```bash

container system start

```

### Start ACMS Server
```bash
# Recommended: Use the startup script
./start-acms.sh

# Or start directly with custom options
python3 acms/acms.py --port 8765 --host 127.0.0.1 > acms.log 2>&1 &
```

### Configure MCP Client
Add to your MCP client configuration:

```
claude mcp add --transport http acms http://localhost:8765/mcp
```

## Usage Examples

"acms create an ubuntu x64 container ..."

## Testing

ACMS includes comprehensive end-to-end testing, just tell Claude to run the "ACMS CLAUDE TEST GUIDE".

## Security Considerations

This is not secure, especially if you run it on a remote Mac OS endpoint on your home net. Also, you can lose your data when Claude tries to be helpful.

![footgun](./images/footgun.png)

mcp-name: io.github.gattjoe/ACMS
