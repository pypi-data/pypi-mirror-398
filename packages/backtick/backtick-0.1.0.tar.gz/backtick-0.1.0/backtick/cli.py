import sys
import argparse
from backtick.backtick import Backtick

if len(sys.argv) == 1:
    print("Hello from the Backtick programming language!")
    sys.exit(0)

bt = Backtick()

parser = argparse.ArgumentParser(description="Command line tool for the Backtick programming language by splot.dev")
parser.add_argument("command", choices=["run"],help="Command to run.")
parser.add_argument("filepath", type=str,help="Path to run.")
args = parser.parse_args()

if args.command == "run":
    try:
        with open(args.filepath, 'r') as file:
            content = file.read()
    except Exception as e:
        print(f"ERROR: Could not read file: {e}")
        sys.exit(1)

    try:  
        bt.run(bt.tokenize(str(content))[0])
    except Exception as e:
        print(f"ERROR: Could not run file: {e}")
        sys.exit(1)
else:
    print("ERROR: Invalid command.")
    sys.exit(1)