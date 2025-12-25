import logging
import os
import sys
import pandas as pd
from datetime import datetime
from .tensile import stressstrain2

_logger = logging.getLogger(__name__)


def main(args):
    """
    Main function to process stress-strain data for multiple samples.

    This function reads input data from a CSV file containing sample names and areas,
    processes the corresponding stress-strain data for each sample, and saves the results
    in the specified results folder. It also handles logging and error reporting during
    execution.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing:
            input_file (str): Path to the input CSV file with sample names and areas.
            input_folder (str): Path to the folder containing raw data files.
            results_folder (str): Path to save processed results (default: 'results').
            fcol (int): Column index for force data (1-based index).
            etcol (int): Column index for true strain data (1-based index).
            Aunit (str): Unit for area ('mm^2' or 'in^2').
            Funit (str): Unit for force ('kN' or 'N').
            Sunit (str): Unit for stress ('MPa' or 'N/mm^2').
            loglevel (int): Logging verbosity level (INFO or DEBUG).

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input data is invalid or incomplete.
        Exception: For unexpected errors during processing.

    Workflow:
        1. Set up logging based on the verbosity level.
        2. Create the results directory if it doesn't exist.
        3. Read the input CSV file for sample names and areas.
        4. Process stress-strain data for each sample.
        5. Log the completion status and save results.
    """
    # Set up logging
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=args.loglevel or logging.INFO, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S")

    _logger.debug(f"Started processing data at {datetime.now().isoformat()}")

    # Create the results folder if it doesn't exist
    if not os.path.exists(args.results_folder):
        os.makedirs(args.results_folder)
        _logger.info(f"Created results folder at {args.results_folder}")

    try:
        # Read the CSV to get area for each sample
        data = pd.read_csv(args.input_file, header=None)
        Names = data.iloc[:, 0]  # Sample names
        Areas = data.iloc[:, 1]  # Cross-sectional areas
    except FileNotFoundError:
        _logger.error(f"Input file not found: {args.input_file}")
        raise
    except Exception as e:
        _logger.error(f"Error reading input file: {e}")
        raise

    # Process each sample
    for i in range(len(data)):
        filenombe = str(Names.iloc[i]).strip()  # Get the filename/identifier
        area = float(Areas.iloc[i])             # Get the area value for the sample

        input_raw_file = os.path.join(args.input_folder, f'{filenombe}_fuse.csv')

        if os.path.exists(input_raw_file):
            _logger.info(f"Processing file: {filenombe} with area: {area} {args.Aunit}")

            try:
                stressstrain2(
                    area,
                    fcol=args.fcol,
                    etcol=args.etcol,
                    filenombe=filenombe,
                    input_folder=args.input_folder,
                    results_folder=args.results_folder,
                    Aunit=args.Aunit,
                    Funit=args.Funit,
                    Sunit=args.Sunit
                )
            except Exception as e:
                _logger.error(f"An unexpected error occurred while processing file {filenombe}: {e}")
                continue
        else:
            if args.loglevel <= logging.INFO:  # Log warnings only if verbosity is enabled
                _logger.warning(f"File not found: {input_raw_file}")
            continue

    _logger.info(f"Finished processing data at {datetime.now().isoformat()}")

