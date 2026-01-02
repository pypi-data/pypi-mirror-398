"""
Command-line interface for drop_email
"""

import sys
import argparse
import pandas as pd
from .email_sender import send
from .config import init_config, get_config_path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="drop_email - Send data as beautiful HTML emails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize configuration file
  drop_email init
  
  # Send data using Python API
  python -c "import drop_email as de; import pandas as pd; df = pd.DataFrame({'A': [1,2,3]}); de.send(df)"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize configuration file")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration file"
    )
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration file path")
    
    args = parser.parse_args()
    
    if args.command == "init":
        config_path = init_config(force=args.force)
        print(f"\nConfiguration file location: {config_path}")
        print("\nEdit this file to configure your email settings.")
    
    elif args.command == "config":
        config_path = get_config_path()
        print(f"Configuration file path: {config_path}")
        if config_path.exists():
            print("✓ Configuration file exists")
        else:
            print("✗ Configuration file does not exist")
            print("Run 'drop_email init' to create it")
    
    else:
        # Default: show help if no command provided
        parser.print_help()
        print("\nTip: Use 'drop_email init' to create the configuration file.")


if __name__ == "__main__":
    main()

