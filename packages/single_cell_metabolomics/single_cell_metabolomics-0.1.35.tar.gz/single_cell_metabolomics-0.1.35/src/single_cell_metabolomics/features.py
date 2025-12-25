# %%
import numpy as np
import pandas as pd
import pyopenms as oms
import matplotlib.pyplot as plt
from typing import List, Tuple
from pathlib import Path

import typer
from loguru import logger
# from tqdm import tqdm

# %%
app = typer.Typer(add_completion=False)

# @app.command()
# def main(
#     # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
#     input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
#     output_path: Path = PROCESSED_DATA_DIR / "features.csv",
#     # -----------------------------------------
# ):
#     # ---- REPLACE THIS WITH YOUR OWN CODE ----
#     logger.info("Generating features from dataset...")
#     for i in tqdm(range(10), total=10):
#         if i == 5:
#             logger.info("Something happened for iteration 5.")
#     logger.success("Features generation complete.")
#     # -----------------------------------------

# %%
class PeakFinder:
    def __init__(self, mzML_file, standard_csv, ppm_tolerance=5):
        logger.info(f'Read file: {mzML_file}')
        exp = oms.MSExperiment()
        oms.MzMLFile().load(mzML_file, exp)
        spectra = exp.getSpectra()
        self.spectra_ms1 = [s for s in spectra if s.getMSLevel() == 1]
        logger.info(f'Read file: {standard_csv}')
        self.standard_MS1 = pd.read_csv(standard_csv)
        self.ppm_tolerance = ppm_tolerance
        self.polarity_map = {
            oms.IonSource.Polarity.POSITIVE: 'positive',
            oms.IonSource.Polarity.NEGATIVE: 'negative',
            oms.IonSource.Polarity.POLNULL: 'polnull'
        }
        self.all_standard_peaks = {}

    def get_peak_position_per_spectrum(self, spectrum, target_position):
        peaks_df = pd.DataFrame(spectrum.get_peaks()).T
        peaks_df.columns = ['position', 'intensity']
        position_upper = target_position * (1 + self.ppm_tolerance / 1e6)
        position_lower = target_position * (1 - self.ppm_tolerance / 1e6)
        accepted_peaks = peaks_df.query(f'position >= {position_lower} & position <= {position_upper}')
        if accepted_peaks.empty:
            return None
        else:
            highest_peak = accepted_peaks.loc[accepted_peaks['intensity'].idxmax(),].to_list()
            return highest_peak

    def get_peak_position(self, spectra_ms1, target_polarity, target_position):
        peak_positions = []
        for spectrum in spectra_ms1:
            if self.polarity_map.get(spectrum.getInstrumentSettings().getPolarity(), None) != target_polarity:
                continue
            peak_position = self.get_peak_position_per_spectrum(spectrum, target_position)
            if peak_position is not None:
                peak_positions.append(peak_position)
        return peak_positions

    def find_peaks_in_file(self):
        for i, row in self.standard_MS1.iterrows():
            print(f'Find peaks for {row["Working name"]}')
            peaks = {
                'positive': self.get_peak_position(self.spectra_ms1, 'positive', row['positive']),
                'negative': self.get_peak_position(self.spectra_ms1, 'negative', row['negative'])
            }
            self.all_standard_peaks[row['Working name']] = peaks

    def get_peak_statistics(self):
        self.all_standard_statistics = pd.DataFrame(columns=['WorkingName', 'Polarity', 'nIdentifiedPeaks', 'nSpectra', 'PositionMean', 'PositionStd', 'IntensityMean', 'IntensityStd'])

        spectrum_polarities = [spectrum.getInstrumentSettings().getPolarity() for spectrum in self.spectra_ms1]
        spectrum_polarities = [self.polarity_map.get(polarity, None) for polarity in spectrum_polarities]
        n_positive = spectrum_polarities.count('positive')
        n_negative = spectrum_polarities.count('negative')

        for key, peaks in self.all_standard_peaks.items():
            for polarity in ['positive', 'negative']:
                peak_data = peaks[polarity]
                n_peaks = len(peak_data)
                
                if n_peaks > 0:
                    positions, intensities = zip(*peak_data)
                    position_mean = np.mean(positions)
                    position_std = np.std(positions)
                    intensity_mean = np.mean(intensities)
                    intensity_std = np.std(intensities)
                else:
                    position_mean = np.nan
                    position_std = np.nan
                    intensity_mean = np.nan
                    intensity_std = np.nan
                
                self.all_standard_statistics.loc[len(self.all_standard_statistics)] = {
                    'WorkingName': key,
                    'Polarity': polarity,
                    'nIdentifiedPeaks': n_peaks,
                    'nSpectra': n_positive if polarity == 'positive' else n_negative,
                    'PositionMean': position_mean,
                    'PositionStd': position_std,
                    'IntensityMean': intensity_mean,
                    'IntensityStd': intensity_std
                }
    
    def get_errors(self, ppm = True):
        self.errors = {}
        self.error_type = 'ppm' if ppm else 'm/z'
        for key, peaks in self.all_standard_peaks.items():
            errors = {}
            for polarity in ['positive', 'negative']:
                peak_data = peaks[polarity]
                n_peaks = len(peak_data)
                if n_peaks > 0:
                    positions, intensities = zip(*peak_data)
                    ms1 = self.standard_MS1.query(f'`Working name` == "{key}"')[polarity].iloc[0]
                    if ppm:
                        errors[polarity] = [(p - ms1) / ms1 * 1e6 for p in positions]
                    else:
                        errors[polarity] = [p - ms1 for p in positions]
                else:
                    errors[polarity] = np.nan
            self.errors[key] = errors
    
    def draw_error_boxplot(
            self,
            standard_list: List[Tuple[str, str]] = None,
            suptitle = None,
            output = None
        ):
        if standard_list is None:
            plotting_standards = list(peak_finder.errors.keys())
            plotting_standards = tuple(zip(plotting_standards * 2, np.repeat(['positive', 'negative'], len(plotting_standards))))
        else:
            plotting_standards = standard_list
        plotting_data = [self.errors[standard][polarity] for standard, polarity in plotting_standards]
        plotting_labels = [f'{standard} {polarity[0]}' for standard, polarity in plotting_standards]
        plt.figure(figsize=(8, 6))
        plt.axhline(y=0, color='black', linestyle='--')
        plt.boxplot(
            plotting_data,
            labels=plotting_labels,
            flierprops={'marker': 'o', 'markersize': 2, 'markerfacecolor': 'black'},
            medianprops={'color': 'black'}
        )
        plt.xticks(rotation=90)
        if self.error_type == 'ppm':
            plt.ylabel('m/z error (ppm)')
        else:
            plt.ylabel('m/z error')
        if suptitle is not None:
            plt.suptitle(suptitle)
        plt.title('m/z error of identification')
        if output is not None:
            plt.savefig(output, dpi=600, bbox_inches='tight')
        plt.show()

@app.command()
def get_standards_scanwise(
    mzML_file = Path('.'),
    standard_csv = Path('.'),
    ppm_tolerance: float = 5,
    output_csv = Path('.')
):
    peak_finder = PeakFinder(mzML_file, standard_csv, ppm_tolerance=ppm_tolerance)
    peak_finder.find_peaks_in_file()
    peak_finder.get_peak_statistics()

    logger.info(f'Write file: {output_csv}')
    peak_finder.all_standard_statistics.to_csv(output_csv, index=False)

@app.callback()
def callback():
    pass

# %%
if __name__ == '__main__':
    app()
