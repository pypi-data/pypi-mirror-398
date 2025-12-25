import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from matplotlib.ticker import ScalarFormatter

def convert_units(value, from_unit, to_unit):
    """
    Convert a numerical value between specified units.

    Args:
        value (float or array-like): The value(s) to convert.
        from_unit (str): The unit of the input value. Supported units are:
            - 'kN': kilonewton
            - 'N': newton
            - 'MPa': megapascal
            - 'Pa': pascal
            - 'mm^2': square millimeters
            - 'in^2': square inches
            - 'N/mm^2': newtons per square millimeter (equivalent to MPa)
        to_unit (str): The desired output unit. Same options as `from_unit`.

    Returns:
        float or array-like: Converted value(s).

    Raises:
        ValueError: If the `from_unit` or `to_unit` is not supported.
    """
    conversion_factors = {
        'kN': 1e3,              # kN to N
        'N': 1,                 # N to N
        'MPa': 1e6,             # MPa to Pa (Pascal)
        'Pa': 1,                # Pa to Pa
        'mm^2': 1,              # mm^2 remains mm^2 for area
        'in^2': 25.4 * 25.4,    # in^2 to mm^2 conversion factor
        'N/mm^2': 1e6,          # 1 N/mm² = 1 MPa = 1e6 Pa
    }

    if from_unit not in conversion_factors or to_unit not in conversion_factors:
        raise ValueError(f"Unsupported units: {from_unit}, {to_unit}")
    
    factor = conversion_factors[from_unit] / conversion_factors[to_unit]
    return value * factor

def check_and_flip(values, threshold=0.8):
    """
    Adjust the sign of an array if the majority of values are negative.

    Args:
        values (array-like): Array of numerical values to check and adjust.
        threshold (float, optional): Proportion of negative values required to flip
            the sign of the array. Defaults to 0.8.

    Returns:
        array-like: Adjusted array with corrected signs.
    """
    negative_count = np.sum(values < 0)
    total_count = len(values)
    if negative_count / total_count > threshold:
        values = values * -1
    return values


