"""
Command-line interface for UDPScope
"""
import argparse
import sys

from udpscope.capture import TrafficCapture
from udpscope.parser import PacketParser
from udpscope.analyzer import UDPAnalyzer
from udpscope.diagnostics import NetworkDiagnostics
from udpscope.report import AnalysisReport
from udpscope.utils import check_tool_availability, validate_port, print_warning

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='UDPScope Professional UDP traffic analysis and diagnostics tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
            """
                Examples:
                sudo udpscope --port 2456 --duration 60 --interface any
                sudo udpscope --port 53 --duration 30 --interface eth0
                sudo udpscope --port 51820 --duration 10
              
            """
    )
    parser.add_argument('--port', type=int, required=True, help='UDP port to monitor')
    parser.add_argument('--duration', type=int, default=30,
    help='Capture duration in seconds (default: 30)')
    parser.add_argument('--interface', default='any',
    help='Network interface to monitor (default: any)')
    parser.add_argument('--json', action='store_true',
    help='Output report in JSON format')

    args = parser.parse_args()

    # Validate port
    try:
        validate_port(args.port)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("🚀 UDPScope - UDP Traffic Analyzer")
    print(f"🎯 Target Port: {args.port}/udp")
    print(f"⏱️  Duration: {args.duration} seconds")
    print(f"🔌 Interface: {args.interface}")
    print("-" * 60)

    # Check if we have required tools
    tools = ['tcpdump', 'docker', 'ss', 'tshark']
    available, missing = check_tool_availability(tools)

    if missing:
        print_warning(f"Missing tools: {', '.join(missing)} - some features may not work")
    print(f"✅ Available tools: {', '.join(available)}")

    # Create components
    capture = TrafficCapture(args.port, args.duration, args.interface)

    # Capture traffic
    if capture.capture_traffic_multiple_methods():
        # Parse packets
        packets = PacketParser.parse_raw_output(capture.get_raw_output(), args.port)
        
        if packets:
            # Analyze traffic
            analyzer = UDPAnalyzer(args.port, args.duration, args.interface)
            analysis = analyzer.analyze_traffic(packets)
            
            # Generate report
            if args.json:
                json_report = AnalysisReport.generate_json_report(analysis)
                print(json_report)
            else:
                AnalysisReport.print_console_report(analysis, packets, args.duration, args.port)
                AnalysisReport.print_summary(analysis)
        else:
            print("💡 No packets captured, but capture method was successful")
            print("   This might mean there's no traffic on this port")
            # Run diagnostics
            diagnostics = NetworkDiagnostics(args.port)
            diagnostics.run_diagnostics()
    else:
        print("💥 All capture methods failed")
        # Run diagnostics even if capture failed
        diagnostics = NetworkDiagnostics(args.port)
        diagnostics.run_diagnostics()
        sys.exit(1)
    
if __name__ == "__main__":
    main()