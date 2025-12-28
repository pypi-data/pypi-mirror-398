"""
Analysis reporting module
"""

class AnalysisReport:
    """Generate analysis reports from analyzer results"""
    @staticmethod
    def print_console_report(analysis, packets, duration, port):
        """Print analysis report to console"""
        if not analysis:
            print("❌ No analysis available")
            return

        print("\n" + "="*80)
        print("📊 UDP TRAFFIC ANALYSIS REPORT")
        print("="*80)

        stats = analysis.get('basic_stats', {})
        print(f"\n📈 BASIC STATISTICS:")
        print(f"   Target Port: {port}/udp")
        print(f"   Total Packets: {stats.get('total_packets', 0)}")
        print(f"   Total Bytes: {stats.get('total_bytes', 0):,}")
        print(f"   Duration: {duration}s")
        print(f"   Packets/Second: {stats.get('packets_per_second', 0):.1f}")
        print(f"   Bytes/Second: {stats.get('bytes_per_second', 0):,.0f}")
        print(f"   Unique IPs: {stats.get('unique_ips', 0)}")
        print(f"   Unique Ports: {stats.get('unique_ports', 0)}")

        if packets:
            length_stats = analysis.get('packet_length_analysis', {})
            if length_stats:
                print(f"\n📏 PACKET LENGTH ANALYSIS:")
                print(f"   Min Length: {length_stats.get('min_length', 0)} bytes")
                print(f"   Max Length: {length_stats.get('max_length', 0)} bytes")
                print(f"   Mean Length: {length_stats.get('mean_length', 0):.1f} bytes")
                print(f"   Median Length: {length_stats.get('median_length', 0)} bytes")

                distribution = length_stats.get('length_distribution', {})
                if distribution:
                    print(f"\n📊 LENGTH DISTRIBUTION:")
                    for bin_range, count in distribution.items():
                        if count > 0:
                            percentage = (count / stats.get('total_packets', 1)) * 100
                            print(f"   {bin_range:10} bytes: {count:6} packets ({percentage:5.1f}%)")

        ip_analysis = analysis.get('ip_analysis', {})
        if ip_analysis:
            print(f"\n🔝 TOP IPs BY TRAFFIC:")
            sorted_ips = sorted(ip_analysis.items(), key=lambda x: x[1].get('total_packets', 0), reverse=True)

            for ip, data in sorted_ips[:10]:
                print(f"   {ip:15} - {data.get('total_packets', 0):5} packets | "
                    f"PPS: {data.get('packets_per_second', 0):5.1f} | "
                    f"Min: {data.get('min_packet_length', 0):4} | "
                    f"Max: {data.get('max_packet_length', 0):4} | "
                    f"Mean: {data.get('avg_packet_length', 0):6.1f} | "
                    f"Ports: {data.get('unique_ports', 0):2}")

        threat_assessment = analysis.get('threat_assessment', {})
        if threat_assessment:
            high_threats = threat_assessment.get('high_threat_ips', [])
            if high_threats:
                print(f"\n⚠️  THREAT ASSESSMENT:")
                print(f"   Total High Threat IPs: {threat_assessment.get('total_threats', 0)}")
                for threat in high_threats[:5]:  # Show top 5 threats
                    print(f"   - {threat.get('ip', 'Unknown')}: "
                        f"Score {threat.get('threat_score', 0)} - {threat.get('reason', '')}")
            else:
                print(f"\n✅ THREAT ASSESSMENT: No high-threat IPs detected")

        temporal_analysis = analysis.get('temporal_analysis', {})
        if temporal_analysis:
            print(f"\n⏰ TEMPORAL ANALYSIS:")
            print(f"   Peak PPS: {temporal_analysis.get('peak_pps', 0):.1f}")
            print(f"   Average PPS: {temporal_analysis.get('avg_pps', 0):.1f}")
            print(f"   Burst Count (>10 PPS): {temporal_analysis.get('burst_count', 0)}")

    @staticmethod
    def generate_json_report(analysis):
        """Generate JSON report"""
        import json
        return json.dumps(analysis, indent=2, default=str)

    @staticmethod
    def print_summary(analysis):
        """Print a quick summary of the analysis"""
        if not analysis:
            print("No analysis data available")
            return

        stats = analysis.get('basic_stats', {})
        threats = analysis.get('threat_assessment', {}).get('total_threats', 0)
        
        print("\n📋 QUICK SUMMARY:")
        print(f"   Packets: {stats.get('total_packets', 0)}")
        print(f"   Bytes: {stats.get('total_bytes', 0):,}")
        print(f"   Unique IPs: {stats.get('unique_ips', 0)}")
        print(f"   Threat IPs: {threats}")
        print(f"   PPS: {stats.get('packets_per_second', 0):.1f}")