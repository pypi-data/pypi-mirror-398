# %%
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix, save_npz
import pyopenms as oms
# import multiprocessing as mp
# import itertools
# from functools import partial

from typing import List
from pathlib import Path
import typer
from loguru import logger
from tqdm import tqdm

from .database import DatabaseController

resultDBWorker = DatabaseController(table_name='analysis_results')

# %%
app = typer.Typer(add_completion=False)

# @app.command()
# def main(
#     # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
#     input_path: Path = RAW_DATA_DIR / "dataset.csv",
#     output_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
#     # ----------------------------------------------
# ):
#     # ---- REPLACE THIS WITH YOUR OWN CODE ----
#     logger.info("Processing dataset...")
#     for i in tqdm(range(10), total=10):
#         if i == 5:
#             logger.info("Something happened for iteration 5.")
#     logger.success("Processing dataset complete.")
#     # -----------------------------------------

@app.command()
def mzml2tsv(
    input_path = Path('.'),
    output_path = Path('.'),
    integration_type: str = 'sum',
    lc_lower_bound: float = 0.0,
    lc_upper_bound: float = 300.0
):
    """
    Convert mzML file to tsv file with three columns: mode, position, intensity.
    integration_type: 'sum' or 'mean' to indicate how to integrate intensities across scans.
    """
    logger.info(f'Read file: {input_path}')
    exp = oms.MSExperiment()
    oms.MzMLFile().load(input_path, exp)
    spectra = exp.getSpectra()
    spectra_ms1 = [
        s for s in spectra
        if s.getMSLevel() == 1 and
        lc_lower_bound <= s.getRT() <= lc_upper_bound
    ]

    positions = []
    intensities = []
    polarities = []
    polarity_map = {
        oms.IonSource.Polarity.POSITIVE: 'positive',
        oms.IonSource.Polarity.NEGATIVE: 'negative',
        oms.IonSource.Polarity.POLNULL: 'polnull'
    }
    scan_number = len(spectra_ms1)
    for i in range(scan_number):
        positions.extend(spectra_ms1[i].get_peaks()[0])
        intensities.extend(spectra_ms1[i].get_peaks()[1])
        polarities.extend(
            [polarity_map.get(spectra_ms1[i].getInstrumentSettings().getPolarity(), None)] *
            len(spectra_ms1[i].get_peaks()[0])
        )
    data = pd.DataFrame(
        {
            'position': positions,
            'intensity': intensities,
            'mode': polarities
        }
    )
    data['position'] = np.round(data['position'], 4)
    if integration_type == 'mean':
        data['intensity'] = data['intensity'] / scan_number
    data = data \
        .groupby(['mode', 'position']) \
        .agg({'intensity': 'sum'}) \
        .reset_index()

    logger.info(f'Write file: {output_path}')
    data.to_csv(output_path, sep='\t', index=False, header=False)

def create_bins(lower_bound, upper_bound, bin_width):
    bins = []
    added_bound = lower_bound
    while added_bound < upper_bound:
        bins.append(added_bound)
        added_bound = added_bound + added_bound * bin_width / 1e6
    bins.append(added_bound)
    return bins

def get_bins_center(bins):
    n = len(bins)
    bins = np.array(bins)
    bin_center = (bins[:n-1] + bins[1:]) / 2
    return bin_center

@app.command()
def bindata(
    input_path = Path('.'),
    output_path = Path('.'),
    bin_width_value: float = 0.0003,
    bin_width_unit: str = 'm/z',
    ms_lower_bound: float = 100,
    ms_upper_bound: float = 1500
):
    """
    Bin the mass spectrometry data.
    bin_width_unit: 'm/z' or 'ppm' to indicate the unit of bin_width.
    ms_lower_bound and ms_upper_bound define the range of mass/charge ratios to consider.
    """
    logger.info(f'Read file: {input_path}')
    data = pd.read_table(input_path, header=None, names=['mode', 'position', 'intensity'])
    data = data[(data['position'] >= ms_lower_bound) & (data['position'] <= ms_upper_bound)]
    if bin_width_unit == 'ppm':
        bins = create_bins(ms_lower_bound, ms_upper_bound, bin_width_value)
    elif bin_width_unit == 'm/z':
        bins = np.arange(ms_lower_bound - bin_width_value / 2, ms_upper_bound + bin_width_value, bin_width_value)
    else:
        logger.error(f'Invalid bin_width_unit: {bin_width_unit}. Use "m/z" or "ppm".')
        raise ValueError(f'Invalid bin_width_unit: {bin_width_unit}. Use "m/z" or "ppm".')
    bins_center = get_bins_center(bins)
    data['bin_index'] = np.digitize(data['position'], bins, right=False) - 1

    binned_data = data.groupby(['mode', 'bin_index']).agg({'position': 'mean', 'intensity': 'sum'}).reset_index()
    bin_center = bins_center[binned_data['bin_index']]
    binned_data['bin_center'] = [f'{i:.4f}' for i in bin_center]

    output = binned_data[['mode', 'bin_center', 'intensity']]
    logger.info(f'Write file: {output_path}')
    output.to_csv(output_path, sep='\t', index=False, header=False)


