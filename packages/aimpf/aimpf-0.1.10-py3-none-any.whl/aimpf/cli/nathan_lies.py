import logging
import textwrap
from aimpf.contrib.nathan_lies.mechanical import fuse, error_analysis
import argparse


def add_subcommands(subparsers):
    """Add Nathan Lies' commands."""
    parser = subparsers.add_parser(
        "nathan-lies",
        help="Commands for Nathan Lies' work.",
    )
    work_parsers = parser.add_subparsers(title="Work Categories", dest="work")

    # Add 'mechanical' subcommand
    mechanical_parser = work_parsers.add_parser(
        "mechanical",
        help="Mechanical testing of MoReX alloys.",
    )
    mechanical_parsers = mechanical_parser.add_subparsers(
        title="Mechanical Tasks", dest="task"
    )

    # Add 'fuse' subcommand with properly formatted example
    fuse_parser = mechanical_parsers.add_parser(
        "fuse",
        help="Analyze loading curves for multiple samples.",
        description=textwrap.dedent(
            """
            Analyze loading curves for multiple samples.

            Example:
                Suppose the input CSV file `cross-sectional-area.csv` contains
                the following content:

                    Mo2ReX1,0.01542395
                    Mo2ReX2,0.015418665
                    Mo2ReY1,0.01542483
                    Mo2ReY3,0.0154938
                    ...
                    [sample],[cross-sectional area]

                The file `Mo2ReX1_fuse.csv`, located in the current folder,
                contains the raw stress-strain data for the sample `Mo2ReX1`.
                More generally, the files `[sample]_fuse.csv` contains
                the strain-load data for [sample]. Run the following command to
                process the data:

                    aimpf nathan-lies mechanical fuse --Aunit in^2 cross-sectional-area.csv .

                The generated results include:
                    - A CSV file with two columns (true strain, true stress)
                    - A plot of the load curves in PNG format

                All results are saved in the `results` folder.
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Ensures proper formatting
    )
    fuse_parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input CSV file containing sample names and areas",
    )
    fuse_parser.add_argument(
        "input_folder",
        type=str,
        help="Folder where the input raw data files are located",
    )
    fuse_parser.add_argument(
        "--results_folder",
        type=str,
        default="results",
        help="Folder where the results will be saved (default: 'results')",
    )
    fuse_parser.add_argument(
        "--fcol",
        type=int,
        default=1,
        help="Column index for force data (1-based index)",
    )
    fuse_parser.add_argument(
        "--etcol",
        type=int,
        default=11,
        help="Column index for true strain data (1-based index)",
    )
    fuse_parser.add_argument(
        "--Aunit",
        type=str,
        default="mm^2",
        choices=["mm^2", "in^2"],
        help="Unit of area",
    )
    fuse_parser.add_argument(
        "--Funit",
        type=str,
        default="kN",
        choices=["kN", "N"],
        help="Unit of force",
    )
    fuse_parser.add_argument(
        "--Sunit",
        type=str,
        default="MPa",
        choices=["MPa", "N/mm^2"],
        help="Unit of stress",
    )
    fuse_parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="Set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
        default=logging.WARNING,
    )
    fuse_parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="Set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    fuse_parser.set_defaults(func=handle_mechanical_fuse)

    # Add 'error-analysis' subcommand with properly formatted example
    error_parser = mechanical_parsers.add_parser(
        "error-analysis",
        help="Error analysis of DIC strain measurements.",
        description=textwrap.dedent(
            """
            Conducts an strain error analysis of DIC measurements.

            Example
            -------
            Suppose you have a root folder named `Step0_ErrorAnalysis`
            containing subfolders as specified in `experiment_config.json`:

                experiment_config.json:

                    {
                        "error_analysis_dirs": [
                            "Mo2ReX1_41_20",
                            "Mo2ReX1_61_30",
                            "Mo2ReX1_101_30",
                            "Mo2ReX1_151_30"
                        ]
                    }

            Each sample folder must contain up to 10 DIC patterns:
            
                Step0_ErrorAnalysis/
                    ├── Mo2ReX1_41_20/
                    ├   ├── Paint1-0000_0.csv
                    ├   ├── Paint1-0001_0.csv
                    ├   ├── ...
                    ├   ├── Paint1-0009_0.csv
                    ├── Mo2ReX1_61_30/
                    ├── Mo2ReX1_101_30/
                    ├── Mo2ReX1_151_30/

            The second column in each file (Paint1-%04d_0.csv) is the measured
            strain. Invalid data is demarcated by a row of all zeros. These
            files cannot have a header.

            Run the following command:

                aimpf nathan-lies mechanical error-analysis Step0_ErrorAnalysis experiment_config.json

            Results:

                - Individual analysis CSV and PNG files for each folder.
                - Summary CSV and PNG files saved in the `results/` folder.
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    error_parser.add_argument(
        "root_folder_path",
        type=str,
        help="Path to the root folder containing the experiment data and subfolders",
    )
    error_parser.add_argument(
        "config_file",
        type=str,
        help="Path to the configuration JSON file",
    )
    error_parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="Set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
        default=logging.WARNING,
    )
    error_parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="Set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    error_parser.set_defaults(func=handle_error_analysis)


def handle_mechanical_fuse(args):
    """Handle the fuse analysis."""
    fuse.main(args)


def handle_error_analysis(args):
    """Handle the error analysis."""
    error_analysis.main(args)
