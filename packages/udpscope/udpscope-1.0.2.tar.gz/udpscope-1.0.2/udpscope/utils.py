"""
Utility functions and helpers
"""
from email import message
import subprocess
import statistics
import sys

def validate_port(port):
    """Validate port number"""
    if not isinstance(port, int):
        raise ValueError("Port must be an integer")
    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535")
    return True

def check_tool_availability(tools):
    """Check if required tools are available"""
    available = []
    missing = []

    for tool in tools:
        try:
            subprocess.run(['which', tool], check=True, capture_output=True)
            available.append(tool)
        except subprocess.CalledProcessError:
            missing.append(tool)

    return available, missing

def safe_mean(data):
    """Safe mean calculation that handles empty lists"""
    if not data:
        return 0
    try:
        return statistics.mean(data)
    except statistics.StatisticsError:
        return 0

def safe_median(data):
    """Safe median calculation that handles empty lists"""
    if not data:
        return 0
    try:
        return statistics.median(data)
    except statistics.StatisticsError:
        return 0
    
def safe_stdev(data):
    """Safe standard deviation calculation"""
    if len(data) < 2:
        return 0
    try:
        return statistics.stdev(data)
    except statistics.StatisticsError:
        return 0
    
def format_bytes(bytes_count):
    """Format bytes count to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        
    bytes_count /= 1024.0  
    return f"{bytes_count:.2f} TB"

def print_warning(message):
    """Print warning message with consistent formatting"""
    print(f"⚠️ {message}", file=sys.stderr)

def print_error(message):
    """Print error message with consistent formatting"""
    print(f"❌ {message}", file=sys.stderr)

def print_success(message):
    """Print success message with consistent formatting"""
    print(f"✅ {message}")