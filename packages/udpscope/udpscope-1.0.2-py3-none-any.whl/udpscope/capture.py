"""
Traffic capture module with multiple capture methods
"""
import subprocess
import time
import threading
from datetime import datetime

class TrafficCapture:
    """Handle UDP traffic capture using multiple methods"""
    def __init__(self, port, duration=60, interface="any"):
        self.port = port
        self.duration = duration
        self.interface = interface
        self.raw_output = ""
        self.connections_data = []

    def capture_traffic_multiple_methods(self):
        """Try multiple methods to capture UDP traffic"""
        print(f"Targeting UDP port {self.port} for {self.duration} seconds")

        methods = [
            self._capture_with_tcpdump,
            self._capture_with_tshark,
            self._capture_from_container,
            self._capture_with_ss
        ]

        for method in methods:
            print(f"🔄 Trying {method.__name__}...")
            if method():
                print(f"✅ Success with {method.__name__}")
                return True
            else:
                print(f"❌ Failed with {method.__name__}")

        print("💥 All capture methods failed")
        return False

    def _capture_with_tcpdump(self):
        """Method 1: Standard tcpdump"""
        try:
            cmd = [
                'timeout', str(self.duration),
                'tcpdump', '-i', self.interface,
                '-n',
                f'udp and port {self.port}',
                '-t',
                '-q'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.duration + 5)
            self.raw_output = result.stdout
            return len(self.raw_output.strip()) > 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _capture_with_tshark(self):
        """Method 2: tshark (more reliable)"""
        try:
            cmd = [
                'timeout', str(self.duration),
                'tshark', '-i', self.interface,
                '-f', f'udp port {self.port}',
                '-Y', f'udp.port == {self.port}',
                '-T', 'fields',
                '-e', 'frame.time',
                '-e', 'ip.src',
                '-e', 'udp.srcport',
                '-e', 'ip.dst',
                '-e', 'udp.dstport',
                '-e', 'frame.len'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.duration + 5)
            self.raw_output = result.stdout
            return len(self.raw_output.strip()) > 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _capture_from_container(self):
        """Method 3: Capture from inside the game container"""
        try:
            # First, find the container using our port
            container_id = self._find_container_by_port()
            if not container_id:
                return False

            print(f"🐳 Found container: {container_id[:12]}")

            # Execute tcpdump inside the container
            cmd = [
                'timeout', str(self.duration),
                'docker', 'exec', container_id,
                'tcpdump', '-i', 'any', '-n', '-q',
                f'udp and port {self.port}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.duration + 5)
            self.raw_output = result.stdout
            return len(self.raw_output.strip()) > 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _capture_with_ss(self):
        """Method 4: Use ss to see active connections"""
        try:
            # Monitor connections in real-time
            import threading

            self.connections_data = []
            stop_monitor = threading.Event()

            def monitor_connections():
                while not stop_monitor.is_set():
                    try:
                        cmd = ['ss', '-unp', 'sport', f':{self.port}']
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.stdout:
                            self.connections_data.append({
                                'time': datetime.now().isoformat(),
                                'data': result.stdout
                            })
                        time.sleep(1)
                    except:
                        pass

            monitor_thread = threading.Thread(target=monitor_connections)
            monitor_thread.start()
            time.sleep(self.duration)
            stop_monitor.set()
            monitor_thread.join()

            # Process the collected data
            self.raw_output = "\n".join([f"{item['time']} {item['data']}" for item in self.connections_data])
            return len(self.connections_data) > 0
        except:
            return False

    def _find_container_by_port(self):
        """Find Docker container using the specified port"""
        try:
            cmd = ['docker', 'ps', '--format', '{{.ID}} {{.Ports}}']
            result = subprocess.run(cmd, capture_output=True, text=True)

            for line in result.stdout.split('\n'):
                if f':{self.port}' in line:
                    return line.split()[0]
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def get_raw_output(self):
        """Get the raw captured output"""
        return self.raw_output