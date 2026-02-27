import os
import sys
from datetime import datetime
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from dotenv import load_dotenv
from App.src.cli.main_cli_menu import main_menu
from App.src.cli.cli_utils import _test_context

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="PEARL AI Application")
    parser.add_argument('--test', nargs='?', const='test_inputs.txt', help='Run in test mode, optionally specifying an input file.')
    args = parser.parse_args()
    print(f"[DEBUG] args.test: {args.test}", file=sys.__stderr__)

    test_mode = False
    test_file_path = None

    if args.test:
        test_mode = True
        test_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', args.test))
        print(f"[DEBUG] Entering test_mode block. test_file_path: {test_file_path}", file=sys.__stderr__)

        if os.path.exists(test_file_path):
            with open(test_file_path, 'r') as f:
                test_inputs = [line.strip() for line in f.readlines()]
            _test_context.activate_test_mode(test_inputs)
            print(f"[DEBUG] Test mode activated. Inputs loaded from {test_file_path}", file=sys.__stderr__)
            
            output_file_path = os.path.join(os.path.dirname(__file__), '..', '..', f'test_run_capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

            print(f"[DEBUG] Attempting to open file for writing: {output_file_path}", file=sys.__stderr__)
            
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                sys.stdout = output_file
                sys.stderr = output_file

                main_menu(test_mode=_test_context.test_mode)

            
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            _test_context.deactivate_test_mode()
            return # Exit after test run
        else:
            print(f"Error: Test mode enabled but test input file not found: {test_file_path}", file=sys.__stderr__)
            sys.exit(1)
    
    main_menu(test_mode=test_mode)

if __name__ == "__main__":
    main()
