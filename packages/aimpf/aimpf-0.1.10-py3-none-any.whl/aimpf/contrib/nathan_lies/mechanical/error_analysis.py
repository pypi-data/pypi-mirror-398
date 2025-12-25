import logging
import os
import sys
import json
from .tensile import process_folder, generate_plots

_logger = logging.getLogger(__name__)


def setup_logging(loglevel):
    """
    Configure logging for the CLI.

    Sets up logging with a specified log level. This function ensures that all log messages
    are formatted with timestamps, log levels, and message content.

    Args:
        loglevel (int): Logging verbosity level. Can be:
            - `logging.INFO` for informational messages.
            - `logging.DEBUG` for detailed debugging messages.
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel or logging.INFO, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """
    Main function for performing error analysis on stress-strain data.

    This function orchestrates the error analysis process by:
        1. Setting up logging based on the verbosity level.
        2. Creating a results directory for output files.
        3. Reading a configuration file to extract analysis parameters.
        4. Processing experiment folders to analyze data and generate individual results.
        5. Creating summary plots and saving the aggregated results.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing:
            - root_folder_path (str): Path to the root folder containing experiment data and subfolders.
            - config_file (str): Path to the configuration JSON file.
            - loglevel (int): Logging verbosity level (INFO or DEBUG).

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        JSONDecodeError: If the configuration file is not in valid JSON format.
        Exception: For any issues during processing or plot generation.
    """

    # Set up logging
    setup_logging(args.loglevel)

    # Create the results directory outside the root_folder_path
    results_dir = os.path.join(os.getcwd(), 'results')
    os.makedirs(results_dir, exist_ok=True)
    _logger.info(f"Results directory created at: {results_dir}")

    # Read the configuration file
    try:
        with open(args.config_file, 'r') as file:
            config_data = json.load(file)
        _logger.info(f"Configuration file loaded successfully from: {args.config_file}")
    except FileNotFoundError:
        _logger.error(f"Configuration file not found: {args.config_file}")
        raise
    except json.JSONDecodeError as e:
        _logger.error(f"Error parsing configuration file: {e}")
        raise

    # Process the folders and generate plots
    try:
        results = process_folder(args.root_folder_path, config_data, results_dir, _logger)
        _logger.info(f"Data processing completed for folder: {args.root_folder_path}")
    except Exception as e:
        _logger.error(f"Error during data processing: {e}")
        raise

    # Generate overall plots and summaries
    try:
        generate_plots(results, results_dir, _logger)
        _logger.info("Summary plots and results generated successfully.")
    except Exception as e:
        _logger.error(f"Error during plot generation: {e}")
        raise

