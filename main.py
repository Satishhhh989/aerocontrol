#!/usr/bin/env python3
"""
AeroControl - Hand Gesture Mouse Control for Linux
Main entry point for the application.
"""

import sys
import argparse
import logging
from pathlib import Path

from aerocontrol.cli import setup_logging, main as cli_main


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AeroControl - Hand Gesture Mouse Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aerocontrol --debug          Run with debug overlay
  aerocontrol --headless       Run without UI (logs only)
  aerocontrol --calibrate      Run calibration wizard
  aerocontrol --config custom.yaml  Use custom config
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug overlay window'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run without UI (logs only)'
    )
    
    parser.add_argument(
        '--calibrate',
        action='store_true',
        help='Run calibration wizard'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera device index (default: 0)'
    )
    
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    try:
        cli_main(args)
    except KeyboardInterrupt:
        print("\nShutting down AeroControl...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)