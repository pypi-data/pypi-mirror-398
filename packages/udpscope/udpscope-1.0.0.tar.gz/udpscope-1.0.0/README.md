
# UDPScope
- UDPScope is a professional network observability and diagnostics tool for UDP traffic analysis on Linux systems. It provides comprehensive monitoring, analysis, and reporting capabilities for system administrators to diagnose UDP based applications and services.

---

## Features
- Multi method capture: Uses tcpdump, tshark, Docker container introspection, and ss (socket statistics)
- Comprehensive analysis: Packet statistics, IP analysis, temporal patterns, and threat assessment
- Network diagnostics: Automatic diagnostics when no traffic is detected
- Multiple output formats: Clear console reporting with structured data
- Enterprise safe: Designed for legitimate system administration and troubleshooting

---

## Installation

### From PyPI
```bash
pip install udpscope
```

### From Debian / APT
```bash
sudo apt install udpscope
```

### From Snap
```bash
sudo snap install udpscope
```

### From Source
```bash
git clone https://github.com/yourorg/udpscope.git
cd udpscope
pip install -e .
```

---

## Usage

### Basic usage
```bash
sudo udpscope --port 2456 --duration 60 --interface any
```

### Monitor a specific interface
```bash
sudo udpscope --port 53 --duration 30 --interface eth0
```

### Short capture for quick diagnostics
```bash
sudo udpscope --port 51820 --duration 10
```

---

## Requirements

- Python 3.8+
- Linux kernel with packet capture capabilities
- One or more of:
  - tcpdump
  - tshark
  - docker
  - ss
- Root / sudo privileges (required for packet capture)

---

## License

MIT License  
See the `LICENSE` file for details.

