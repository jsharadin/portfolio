# Project Overview
This project involves working with high-frequency trading data to compute and analyze order flow imbalance (OFI) metrics.

## Steps to Run the Project

### Step 1: Load Data
Run the file `data_load` in the `data` folder. This notebook loads the data files in the `.dbn.zst` format, converts them into Pandas dataframes, and merges them. The final dataframe is saved as a `.pkl` (pickle) file for further use in other Jupyter notebooks.

**Note:** The `data` folder does not contain the actual `.dbn.zst` data files due to GitHub's file size limitations. You will need to obtain the data separately and place it in the `data` folder before running the code.

### Step 2: Preprocess the Data
Open and run the code in the `notebooks/preprocessing` notebook to preprocess the data.

### Step 3: OFI Computation and Analysis
Open and run the code in the `notebooks/ofi_computation_and_analysis` notebook for computing and analyzing the order flow imbalance metrics.

### Step 4: View Results
Open the `results` folder to view the generated images and analysis results.

## Dependencies
Ensure all the packages listed in the `requirements.txt` file are installed before running the code.
