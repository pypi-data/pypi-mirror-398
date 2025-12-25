import logging
import textwrap
from aimpf.contrib.kate_kelly.db38pulling import db38pulling

_logger = logging.getLogger(__name__)

def add_subcommands(subparsers):
    """Add Kate Kelly's commands."""
    parser = subparsers.add_parser("kate-kelly", help="Commands for Kate Kelly's work.")
    work_parsers = parser.add_subparsers(title="Work Categories", dest="work")

    # Add 'db38pulling' subcommand
    db38_parser = work_parsers.add_parser(
        "db38pulling",
        help="Pull data from DB38.",
        description=textwrap.dedent(
            """
            Pulls data from DB38, a SQL database used to collect experimental,
            maintenance, and telemetry data from the Fanuc, Basler Camera,
            power supply, and IR camera.
            """))
    db38_parser.add_argument("-l", "--experiment-list",
                             type=str,
                             help="Pull data related to specific experiments. "
                                  "Experiments names separated by commas")
    db38_parser.add_argument("-f", "--experiment-file",
                             type=str,
                             help="Pull data related to experiments listed in "
                                  "a file, one experiment name per line")
    db38_parser.add_argument("-m", "--master-folder",
                             type=str,
                             default="Backup-of-mysql",
                             help="Folder to contain a backup of DB38.")
    db38_parser.add_argument("-e", "--exclude-motion-data",
                             action="store_true",
                             help="Exclude motion data.")
    db38_parser.add_argument("-u", "--username",
                             type=str,
                             help="Carta username. Can also be set using the "
                                  "SBGSECRET_CARTA_USERNAME environment "
                                  "variable.")
    db38_parser.add_argument("-p", "--password",
                             type=str,
                             help="Carta password. Can also be set using the "
                                  "SBGSECRET_CARTA_PASSWORD environment "
                                  "variable.")
    db38_parser.add_argument("-v", "--verbose",
                             dest="loglevel",
                             action="store_const",
                             const=logging.INFO,
                             help="Set loglevel to INFO")
    db38_parser.add_argument("-vv", "--very-verbose",
                             dest="loglevel",
                             action="store_const",
                             const=logging.DEBUG,
                             help="Set loglevel to DEBUG")
    db38_parser.set_defaults(func=handle_db38pulling)

def handle_db38pulling(args):
    """Handle the DB38 pulling task."""
    db38pulling(
        experiment_list=args.experiment_list,
        experiment_file=args.experiment_file,
        master_folder=args.master_folder,
        motion_toggle=not args.exclude_motion_data,
        username=args.username,
        password=args.password
    )

