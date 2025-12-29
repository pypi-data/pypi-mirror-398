# %%
import duckdb
from pathlib import Path
import typer
from loguru import logger
# from tqdm import tqdm


# Notice: DuckDB use Lazy Evaluation for DuckDBPyRelation objects.
# %%
class FilterExecutor:
    def __init__(
            self,
            matrix_data_path: str,
            matrix_row_path: str,
            matrix_column_path: str,
            metadata_path: str
        ):
        self.matrix_data_path = matrix_data_path
        self.matrix_row_path = matrix_row_path
        self.matrix_column_path = matrix_column_path
        self.metadata_path = metadata_path

        self.conn = duckdb.connect(database = ":memory:")
        self.conn.read_parquet(matrix_data_path).create('matrix_data')
        self.conn.read_csv(matrix_row_path, sep='\t').create('matrix_row')
        self.conn.read_csv(matrix_column_path, sep='\t').create('matrix_column')
        self.conn.read_csv(metadata_path).create('metadata')

        # TODO: implement blank and batch filtration
        # do_blank_filtration: bool = False,
        # blank_label: str|None = None,
        # do_within_batch_filtration: bool = False,
        # batch_column: str|None = None,
        # blank_filtration_ratio: float = 5

    def close(self) -> None:
        self.conn.close()

    def update_table_with_sql(
            self,
            table_name: str,
            query_str: str
        ) -> None:
        """
        Update a table in the DuckDB connection using a SQL query.
        Args:
            table_name (str): The name of the table to update.
            query_str (str): The SQL query to create the new table.
        Returns:
            None
        """
        self.conn.sql(query_str).create('temp_table')
        self.conn.sql(f'DROP TABLE IF EXISTS {table_name}')
        self.conn.sql(f'ALTER TABLE temp_table RENAME TO {table_name}')

    def validate_min_counts(
            self,
            min_features_for_sample: int = 200,
            min_samples_for_feature: int = 3
        ) -> bool:
        """
        Validate the filtering results by checking the minimum feature and sample counts.
        Args:
            min_features_for_sample (int): Minimum number of features required for each sample.
            min_samples_for_feature (int): Minimum number of samples required for each feature.
        Returns:
            Tuple[int, int]: Minimum feature count per sample and minimum sample count per feature.
        """
        query_str = f'''
        WITH
            FeatureCounts AS (
                SELECT
                    col,
                    COUNT(value) AS feature_count
                FROM matrix_data
                GROUP BY col
            ),
            SampleCounts AS (
                SELECT
                    row,
                    COUNT(value) AS sample_count
                FROM matrix_data
                GROUP BY row
            )
        SELECT
            (SELECT MIN(feature_count) FROM FeatureCounts) AS min_feature_count,
            (SELECT MIN(sample_count) FROM SampleCounts) AS min_sample_count
        '''
        result_df = self.conn.sql(query_str).to_df()
        min_feature_count = result_df.iat[0, 0]
        min_sample_count = result_df.iat[0, 1]
        # min_feature_count = self.matrix_data \
        #     .aggregate('col, count(value) as feature_count', group_expr='col') \
        #     .min('feature_count') \
        #     .to_df().iat[0, 0]
        # min_sample_count = self.matrix_data \
        #     .aggregate('row, count(value) as sample_count', group_expr='row') \
        #     .min('sample_count') \
        #     .to_df().iat[0, 0]
        logger.info(f'Validation results - Minimum feature count per sample: {min_feature_count}, Minimum sample count per feature: {min_sample_count}.')
        if min_feature_count < min_features_for_sample:
            logger.warning(f'Minimum feature count per sample is {min_feature_count}, which is less than the threshold of {min_features_for_sample}.')
            return False
        if min_sample_count < min_samples_for_feature:
            logger.warning(f'Minimum sample count per feature is {min_sample_count}, which is less than the threshold of {min_samples_for_feature}.')
            return False
        return True

    def filter_min_counts(
            self,
            min_features_for_sample: int = 200,
            min_samples_for_feature: int = 3
        ) -> None:
        """
        Filter the data based on minimum feature and sample counts.
        Args:
            min_features_for_sample (int): Minimum number of features required for each sample.
            min_samples_for_feature (int): Minimum number of samples required for each feature.
        Returns:
            duckdb.DuckDBPyConnection: The filtered data table.
        """
        logger.info(f'Filtering data with min_features_for_sample={min_features_for_sample} and min_samples_for_feature={min_samples_for_feature}.')
        query_str = f'''
        WITH
            FilteredSamples AS (
                SELECT
                    col,
                    COUNT(value) AS feature_count
                FROM matrix_data
                GROUP BY col
                HAVING feature_count >= {min_features_for_sample}
            ),
            FilteredFeatures AS (
                SELECT
                    row,
                    COUNT(value) AS sample_count
                FROM matrix_data
                GROUP BY row
                HAVING sample_count >= {min_samples_for_feature}
            )
        SELECT *
        FROM matrix_data
        WHERE col IN (SELECT col FROM FilteredSamples)
        AND row IN (SELECT row FROM FilteredFeatures)
        '''
        # self.conn.sql(query_str).create('matrix_new_data')
        # self.conn.sql('DROP TABLE matrix_data')
        # self.conn.sql('ALTER TABLE matrix_new_data RENAME TO matrix_data')
        self.update_table_with_sql('matrix_data', query_str)

    def filter_strict_min_counts(
            self,
            min_features_for_sample: int = 200,
            min_samples_for_feature: int = 3
        ) -> None:
        """
        Strictly filter the data based on minimum feature and sample counts until convergence.
        Args:
            min_features_for_sample (int): Minimum number of features required for each sample.
            min_samples_for_feature (int): Minimum number of samples required for each feature.
        """
        while True:
            self.filter_min_counts(
                min_features_for_sample,
                min_samples_for_feature
            )
            current_status = self.validate_min_counts(
                min_features_for_sample,
                min_samples_for_feature
            )
            if current_status:
                break
        result_shape = self.conn.sql('SELECT COUNT(*) AS count_rows, COUNT(DISTINCT col) AS count_cols FROM matrix_data').to_df()
        n_unique_rows = self.conn.sql('SELECT COUNT(DISTINCT row) AS count_rows FROM matrix_data').to_df().iat[0, 0]
        n_unique_cols = self.conn.sql('SELECT COUNT(DISTINCT col) AS count_cols FROM matrix_data').to_df().iat[0, 0]
        logger.info(f"Strict filtering completed. Resulting data shape: ({result_shape.iat[0, 0]}, {result_shape.iat[0, 1]}).")
        logger.info(f"Number of unique rows: {n_unique_rows}, Number of unique columns: {n_unique_cols}")

    def remove_unused_samples(self) -> None:
        """
        Remove unused samples from the matrix_column table.
        """
        logger.info(f'''Number of distinct columns: {
            self.conn.sql('SELECT COUNT(*) FROM matrix_column').to_df().iat[0, 0]
        }''')
        query_str = f'''
        SELECT * FROM matrix_column
        WHERE index IN (SELECT DISTINCT col FROM matrix_data)
        '''
        self.update_table_with_sql('matrix_column', query_str)
        logger.info(f'''Number of distinct columns after filtering: {
            self.conn.sql('SELECT COUNT(*) FROM matrix_column').to_df().iat[0, 0]
        }''')
    
    def remove_unused_features(self) -> None:
        """
        Remove unused features from the matrix_row table.
        """
        logger.info(f'''Number of distinct rows: {
            self.conn.sql('SELECT COUNT(*) FROM matrix_row').to_df().iat[0, 0]
        }''')
        query_str = f'''
        SELECT * FROM matrix_row
        WHERE index IN (SELECT DISTINCT row FROM matrix_data)
        '''
        self.update_table_with_sql('matrix_row', query_str)
        logger.info(f'''Number of distinct rows after filtering: {
            self.conn.sql('SELECT COUNT(*) FROM matrix_row').to_df().iat[0, 0]
        }''')
    
    def save_results(
            self,
            output_matrix_data_path: str,
            output_matrix_row_path: str,
            output_matrix_column_path: str
        ) -> None:
        """
        Save the filtered results to specified file paths.
        Args:
            output_matrix_data_path (str): Path to save the filtered matrix data.
            output_matrix_row_path (str): Path to save the filtered matrix row data.
            output_matrix_column_path (str): Path to save the filtered matrix column data.
        """
        Path(output_matrix_data_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_matrix_row_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_matrix_column_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn.sql('SELECT * FROM matrix_data') \
            .to_parquet(output_matrix_data_path)
        self.conn.sql('SELECT * FROM matrix_row') \
            .to_csv(output_matrix_row_path, sep='\t')
        self.conn.sql('SELECT * FROM matrix_column') \
            .to_csv(output_matrix_column_path, sep='\t')
        logger.info(f"Filtered results saved to {output_matrix_data_path}, {output_matrix_row_path}, and {output_matrix_column_path}.")

# # %%
# test_path = '/home/server/YLCproject_SingleCellMetabolomePlatform/SCM/analysis/test/results/Preparation/Concat_MS1/1_preprocessing_mergetsv_sparse_matrix.parquet'
# duckdb.read_parquet(test_path)
# row_path = '/home/server/YLCproject_SingleCellMetabolomePlatform/SCM/analysis/test/results/Preparation/Concat_MS1/row_feature_names.tsv'
# duckdb.read_csv(row_path, sep='\t')
# column_path = '/home/server/YLCproject_SingleCellMetabolomePlatform/SCM/analysis/test/results/Preparation/Concat_MS1/column_sample_names.tsv'
# duckdb.read_csv(column_path, sep='\t')

# # %%
# min_sample_number = 3
# min_feature_number = 200

# metadata_path = '/home/server/YLCproject_SingleCellMetabolomePlatform/SCM/analysis/test/all_raw_metadata.csv'
# do_blank_filtration = True
# blank_label = 'matrix'
# do_within_batch_filtration = True
# batch_column = 'batch'
# blank_filtration_ratio = 5.0

# # %%
# filterExecutor = FilterExecutor(
#     matrix_data_path=test_path,
#     matrix_row_path=row_path,
#     matrix_column_path=column_path,
#     metadata_path=metadata_path
# )

# # %%
# filterExecutor.filter_strict_min_counts(
#     min_features_for_sample=min_feature_number,
#     min_samples_for_feature=min_sample_number
# )

# # %%
# filterExecutor.remove_unused_features()
# filterExecutor.remove_unused_samples()

# # %%
# filterExecutor.save_results(
#     output_matrix_data_path = 'temp/Concat_MS1/1_preprocessing_mergetsv_sparse_matrix_filtered.parquet',
#     output_matrix_row_path = 'temp/Concat_MS1/row_feature_names_filtered.tsv',
#     output_matrix_column_path = 'temp/Concat_MS1/column_sample_names_filtered.tsv'
# )



# %%
app = typer.Typer(add_completion=False)

# %%
@app.command()
def filter_and_mask(
    parquet_path: str = "/path/to/your/input.parquet",
    row_path: str = "/path/to/your/row_feature_names.tsv",
    column_path: str = "/path/to/your/column_sample_names.tsv",
    min_sample_number: int = 3,
    min_feature_number: int = 200,
    metadata_path: str = "/path/to/your/metadata.csv",
    do_blank_filtration: bool = True,
    blank_label: str = "your_blank_label",
    do_within_batch_filtration: bool = True,
    batch_column: str = "your_batch_column",
    blank_filtration_ratio: float = 5.0,
    output_parquet_path: str = "/path/to/your/output.parquet",
    output_row_path: str = "/path/to/your/output_row_feature_names.tsv",
    output_column_path: str = "/path/to/your/output_column_sample_names.tsv",
):
    filterExecutor = FilterExecutor(
        matrix_data_path=parquet_path,
        matrix_row_path=row_path,
        matrix_column_path=column_path,
        metadata_path=metadata_path
    )
    filterExecutor.filter_strict_min_counts(
        min_features_for_sample=min_feature_number,
        min_samples_for_feature=min_sample_number
    )
    filterExecutor.remove_unused_features()
    filterExecutor.remove_unused_samples()
    filterExecutor.save_results(
        output_matrix_data_path=output_parquet_path,
        output_matrix_row_path=output_row_path,
        output_matrix_column_path=output_column_path
    )
    filterExecutor.close()
    logger.success("Data filtering complete.")

# %%
@app.callback()
def callback():
    pass

# %%
if __name__ == '__main__':
    app()