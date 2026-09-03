import argparse
import sys
import os

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.optimization.pipeline import OptimizationFunnel

def main():
    """Main execution entry point for Phase 1 optimization funnel CLI."""
    parser = argparse.ArgumentParser(description="Phase 1: Input Processing & Optimization Funnel")
    parser.add_argument("--log", type=str, help="Raw incident log string or path to log file", required=True)
    parser.add_argument("--history", type=str, help="Chat history string or path to history file", default="")
    parser.add_argument("--output", type=str, help="Output file path for the compressed payload", default="")

    args = parser.parse_args()

    # Read log input
    raw_log = args.log
    if args.log.endswith(".txt") or args.log.endswith(".json"):
        try:
            with open(args.log, 'r', encoding='utf-8') as f:
                raw_log = f.read()
        except Exception as e:
            print(f"Error reading log file: {e}")
            sys.exit(1)

    # Read history input
    chat_history = args.history
    if args.history.endswith(".txt"):
        try:
            with open(args.history, 'r', encoding='utf-8') as f:
                chat_history = f.read()
        except Exception as e:
            print(f"Error reading history file: {e}")
            sys.exit(1)

    print("Starting Optimization Funnel...")
    funnel = OptimizationFunnel()
    compressed_payload = funnel.process(raw_incident=raw_log, chat_history=chat_history)
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(compressed_payload)
            print(f"Compressed payload successfully written to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            sys.exit(1)
    else:
        print("\n=== FINAL COMPRESSED PAYLOAD ===")
        print(compressed_payload)
        print("================================")

if __name__ == "__main__":
    main()