def stressstrain2(area, fcol, etcol, filenombe, input_folder, results_folder, Aunit='mm^2', Funit='kN', Sunit='MPa'):
    """
    Calculate and plot the true stress-strain curve for a given material sample.

    This function reads raw stress-strain data from an input CSV file, computes
    engineering and true stress-strain values, and saves the results as a CSV file and a plot.

    Args:
        area (float): Cross-sectional area of the material.
        fcol (int): Column index for force data in the input file (1-based indexing).
        etcol (int): Column index for true strain data in the input file (1-based indexing).
        filenombe (str): Base name of the input file (without extension).
        input_folder (str): Path to the folder containing the input CSV file.
        results_folder (str): Path to the folder where results will be saved.
        Aunit (str, optional): Unit of the cross-sectional area. Defaults to 'mm^2'.
        Funit (str, optional): Unit of the force. Defaults to 'kN'.
        Sunit (str, optional): Desired unit for stress. Defaults to 'MPa'.

    Returns:
        pd.DataFrame: A DataFrame containing engineering strain and stress data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input data is invalid or incomplete.
        Exception: For unexpected errors during calculation or file saving.

    Saves:
        - Stress-strain data as a CSV file in the `results_folder` (e.g., `filenombe_sstrue.csv`).
        - Stress-strain plot as a PNG image in the `results_folder` (e.g., `filenombe_plot.png`).

    Example:
        >>> stressstrain2(
        ...     area=10.0, 
        ...     fcol=2, 
        ...     etcol=4, 
        ...     filenombe="sample1", 
        ...     input_folder="raw_data", 
        ...     results_folder="results"
        ... )
    """
    # File paths
    input_raw_file = os.path.join(input_folder, f'{filenombe}_fuse.csv')
    output_data_path = os.path.join(results_folder, f'{filenombe}_sstrue.csv')
    output_plot_path = os.path.join(results_folder, f'{filenombe}_plot.png')

    # Read the input raw data file
    try:
        raw_reader = pd.read_csv(input_raw_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_raw_file}")
    except Exception as e:
        raise ValueError(f"Error reading input file: {e}")

    # Extract force and true strain data from specified columns
    force = raw_reader.iloc[:, fcol - 1].astype(float)
    true_strain = raw_reader.iloc[:, etcol - 1].astype(float)

    # Unit conversions
    force_u = convert_units(force, Funit, 'N')                      # Convert force to Newtons
    area_u = convert_units(area, Aunit, 'mm^2')                     # Convert area to mm^2
    engineering_stress_u = force_u / area_u                         # Engineering stress in N/mm^2
    engineering_stress = convert_units(engineering_stress_u, 'N/mm^2', Sunit)  # Convert stress to desired unit

    engineering_strain = np.exp(true_strain) - 1
    true_stress = engineering_stress * np.exp(true_strain)

    # Adjust signs for true stress and strain if necessary
    true_stress = check_and_flip(true_stress)
    true_strain = check_and_flip(true_strain)

    # Save engineering strain and stress data to a DataFrame
    sig_ep = pd.DataFrame({'Strain': engineering_strain, 'Stress': engineering_stress})
    sig_ep_true = pd.DataFrame({'Strain': true_strain, 'Stress': true_stress})

    # Plot the true stress-strain curve
    plt.figure(figsize=(9, 6))
    plt.plot(true_strain, true_stress, label='True Stress-Strain')
    plt.xlabel('True Strain')
    plt.ylabel(f'True Stress ({Sunit})')
    plt.title(f'{filenombe} Stress-Strain Curve')
    plt.legend()
    plt.grid(which='major', linestyle=':', alpha=0.4)
    plt.minorticks_on()
    plt.savefig(output_plot_path)
    plt.close()

    # Save the true stress-strain data to a CSV file
    try:
        sig_ep_true.to_csv(output_data_path, index=False)
    except Exception as e:
        raise IOError(f"Error saving output data file: {e}")

    return sig_ep

