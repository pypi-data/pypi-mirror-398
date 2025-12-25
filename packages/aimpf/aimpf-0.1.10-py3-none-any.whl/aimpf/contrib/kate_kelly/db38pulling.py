import os
import logging
import pathlib
import csv
from dotenv import load_dotenv
import pandas as pd
from aimpf.dispatcher.mysql import Db38
from pycarta.auth import CartaAgent

_logger = logging.getLogger(__name__)

def select_data_func(
        experiment_list=None,
        experiment_file=None,
        master_folder="Backup-of-mysql",
        motion_toggle=True
    ):
    """
    Prepare experiment data based on input parameters.

    This function processes user input to determine the list of experiments to process,
    the master folder to store the results, and whether to include motion data.

    Args:
        experiment_list (Union[List[str], str, None]): A list of experiment names or a comma-separated string of names.
        experiment_file (Optional[str]): Path to a file containing experiment names, one per line.
        master_folder (str): Name of the folder to store results. Defaults to "Backup-of-mysql".
        motion_toggle (bool): Whether to include motion data. Defaults to True.

    Returns:
        Tuple[List[str], str, bool]: A tuple containing the experiment list, the master folder path, and motion toggle status.
    """
    if experiment_list is None and experiment_file is None:
        Experiment_List = ["Franuc_CRS_40_ROT_50IPT"]
    elif experiment_file:
        with open(experiment_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            Experiment_List = [row[0].strip() for row in reader if row]
    else:
        if isinstance(experiment_list, str):
            Experiment_List = [item.strip() for item in experiment_list.split(',')]
        else:
            Experiment_List = experiment_list

    MasterFolder = master_folder
    MotionToggle = motion_toggle

    return Experiment_List, MasterFolder, MotionToggle


def main_func(db38, exp_name, master_folder, motion_toggle):
    """
    Process and save data for a single experiment.

    This function retrieves data for a specific experiment from the database,
    processes it, and saves the results in an Excel file in the specified folder.

    Args:
        db38 (Db38): An instance of Db38 for database interaction.
        exp_name (str): Name of the experiment to process.
        master_folder (str): Path to the folder where results will be saved.
        motion_toggle (bool): Whether to include motion data in the results.

    Raises:
        Exception: If there are issues with database queries or data processing.
    """
    if not isinstance(exp_name, str):
        exp_name = str(exp_name)

    # Create the storage folder
    path = pathlib.Path().resolve()
    if master_folder:
        path = os.path.join(path, master_folder)
        os.makedirs(path, exist_ok=True)

    out_path = os.path.join(path, f"{exp_name}.xlsx")
    _logger.info(f"Saving to {out_path}.")

    with pd.ExcelWriter(out_path, engine='xlsxwriter') as writer:
        database = "ProcessData"
        data_item_tables = [
            "BaslerCameraData_Fronius",
            "PowerSupplyData_Fronius",
            "IRCameraData_Fronius",
            "MaintenanceData_Fronius",
        ] + (["PositionData_Fanuc"] if motion_toggle else [])

        for table in data_item_tables:
            data_ids = []
            if table == "PowerSupplyData_Fronius":
                data_ids = ["ACTUAL_CURRENT", "ACTUAL_VOLTAGE", "ACTUAL_POWER", "ACTUAL_WFS", "DISPLAY_ENERGY"]
            elif table == "IRCameraData_Fronius":
                data_ids = ["Bx1"]
            elif table == "BaslerCameraData_Fronius":
                data_ids = ["CTWD (mm)"]
            elif table == "PositionData_Fanuc":
                data_ids = ["X", "Y", "Z", "W", "P", "R"]
            elif table == "MaintenanceData_Fronius":
                data_ids = ["ACTUAL_WELDINGTIME", "JOBNAME", "JOBNUMBER"]

            for data_item_id in data_ids:
                data = db38.list(
                    database=database,
                    table=table,
                    where=f"ExperimentLabel={exp_name},dataItemId={data_item_id}"
                )
                columns = db38.list_columns(database=database, table=table)["columns"]
                dataframe = pd.DataFrame(data, columns=columns)

                dataframe["dateTime"] = pd.to_datetime(dataframe["dateTime"], errors="coerce")
                dataframe["dateTime"] = dataframe["dateTime"].dt.strftime('%Y-%m-%d %H:%M:%S')

                if table == "IRCameraData_Fronius":
                    dataframe = dataframe[["dateTime", "value"]]
                else:
                    dataframe = dataframe[["dateTime", "value", "BeadNumber"]]

                dataframe.to_excel(writer, sheet_name=f"{data_item_id}", index=False)

    # writer.close()


def db38pulling(
        experiment_list=None,
        experiment_file=None,
        master_folder="Backup-of-mysql",
        motion_toggle=True,
        username=None,
        password=None
    ):
    """
    Main function to process multiple experiments.

    This function processes a list of experiments or reads them from a file, retrieves the data
    for each experiment from the database, and saves the results in Excel files.

    Args:
        experiment_list (Union[List[str], str, None]): A list of experiment names or a comma-separated string of names.
        experiment_file (Optional[str]): Path to a file containing experiment names, one per line.
        master_folder (str): Path to the folder where results will be saved. Defaults to "Backup-of-mysql".
        motion_toggle (bool): Whether to include motion data in the results. Defaults to True.
        username (Optional[str]): Username for database authentication. Defaults to environment variable.
        password (Optional[str]): Password for database authentication. Defaults to environment variable.

    Raises:
        Exception: If there are issues with database authentication or data retrieval.
    """
    load_dotenv()

    db38 = Db38(
        CartaAgent(
            username=username or os.getenv("SBGSECRET_CARTA_USERNAME"),
            password=password or os.getenv("SBGSECRET_CARTA_PASSWORD")
        ),
        namespace="aimpf",
        service="mysql"
    )

    experiment_list, master_folder, motion_toggle = select_data_func(
        experiment_list=experiment_list,
        experiment_file=experiment_file,
        master_folder=master_folder,
        motion_toggle=motion_toggle
    )

    for i, experiment in enumerate(experiment_list):
        _logger.info(f"Running experiment {i + 1}/{len(experiment_list)}: {experiment}")
        main_func(db38, experiment, master_folder, motion_toggle)

    _logger.info("All experiments processed successfully!")
