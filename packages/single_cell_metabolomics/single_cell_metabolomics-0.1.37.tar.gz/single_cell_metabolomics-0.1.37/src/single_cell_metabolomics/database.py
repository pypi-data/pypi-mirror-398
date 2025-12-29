import psycopg
from psycopg.sql import SQL, Identifier
from psycopg.types.json import Jsonb
import pandas as pd
from .config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class DatabaseController:
    def __init__(self, table_name='analysis_results', compression_threshold_mb=10):
        self.conn = self.connect_db()
        self.table_name = table_name
        self.compression_threshold_mb = compression_threshold_mb

    def connect_db(self):
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn

    def create_data(self, serial_number, dataset_uid, pipeline_stage, result_type, result_data):
        try:
            with self.conn.cursor() as cursor:
                insert_sql = SQL('''
                    INSERT INTO {} ("serialNumber", "datasetUid", "pipelineStage", "resultName", "resultData")
                    VALUES (%s, %s, %s, %s, %s)
                ''').format(Identifier(self.table_name))
                cursor.execute(insert_sql, (serial_number, dataset_uid, pipeline_stage, result_type, Jsonb(result_data)))
                self.conn.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")
            raise e
    
    def read_data(self, serial_number, dataset_uid, pipeline_stage, result_type):
        try:
            with self.conn.cursor() as cursor:
                select_sql = SQL('''
                    SELECT "resultData" FROM {}
                    WHERE "serialNumber" = %s AND "datasetUid" = %s AND "pipelineStage" = %s AND "resultName" = %s
                ''').format(Identifier(self.table_name))
                cursor.execute(select_sql, (serial_number, dataset_uid, pipeline_stage, result_type))
                result = cursor.fetchall()
                if not result:
                    return None
                return result

        except Exception as e:
            print(f"Error reading data: {e}")
            raise e
    
    def update_data(self, serial_number, dataset_uid, pipeline_stage, result_type, new_result_data):
        try:
            with self.conn.cursor() as cursor:
                update_sql = SQL('''
                    UPDATE {}
                    SET "resultData" = %s, "updatedAt" = NOW()
                    WHERE "serialNumber" = %s AND "datasetUid" = %s AND "pipelineStage" = %s AND "resultName" = %s
                ''').format(Identifier(self.table_name))
                cursor.execute(update_sql, (Jsonb(new_result_data), serial_number, dataset_uid, pipeline_stage, result_type))
                self.conn.commit()
        except Exception as e:
            print(f"Error updating data: {e}")
            raise e

    def delete_data(self, serial_number, dataset_uid, pipeline_stage, result_type):
        try:
            with self.conn.cursor() as cursor:
                delete_sql = SQL('''
                    DELETE FROM {}
                    WHERE "serialNumber" = %s AND "datasetUid" = %s AND "pipelineStage" = %s AND "resultName" = %s
                ''').format(Identifier(self.table_name))
                cursor.execute(delete_sql, (serial_number, dataset_uid, pipeline_stage, result_type))
                self.conn.commit()
        except Exception as e:
            print(f"Error deleting data: {e}")
            raise e

    def save_large_dataframe(self, serial_number, dataset_uid, pipeline_stage, result_type, result_dataframe, storage_folder):
        """Save large dataframe to Parquet file and store metadata in DB"""
        try:
            # Save dataframe to Parquet
            storage_path = storage_folder / f"{dataset_uid}_{pipeline_stage}_{result_type}.parquet"
            result_dataframe.to_parquet(
                path=storage_path,
                engine='pyarrow',
                compression='snappy',
                index=False
            )
            result_data = {
                'storage_path': str(storage_path),
                'file_size_bytes': storage_path.stat().st_size,
                'row_count': len(result_dataframe),
                'column_names': list(result_dataframe.columns)
            }
            self.create_data(serial_number, dataset_uid, pipeline_stage, result_type, result_data)
        except Exception as e:
            print(f"Error saving large dataframe: {e}")
            raise e
        
    def load_large_dataframe(self, serial_number, dataset_uid, pipeline_stage, result_type):
        """Load large dataframe from Parquet file using metadata from DB"""
        try:
            result_records = self.read_data(serial_number, dataset_uid, pipeline_stage, result_type)
            if not result_records:
                print(f"No data found for dataset {dataset_uid}, stage {pipeline_stage}, type {result_type}")
                return None
            result_data = result_records[0][0]
            storage_path = result_data['storage_path']
            df = pd.read_parquet(storage_path)
            if len(df) != result_data['row_count']:
                print(f"Warning: Expected {result_data['row_count']} rows, got {len(df)}")
            return df
        except Exception as e:
            print(f"Error loading large dataframe: {e}")
            raise e

    def close_connection(self):
        if self.conn:
            self.conn.close()


# # Configuration
# PARQUET_BASE_DIR = "/data/analysis_results"

# def save_analysis_result(dataset_id, stage, dataframe):
#     """Save large result to Parquet, metadata to PostgreSQL"""
    
#     # Create directory structure
#     output_dir = Path(PARQUET_BASE_DIR) / f"dataset_{dataset_id}" / stage
#     output_dir.mkdir(parents=True, exist_ok=True)
    
#     # Save to Parquet
#     output_path = output_dir / "data.parquet"
#     dataframe.to_parquet(
#         output_path,
#         engine='pyarrow',
#         compression='snappy',  # good balance of speed/size
#         index=False
#     )
    
#     # Get metadata
#     file_size = output_path.stat().st_size
#     row_count = len(dataframe)
    
#     # Save metadata to PostgreSQL
#     conn = psycopg2.connect("postgresql://user:pass@localhost/mydb")
#     with conn.cursor() as cur:
#         cur.execute("""
#             INSERT INTO analysis_results 
#             (dataset_id, pipeline_stage, storage_type, storage_path, 
#              row_count, file_size_bytes, column_names, computed_at)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
#             RETURNING result_id
#         """, (
#             dataset_id,
#             stage,
#             'parquet',
#             str(output_path),
#             row_count,
#             file_size,
#             list(dataframe.columns)
#         ))
#         result_id = cur.fetchone()[0]
#     conn.commit()
#     conn.close()
    
#     return result_id

# def load_analysis_result(dataset_id, stage):
#     """Load result from Parquet"""
    
#     # Get path from PostgreSQL
#     conn = psycopg2.connect("postgresql://user:pass@localhost/mydb")
#     with conn.cursor() as cur:
#         cur.execute("""
#             SELECT storage_path, row_count
#             FROM analysis_results
#             WHERE dataset_id = %s AND pipeline_stage = %s
#             ORDER BY computed_at DESC
#             LIMIT 1
#         """, (dataset_id, stage))
        
#         result = cur.fetchone()
#         if not result:
#             raise ValueError(f"No result found for dataset {dataset_id}, stage {stage}")
        
#         storage_path, expected_rows = result
#     conn.close()
    
#     # Load from Parquet
#     df = pd.read_parquet(storage_path)
    
#     # Validate
#     if len(df) != expected_rows:
#         print(f"Warning: Expected {expected_rows} rows, got {len(df)}")
    
#     return df