def process_folder(root_folder_path, config_data, results_dir, logger):
    """
    Process a set of folders to perform strain analysis and generate histograms.

    Args:
        root_folder_path (str): Root path to the folders for error analysis.
        config_data (dict): Configuration dictionary containing a list of folder paths
            under the key `error_analysis_dirs`.
        results_dir (str): Path to save the analysis results and plots.
        logger (logging.Logger): Logger instance for logging warnings and errors.

    Returns:
        list of dict: A list of results for each folder, including:
            - Folder name
            - Root mean square error (RMSE) of mu
            - Average sigma
            - Distribution parameters (mu and sigma) for each file
    """
    num_files = 10

    folder_paths = config_data['error_analysis_dirs']
    results = []

    # Loop through each folder in error_analysis_dirs from the config file
    for folder_name in folder_paths:
        folder_path = os.path.join(root_folder_path, folder_name)

        # Initialize lists for strain data and histogram lengths
        strains = []
        histlength = []

        # Loop through the files in the folder
        for i in range(num_files):
            inputfile = os.path.join(folder_path, f"Paint1-{i:04d}_0.csv")
            if not os.path.exists(inputfile):  # Check if the file exists
                logger.warning(f"File not found: {inputfile}")
                continue  # Skip this file if not found
            data_orig = pd.read_csv(inputfile)
            data = data_orig.values

            # Remove rows where the program flagged as suspect
            data = data[~np.all(data == 0, axis=1)]

            # Store the length of the data
            histlength.append(data.shape[0])
            strains.append(data[:, 1])  # Store the strain data (second column)

        if not strains:
            logger.warning(f"No valid strain data found in folder: {folder_name}")
            continue  # Skip this folder if no data

        # Flatten the strains list
        strains = np.concatenate(strains)

        # Get the min and max values for bin edges
        low = np.min(strains)
        high = np.max(strains)

        # Define the number of bins for the histograms
        num_bins_all = 14  # MATLAB's linspace(low, high, 15) results in 14 bins
        edges_all = np.linspace(low, high, num_bins_all + 1)
        edges_subplot = np.linspace(low, high, (num_bins_all + 1) * 2)

        # Create a figure with a tiled layout for multiple plots
        fig, axs = plt.subplots(3, 4, figsize=(15, 12))
        axs = axs.flatten()

        # Plot histogram of all frames with predefined edges
        axs[0].hist(strains, bins=edges_all, color='#1f77b4', edgecolor='black', linewidth=0.5)
        axs[0].set_title('All Frames')

        # Create a line plot of strains
        x_range = np.arange(1, len(strains) + 1)
        axs[1].plot(x_range, strains, color='#1f77b4')
        axs[1].set_title('Line Plot of Strains')
        axs[1].set_ylim([low, high])

        # Initialize variables for the distribution fitting
        total = []
        yl = []

        # Fit a distribution for each subset of strains and plot
        start_idx = 0
        for i in range(num_files):
            if i >= len(histlength):
                break  # No more data to process
            end_idx = start_idx + histlength[i]
            current_strain = strains[start_idx:end_idx]
            start_idx = end_idx

            if len(current_strain) == 0:
                logger.warning(f"No data for file index {i} in folder {folder_name}.")
                continue  # Skip if no data

            # Check if current_strain has more than one unique value
            if np.unique(current_strain).size <= 1:
                logger.warning(f"Not enough unique data points to fit distribution for file index {i} in folder {folder_name}. Skipping.")
                caption = 'Not enough data to fit distribution'
                axs[i + 2].set_title(caption, fontsize=9)
                continue  # Skip to the next iteration

            # Fit a normal distribution
            mu, std = norm.fit(current_strain)
            total.append([mu, std])

            # Calculate bin centers and scaling factor
            bin_width = edges_subplot[1] - edges_subplot[0]
            scaling_factor = len(current_strain) * bin_width

            # Check if std is zero or very small
            if std < 1e-8:
                logger.warning(f"Standard deviation is zero or too small for file index {i} in folder {folder_name}. Skipping PDF plot.")
                caption = f'mu={mu:.3e}, sigma~0'
                axs[i + 2].hist(current_strain, bins=edges_subplot, color='#1f77b4', edgecolor='black', linewidth=0.5)
                axs[i + 2].set_title(caption, fontsize=9)
            else:
                # Plot histogram using the same bins for all files
                axs[i + 2].hist(current_strain, bins=edges_subplot, color='#1f77b4', edgecolor='black', linewidth=0.5)

                # Plot the fitted normal distribution scaled to histogram counts
                x_fit = np.linspace(edges_subplot[0], edges_subplot[-1], 100)
                p = norm.pdf(x_fit, mu, std) * scaling_factor
                axs[i + 2].plot(x_fit, p, color='red', linewidth=2)
                caption = f'mu={mu:.3e}, sigma={std:.3e}'
                axs[i + 2].set_title(caption, fontsize=9)

            # Store y-limits for later adjustment
            yl.append(axs[i + 2].get_ylim())

        if not total:
            logger.warning(f"No valid data to fit distributions in folder: {folder_name}")
            plt.close(fig)
            continue  # Skip if no data

        # Find the maximum y-limits for consistent scaling
        yl = np.array(yl)
        max_yl = np.max(yl[:, 1])

        # Set the y-limits for all individual histograms to the same max
        for ax in axs[2:]:
            ax.set_ylim(0, max_yl)

        # Set x-limits for all histograms except the line plot
        for idx, ax in enumerate(axs):
            if idx != 1:
                ax.set_xlim(low, high)

        # Apply scientific notation to all plots including the line plot
        for ax in axs:
            ax.xaxis.set_major_formatter(ScalarFormatter())
            ax.xaxis.get_major_formatter().set_scientific(True)
            ax.xaxis.get_major_formatter().set_powerlimits((0, 0))
            ax.yaxis.set_major_formatter(ScalarFormatter())
            ax.yaxis.get_major_formatter().set_scientific(True)
            ax.yaxis.get_major_formatter().set_powerlimits((0, 0))

        # Adjust layout to prevent label overlap
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])  # type: ignore[reportArgumentType]

        # Calculate rmse for mu and average sigma
        total = np.array(total)
        rmse_mu = np.sqrt(np.mean(total[:, 0]**2))
        avg_sigma = np.mean(total[:, 1])

        # Create a title for the figure
        overalltitle = f'rmse mu = {rmse_mu:.3e}, avg sigma = {avg_sigma:.3e}'
        fig.suptitle(f'Facet {folder_name} px\n{overalltitle}', fontsize=12)

        # Save the figure as a PNG image in the results folder
        output_png_filename = os.path.join(results_dir, f"{folder_name}_analysis.png")
        fig.savefig(output_png_filename, format='png')
        plt.close(fig)  # Close the figure to free memory

        # Save the calculated values to a CSV file in the results folder
        output_csv_filename = os.path.join(results_dir, f"{folder_name}_analysis.csv")
        np.savetxt(output_csv_filename, total, delimiter=",", header="mu,sigma", comments="")

        # Add the folder name and results to the summary
        results.append({
            'folder': folder_name,
            'rmse_mu': rmse_mu,
            'avg_sigma': avg_sigma,
            'total': total.tolist()
        })

    return results

