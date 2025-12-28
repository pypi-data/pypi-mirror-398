"""
Packet parsing utilities
"""
import re

class PacketParser:
    """Parse packet data from various capture formats"""
    @staticmethod
    def parse_raw_output(raw_output, target_port):
        """Parse raw capture output into structured packet data"""
        packets = []

        if not raw_output:
            print("❌ No raw output to parse")
            return packets

        print(f"📖 Parsing {len(raw_output.splitlines())} lines of output...")

        for line in raw_output.split('\n'):
            if not line.strip():
                continue

            packet = PacketParser._parse_line(line, target_port)
            if packet:
                packets.append(packet)

        print(f"📊 Parsed {len(packets)} packets")
        return packets

    @staticmethod
    def _parse_line(line, target_port):
        """Parse different tcpdump/tshark output formats"""
        # tcpdump format
        patterns = [
            # tcpdump standard
            r'(\S+)\s+IP\s+([\d\.]+)\.(\d+)\s+>\s+([\d\.]+)\.(\d+):\s+UDP.*?length\s+(\d+)',
            # tcpdump quiet
            r'(\S+)\s+IP\s+([\d\.]+)\.(\d+)\s+>\s+([\d\.]+)\.(\d+).*?length\s+(\d+)',
            # tshark format
            r'(\S+)\s+([\d\.]+)\s+(\d+)\s+([\d\.]+)\s+(\d+)\s+(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                timestamp = groups[0]
                src_ip = groups[1]
                src_port = int(groups[2])
                dst_ip = groups[3]
                dst_port = int(groups[4])
                length = int(groups[5])

                # Only process if destination port matches
                if dst_port == target_port:
                    return {
                        'timestamp': timestamp,
                        'src_ip': src_ip,
                        'src_port': src_port,
                        'dst_ip': dst_ip,
                        'dst_port': dst_port,
                        'length': length,
                        'raw_line': line
                    }

        return None

    @staticmethod
    def validate_packet(packet):
        """Validate packet structure"""
        required_fields = ['timestamp', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'length']
        for field in required_fields:
            if field not in packet:
                return False
        return True