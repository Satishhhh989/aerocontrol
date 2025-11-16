"""
CLI interface for AeroControl.
"""

import logging
import sys
import yaml
from pathlib import Path
import argparse  # Make sure this import is here

def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('aerocontrol.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logging.warning(f"Config file not found: {config_path}, using defaults")
        return get_default_config()
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return get_default_config()


def get_default_config() -> dict:
    """Get default configuration."""
    return {
        'camera': {
            'width': 640,
            'height': 480,
            'fps': 30
        },
        'smoother': {
            'alpha_base': 0.3,
            'alpha_min': 0.1,
            'alpha_max': 0.7,
            'adaptation_factor': 0.5,
            'reference_hand_size': 150.0
        },
        'velocity': {
            'gamma': 0.6,
            'gain': 0.0025,
            'min_velocity': 10
        },
        'gestures': {
            'pinch_threshold': 40,
            'pinch_debounce_ms': 200,
            'swipe_min_distance': 100,
            'swipe_min_velocity': 200,
            'swipe_debounce_ms': 500,
            'zoom_threshold': 200
        }
    }


def main(args):
    """Main CLI entry point."""
    from .main import AeroControl
    
    # Load configuration
    config = load_config(args.config)
    
    # Create controller
    controller = AeroControl(
        camera_id=args.camera,
        config=config,
        debug=args.debug
    )
    
    # Run calibration if requested
    if args.calibrate:
        logging.info("Running calibration wizard...")
        if not controller.run_calibration():
            logging.error("Calibration failed")
            return
    
    # Start main loop
    try:
        controller.run()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        controller.stop()

# This is the part that runs when you execute the file
if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="AeroControl: Hand Gesture Mouse")
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera device index'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug UI overlay'
    )
    parser.add_argument(
        '--calibrate',
        action='store_true',
        help='Run the calibration wizard'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    
    # Run main application
    main(args)