def read_tsv_file(file_path):
    """
    Reads a tsv file and renames the columns for merging.
    """
    try:
        df = pd.read_table(
            file_path,
            sep='\t',
            header=None,
            names=['mode', 'mass', f'{file_path.stem}']
        )
        return df
    except FileNotFoundError:
        logger.error(f'File not found: {file_path}')
        return None
    except pd.errors.EmptyDataError:
        logger.error(f'Empty tsv file: {file_path}')
        return None
    except Exception as e:
        logger.error(f'Error reading file {file_path}: {e}')
        return None

# def build_sparse_matrix(dataframes, mass_set):
#     """
#     Builds a sparse matrix from a list of DataFrames based on 'mode' and 'mass_binned'.
#     """
#     mass_list = sorted(list(mass_set))
#     row_names = mass_list
#     index_map = {mass: idx for idx, mass in enumerate(mass_list)}
#     rows = [] # feature indices
#     cols = [] # sample indices
#     data = []
#     column_names = []
#     for col_idx, df in tqdm(enumerate(dataframes), total=len(dataframes)):
#         column_names.append(df.columns[-1])  # Last column is the intensity
#         for _, row in df.iterrows():
#             mass_key = (row['mode'], row['mass'])
#             if mass_key in index_map:
#                 row_idx = index_map[mass_key]
#                 rows.append(row_idx)
#                 cols.append(col_idx)
#                 data.append(row.iloc[-1])  # Last column is the intensity

#     sparse_matrix = coo_matrix(
#         (data, (rows, cols)),
#         shape=(len(row_names), len(dataframes))
#     )
#     return sparse_matrix, row_names, column_names

# def transpose_to_csr_matrix(sparse_matrix, row_names, column_names):
#     """
#     Transposes a sparse matrix.
#     """
#     return sparse_matrix.transpose().tocsr(), column_names, row_names

@app.command()
def concattsv(
    serial_number: str = '',
    dataset_uid: int = 42,
    input_tsv_list_txt: str = '',
    output_parquet_folder: str = '.'
):
    """
    Combines a list of DataFrames on the 'mode' and 'mass' columns using sparse matrix representation.
    """
    # dataframes = []
    valid_dataframe_paths = []
    mass_set = set()
    with open(input_tsv_list_txt, 'r') as file:
        input_tsvs = file.read().strip().split('\n')
    logger.info(f'Input tsv files from {input_tsv_list_txt}')
    logger.info('Gathering mass features from input tsv files...')
    for tsv in tqdm(input_tsvs):
        df = read_tsv_file(Path(tsv))
        if df is not None:
            # dataframes.append(df)
            valid_dataframe_paths.append(tsv)
            mass_set.update(zip(df['mode'], df['mass']))

    if not valid_dataframe_paths:
        logger.error('No valid dataframes to combine.')
        return None

    try:
        logger.info(f'Build sparse matrix from {len(valid_dataframe_paths)} dataframes.')
        # sparse_matrix, row_feature_names, column_sample_names = build_sparse_matrix(dataframes, mass_set)

        mass_list = sorted(list(mass_set))
        row_feature_names = mass_list
        index_map = {mass: idx for idx, mass in enumerate(mass_list)}
        rows = [] # feature indices
        cols = [] # sample indices
        data = []
        column_sample_names = []
        for col_idx, df_path in tqdm(enumerate(valid_dataframe_paths), total=len(valid_dataframe_paths)):
            df = read_tsv_file(Path(df_path))
            if df is None:
                continue
            column_sample_names.append(df.columns[-1])  # Last column is the intensity
            for _, row in df.iterrows():
                mass_key = (row['mode'], row['mass'])
                if mass_key in index_map:
                    row_idx = index_map[mass_key]
                else:
                    logger.error(f'Mass key {mass_key} not found in index map.')
                    continue
                rows.append(row_idx)
                cols.append(col_idx)
                data.append(row.iloc[-1])  # Last column is the intensity

        sparse_matrix = coo_matrix(
            (data, (rows, cols)),
            shape=(len(row_feature_names), len(column_sample_names))
        )
        logger.info(f'Sparse matrix shape: {sparse_matrix.shape}, nnz: {sparse_matrix.nnz}')

        logger.info(f'Saving sparse matrix and metadata to {output_parquet_folder} ...')
        row_df = pd.DataFrame(row_feature_names, columns=['mode', 'mass'])
        row_df['index'] = range(len(row_feature_names))
        row_df.to_csv(
            Path(output_parquet_folder) / 'row_feature_names.tsv',
            sep='\t',
            index=False,
            header=True
        )
        col_df = pd.DataFrame(column_sample_names, columns=['sample'])
        col_df['index'] = range(len(column_sample_names))
        col_df.to_csv(
            Path(output_parquet_folder) / 'column_sample_names.tsv',
            sep='\t',
            index=False,
            header=True
        )

        long_df = pd.DataFrame({
            'row': sparse_matrix.row,
            'col': sparse_matrix.col,
            'value': sparse_matrix.data
        })
        # TODO: Bring the database control to the analysis server
        resultDBWorker.save_large_dataframe(
            serial_number = serial_number,
            dataset_uid = dataset_uid,
            pipeline_stage = 'preparation',
            result_type = 'mergetsv_sparse_matrix',
            result_dataframe = long_df,
            storage_folder = Path(output_parquet_folder)
        )
        logger.success('Concatenate complete.')

        # TODO: reduce RSS by saving in chunks if necessary

    except Exception as e:
        logger.error(f'Error concatenating DataFrames: {e}')
        raise e


if __name__ == '__main__':
    app()

# %%
