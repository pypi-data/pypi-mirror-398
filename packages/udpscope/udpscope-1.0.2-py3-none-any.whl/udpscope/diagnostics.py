"""
Network diagnostics module
"""
import subprocess

class NetworkDiagnostics:
    """Network diagnostics and troubleshooting utilities"""
    def __init__(self, port):
        self.port = port
        self.diagnostics = {}

    def run_diagnostics(self):
        """Run comprehensive network diagnostics"""
        print("\n🔍 RUNNING NETWORK DIAGNOSTICS...")

        self.diagnostics = {
            'port_status': self._check_port_status(),
            'docker_status': self._check_docker_status(),
            'network_interfaces': self._check_network_interfaces(),
            'system_info': self._collect_system_info()
        }

        self._print_diagnostics()
        return self.diagnostics

    def _check_port_status(self):
        """Check if port is open and listening"""
        try:
            cmd = ['ss', '-tunlp', 'sport', f':{self.port}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                'is_listening': len(result.stdout.strip()) > 0,
                'output': result.stdout
            }
        except Exception as e:
            return {'error': str(e), 'is_listening': False}

    def _check_docker_status(self):
        """Check Docker containers and status"""
        try:
            # Check if Docker is running
            subprocess.run(['docker', 'version'], capture_output=True, check=True)
            
            # Get container info
            cmd = ['docker', 'ps', '--format', 'table {{.Names}}\t{{.Ports}}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Find containers using our port
            containers = []
            for line in result.stdout.split('\n'):
                if f':{self.port}' in line:
                    containers.append(line.strip())
            
            return {
                'is_running': True,
                'output': result.stdout,
                'containers_on_port': containers
            }
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            return {'error': str(e), 'is_running': False}

    def _check_network_interfaces(self):
        """Check network interfaces and configuration"""
        try:
            cmd = ['ip', 'addr', 'show']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {'output': result.stdout}
        except Exception as e:
            return {'error': str(e)}

    def _collect_system_info(self):
        """Collect basic system information"""
        try:
            # Get kernel version
            with open('/proc/version', 'r') as f:
                kernel_version = f.read().strip()
            
            # Get OS release
            try:
                with open('/etc/os-release', 'r') as f:
                    os_release = f.read()
            except:
                os_release = "Unknown"
            
            return {
                'kernel': kernel_version,
                'os_release': os_release
            }
        except Exception as e:
            return {'error': str(e)}

    def _print_diagnostics(self):
        """Print diagnostic information"""
        print("\n" + "="*80)
        print("🩺 NETWORK DIAGNOSTICS REPORT")
        print("="*80)

        diag = self.diagnostics

        print(f"\n📡 PORT {self.port} STATUS:")
        port_status = diag.get('port_status', {})
        if port_status.get('is_listening'):
            print("   ✅ Port is listening")
            if port_status.get('output'):
                print(f"   Active connections:\n{port_status['output']}")
        else:
            print("   ❌ Port is NOT listening")
            if port_status.get('error'):
                print(f"   Error: {port_status['error']}")

        print(f"\n🐳 DOCKER STATUS:")
        docker_status = diag.get('docker_status', {})
        if docker_status.get('is_running'):
            print("   ✅ Docker is running")
            containers = docker_status.get('containers_on_port', [])
            if containers:
                print(f"   Containers using port {self.port}:")
                for container in containers:
                    print(f"     - {container}")
            else:
                print(f"   No containers found using port {self.port}")
            print(f"   All containers:\n{docker_status.get('output', 'None')}")
        else:
            print("   ❌ Docker is not running or not installed")
            if docker_status.get('error'):
                print(f"   Error: {docker_status['error']}")

        print(f"\n🔧 RECOMMENDATIONS:")
        print("   1. Check if your application/service is running")
        print("   2. Verify the correct port is being used")
        print("   3. Check if traffic is reaching your server")
        print("   4. Verify firewall rules are not blocking traffic")
        print("   5. Try running from inside the container:")
        print(f"      docker exec <container> tcpdump -i any -n 'udp port {self.port}'")

        # Print system info
        sys_info = diag.get('system_info', {})
        if 'kernel' in sys_info:
            print(f"\n💻 SYSTEM INFO:")
            print(f"   Kernel: {sys_info.get('kernel', 'Unknown')}")