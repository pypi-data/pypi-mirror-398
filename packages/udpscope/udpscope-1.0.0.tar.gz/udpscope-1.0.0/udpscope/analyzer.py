"""
Main analysis engine for UDP traffic
"""
import time
from collections import Counter, defaultdict
import statistics
from datetime import datetime

from udpscope.utils import safe_mean, safe_median, safe_stdev

class UDPAnalyzer:

    """Main analyzer class for UDP traffic analysis"""
    def __init__(self, port, duration=60, interface="any"):
        self.port = port
        self.duration = duration
        self.interface = interface
        self.packets = []
        self.analysis = {}
        self.diagnostics = {}

    def analyze_traffic(self, packets):
        """Comprehensive traffic analysis"""
        self.packets = packets
        
        if not self.packets:
            print("No packets to analyze generating diagnostic info")
            self._generate_diagnostic_info()
            return

        print(f"Analyzing {len(self.packets)} packets...")

        self.analysis = {
            'basic_stats': self._calculate_basic_stats(),
            'ip_analysis': self._analyze_ips(),
            'packet_length_analysis': self._analyze_packet_lengths(),
            'temporal_analysis': self._analyze_temporal_patterns(),
            'threat_assessment': self._assess_threats()
        }
        
        return self.analysis

    def _calculate_basic_stats(self):
        """Calculate basic statistics"""
        packets = self.packets
        lengths = [p['length'] for p in packets]

        return {
            'total_packets': len(packets),
            'total_bytes': sum(lengths),
            'duration': self.duration,
            'packets_per_second': len(packets) / self.duration if self.duration > 0 else 0,
            'bytes_per_second': sum(lengths) / self.duration if self.duration > 0 else 0,
            'unique_ips': len(set(p['src_ip'] for p in packets)),
            'unique_ports': len(set(p['src_port'] for p in packets)),
            'avg_packet_size': safe_mean(lengths),
            'min_packet_size': min(lengths) if lengths else 0,
            'max_packet_size': max(lengths) if lengths else 0
        }

    def _analyze_ips(self):
        """Analyze IP traffic patterns"""
        ip_data = {}

        for packet in self.packets:
            ip = packet['src_ip']
            if ip not in ip_data:
                ip_data[ip] = {
                    'packets': [],
                    'lengths': [],
                    'ports': set()
                }

            ip_data[ip]['packets'].append(packet)
            ip_data[ip]['lengths'].append(packet['length'])
            ip_data[ip]['ports'].add(packet['src_port'])

        # Calculate metrics per IP
        analysis = {}
        for ip, data in ip_data.items():
            lengths = data['lengths']
            analysis[ip] = {
                'total_packets': len(data['packets']),
                'total_bytes': sum(lengths),
                'packets_per_second': len(data['packets']) / self.duration if self.duration > 0 else 0,
                'bytes_per_second': sum(lengths) / self.duration if self.duration > 0 else 0,
                'unique_ports': len(data['ports']),
                'min_packet_length': min(lengths) if lengths else 0,
                'max_packet_length': max(lengths) if lengths else 0,
                'avg_packet_length': safe_mean(lengths),
                'port_diversity': len(data['ports']) / len(data['packets']) if data['packets'] else 0
            }

        return analysis

    def _analyze_packet_lengths(self):
        """Analyze packet length distribution"""
        lengths = [p['length'] for p in self.packets]

        if not lengths:
            return {}

        # Create length distribution
        bins = [0, 64, 128, 256, 512, 1024, 1500, 10000]
        distribution = {}
        for i in range(len(bins)-1):
            bin_name = f"{bins[i]}-{bins[i+1]}"
            count = len([l for l in lengths if bins[i] <= l < bins[i+1]])
            if count > 0:
                distribution[bin_name] = count

        return {
            'min_length': min(lengths),
            'max_length': max(lengths),
            'mean_length': safe_mean(lengths),
            'median_length': safe_median(lengths),
            'std_length': safe_stdev(lengths),
            'length_distribution': distribution,
            'most_common_lengths': dict(Counter(lengths).most_common(10))
        }

    def _analyze_temporal_patterns(self):
        """Analyze temporal patterns"""
        if len(self.packets) < 2:
            return {}

        # Group by second
        seconds_data = defaultdict(list)
        for packet in self.packets:
            time_key = packet['timestamp'][:19]  # Second precision
            seconds_data[time_key].append(packet)

        packets_per_second = [len(packets) for packets in seconds_data.values()]

        return {
            'peak_pps': max(packets_per_second) if packets_per_second else 0,
            'avg_pps': safe_mean(packets_per_second),
            'burst_count': len([pps for pps in packets_per_second if pps > 10])
        }

    def _assess_threats(self):
        """Assess potential threats"""
        if not self.packets:
            return {}

        ip_analysis = self._analyze_ips()
        threats = []

        for ip, data in ip_analysis.items():
            threat_score = 0

            if data['packets_per_second'] > 50:
                threat_score += 3
            elif data['packets_per_second'] > 20:
                threat_score += 2
            elif data['packets_per_second'] > 10:
                threat_score += 1

            if data['port_diversity'] > 0.8:
                threat_score += 2

            if data['total_packets'] > 1000:
                threat_score += 2

            if threat_score >= 3:
                threats.append({
                    'ip': ip,
                    'threat_score': threat_score,
                    'reason': f"High PPS: {data['packets_per_second']:.1f}, Ports: {data['unique_ports']}"
                })

        return {
            'high_threat_ips': sorted(threats, key=lambda x: x['threat_score'], reverse=True),
            'total_threats': len(threats)
        }

    def _generate_diagnostic_info(self):
        """Generate diagnostic information when no packets are captured"""
        # This is a stub actual implementation is in diagnostics.py
        self.diagnostics = {'no_packets': True}