def generate_plots(results, results_dir, logger):
    """
    Generate summary plots and CSV files for RMSE and sigma values.

    Args:
        results (list of dict): Results from `process_folder`, including:
            - Folder name
            - RMSE of mu
            - Average sigma
            - Distribution parameters for each file
        results_dir (str): Path to save the summary plots and CSV files.
        logger (logging.Logger): Logger instance for logging errors.

    Saves:
        - Summary plot (PNG): RMSE and average sigma as functions of height.
        - Summary table (CSV): Folder names, heights, RMSE, and sigma values.
    """
    if not results:
        logger.error("No results to generate summary plot!")
        return

    # Extract height, rmse_mu, and avg_sigma from the results
    try:
        heights = [float(os.path.basename(result['folder']).split('_')[1]) for result in results]
    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing heights from folder names: {e}")
        heights = list(range(len(results)))  # Use indices as fallback

    rmse_mus = [result['rmse_mu'] for result in results]
    avg_sigmas = [result['avg_sigma'] for result in results]

    # Create a plot for RMSE Mu and Avg Sigma vs Height
    plt.figure(figsize=(6, 4))
    plt.plot(heights, rmse_mus, marker='o', linestyle='-', color='b', label='RMSE Mu')
    plt.plot(heights, avg_sigmas, marker='o', linestyle='-', color='r', label='Avg Sigma')
    plt.xlabel('Height [px]')
    plt.ylabel('Value [px]')
    plt.title('RMSE Mu and Avg Sigma vs. Height')
    plt.legend()

    # Save the overall results plot as PNG
    output_png_filename = os.path.join(results_dir, "error_analysis_summary_plot.png")
    plt.savefig(output_png_filename, format='png')
    plt.close()

    # Save the overall summary as CSV
    output_df = pd.DataFrame([{
        'folder': result['folder'],
        'height': height,
        'rmse_mu': rmse_mu,
        'avg_sigma': avg_sigma
    } for result, height, rmse_mu, avg_sigma in zip(results, heights, rmse_mus, avg_sigmas)])

    output_csv_filename = os.path.join(results_dir, "error_analysis_summary.csv")
    output_df.to_csv(output_csv_filename, index=False)
