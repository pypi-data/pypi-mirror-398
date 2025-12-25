from pkgbox import date_fn
from pkgbox import num_fn
from pkgbox import islack
from .memton import Memton


class GlobalImport:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        import inspect
        collector = inspect.getargvalues(inspect.getouterframes(inspect.currentframe())[1][0]).locals
        globals().update(collector)


def import_all():
    with GlobalImport():
        ## will fire a warning as its bad practice for python. 
        import numpy as np
        import pandas as pd
        import polars as pl
        import pyarrow as pa
        import pyarrow.compute as pc
        # import pyarrow.compute as pac
        from pandas import json_normalize
        from multiprocessing import Process
        try:
            import pencilbox as pb
        except ImportError:
            print("Module not found. Continuing without it.")
        import logging
        import seaborn as sns
        import matplotlib.pyplot as plt
        from datetime import datetime, date
        from datetime import timedelta
        from pytz import timezone
        import time
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.float_format', lambda x: '%.5f' % x)
        pl.Config.set_tbl_rows(20000)
        pl.Config.set_tbl_cols(200)
        pl.Config.set_fmt_str_lengths(10000)
        pl.Config.set_fmt_float("full")
        # from sklearn.cluster import KMeans
        # from scipy.stats import zscore
        from numpy import asarray
        # from sklearn.preprocessing import MinMaxScaler
        # from IPython.display import display
        import os, sys
        import json
        from typing import Callable
        from functools import partial
        # from scipy.stats import linregress
        import math
        import matplotlib.ticker as mtick
        import papermill as pm
        import shutil
        import requests
        from tabulate import tabulate
        from babel.numbers import format_currency
        import io
        import ast
        import inspect
        from pandasql import sqldf
        import scrapbook as sb
        import gc
        import re
        from decimal import Decimal
        from urllib.parse import urljoin, urlparse
        from pathlib import Path
        import duckdb
        import adbc_driver_postgresql.dbapi as adbc


import_all()
dt = date_fn.Cdt()

def remark(text):
    mem = Memton()
    remarks = mem.get_value("remarks")
    if remarks is None:
        remarks = text
    else:
        remarks = f"{remarks}\n{text}"
    mem.set_value("remarks", remarks)
    sb.glue("remarks", remarks)
    print(text)


def pysqldf(query):
    # Get the calling frame's globals dynamically to avoid scope issues
    frame = inspect.currentframe().f_back
    caller_globals = frame.f_globals
    return sqldf(query, caller_globals)


def ims_buckets():
    ims = pd.read_csv(io.StringIO("""bucket	ids	op
b2b return	[23, 35]	+
b2b return bad	[24, 25, 66, 36, 37, 68]	NA
b2b sale	[22]	-
badstock sale	[133, 134, 135]	NA
crbs	[7, 9, 63, 67]	NA
crwi bad	[87, 88, 89]	NA
customer return	[3, 29]	+
customer sale	[2, 50]	-
dump	[11, 12, 64]	-
excess stock transfer	[17, 92, 124, 125]	-
fresh liquidation	[127]	-
grn	[1, 28]	+
in house picking	[57, 140]	NA
item not received	[131]	NA
negative manual update	[39, 40, 41, 42, 117, 119, 129, 130, 132]	-
positive manual update	[44, 45, 46, 47, 118, 141]	+
positive manual update for grn	[120]	NA
prn	[20, 21, 65]	NA
put away	[38]	NA
putaway from system	[58, 61]	NA
reinventorization	[121, 122]	+
rts inward at warehouse	[136, 137, 138]	NA
secondary sales	[52, 56, 69]	NA
system negative update	[113]	-
system positive update	[112]	+
vendor return	[126]	-
coins positive update	[142]	+
coins negative update	[143]	-
esto positive udpate	[141]	+"""), delimiter='\t')

    # def CPR(x):
    #     result = x['id'].tolist()
    #     return result
    # ims_ndf = ims.groupby(['bucket']).apply(CPR).reset_index()
    # ims_ndf.rename(columns={0: 'ids'}, inplace=True)
    # def treatments(x):
    #     val = ims[ims.bucket == x['bucket']]['consideration'].tolist()[0]
    #     return val
    # ims_ndf['op'] = ims_ndf.apply(lambda x: treatments(x), axis=1)
    # return ims_ndf
    ims.ids = ims.ids.apply(lambda x: ast.literal_eval(x))
    return ims

def bucketise_ims_df(df, update_type_col, consideration_col_list):
    ims_buckets_df = ims_buckets()
    def ntr(x):
        for index, row in ims_buckets_df.iterrows():
            if x[update_type_col] in row['ids']:
                return row['bucket']
        return 'NA'
    def opr(x):
        for index, row in ims_buckets_df.iterrows():
            if x[update_type_col] in row['ids']:
                return row['op']
        return 'NA'
    def run_op(x, col):
        if x['op'] == '+':
            return x[col]
        elif x['op'] == '-':
            return -1*x[col]
        else:
            return 0
    df['bucket'] = df.apply(lambda x: ntr(x), axis = 1)
    df['op'] = df.apply(lambda x: opr(x), axis = 1)
    for col in consideration_col_list:
        df[f'{col}_consideration'] = df.apply(lambda x: run_op(x, col), axis = 1)

    return df

def fmt_inr(value, compact=False):
    fmt_cur = num_fn.NumFmt(currency=True, decimals=2, compact=compact, absolute=False)
    if value == 0:
        return '0'
    else:
        return fmt_cur.fmt(value)

def fmt_val(value, compact=False):
    fmt_num = num_fn.NumFmt(currency=False, decimals=2, compact=compact, absolute=False)
    if value == 0:
        return '0'
    else:
        return fmt_num.fmt(value)

class StopExecution(Exception):
    def _render_traceback_(self):
        pass

class Store:
    def __init__(self):
        self.default_folder_id = '146i1OOUqlLwRt9uxuOJ_IY4MNhzOyHLi'


store = Store()

def format_to_klcr(num):
    abs_num = abs(num)
    if abs_num >= 1e7:  # Crore
        return f"{num / 1e7:.2f} Cr"
    elif abs_num >= 1e5:  # Lakh
        return f"{num / 1e5:.2f} L"
    elif abs_num >= 1e3:  # Thousand
        return f"{num / 1e3:.2f} K"
    else:
        return str(num)


def redcon():
    return pb.get_connection("redpen").connect()

def trinocon():
    return pb.get_connection('[Warehouse] Trino')


def prescon():
    return pb.get_connection("[Warehouse] Presto").connect()


def get_arrow_type_from_type_code(type_code):
    """
    Map the driver's type code to a PyArrow type.
    This function parses types like 'varchar(34)' or 'decimal(24, 6)'.
    """
    type_code = type_code.strip().upper()
    # Extract the base type (e.g. VARCHAR from VARCHAR(34))
    m = re.match(r'([A-Z]+)', type_code)
    if m:
        base_type = m.group(1)
    else:
        base_type = type_code

    mapping = {
        'INTEGER': pa.int64(),
        'BIGINT': pa.int64(),
        'SMALLINT': pa.int16(),
        'FLOAT': pa.float64(),
        'DOUBLE': pa.float64(),
        'NUMERIC': pa.float64(),
        'VARCHAR': pa.string(),
        'CHAR': pa.string(),
        'TEXT': pa.string(),
        'DATE': pa.date32(),
        'TIMESTAMP': pa.timestamp('ms'),
    }
    
    if base_type == 'DECIMAL':
        # Try to extract precision and scale, e.g. DECIMAL(24,6)
        m = re.search(r'DECIMAL\((\d+)\s*,\s*(\d+)\)', type_code)
        if m:
            precision = int(m.group(1))
            scale = int(m.group(2))
            return pa.decimal128(precision, scale)
        else:
            return pa.decimal128(38, 10)
    
    return mapping.get(base_type, pa.string())

def convert_value(value, arrow_type):
    """
    Convert a value to the type defined by arrow_type.
    - For numeric types (integer/float), strip the string and convert.
    - For date columns, parse the date string and return days since epoch.
    - For timestamp columns, parse the string into a datetime object.
    - For decimal columns, convert to a Decimal.
    - For string columns, return as-is.
    """
    if value is None:
        return None

    # For numeric conversion
    if pa.types.is_integer(arrow_type) or pa.types.is_floating(arrow_type):
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        try:
            if pa.types.is_integer(arrow_type):
                # Convert via float to handle cases like "123.0"
                return int(float(value))
            elif pa.types.is_floating(arrow_type):
                return float(value)
        except (ValueError, TypeError) as e:
            print(f"Numeric conversion failed for value '{value}' to {arrow_type}: {e}")
            return None

    # For date columns (pa.date32 expects an int: days since epoch)
    elif pa.types.is_date(arrow_type):
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            try:
                # Try ISO format first, e.g. "2023-03-15"
                dt_obj = datetime.strptime(value, "%Y-%m-%d")
            except Exception:
                try:
                    dt_obj = datetime.strptime(value, "%d/%m/%Y")
                except Exception as e:
                    print(f"Date conversion failed for value '{value}' to {arrow_type}: {e}")
                    return None
            days_since_epoch = (dt_obj.date() - date(1970, 1, 1)).days
            return days_since_epoch
        else:
            if isinstance(value, (datetime, date)):
                return (value - date(1970, 1, 1)).days
            return None

    # For timestamp columns, convert the string to a datetime object.
    elif pa.types.is_timestamp(arrow_type):
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
            # Try multiple formats
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    dt_obj = datetime.strptime(value, fmt)
                    return dt_obj
                except Exception:
                    continue
            print(f"Timestamp conversion failed for value '{value}' to {arrow_type}")
            return None
        elif isinstance(value, datetime):
            return value
        else:
            return None

    # For decimal columns
    elif pa.types.is_decimal(arrow_type):
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        try:
            return Decimal(value)
        except Exception as e:
            print(f"Decimal conversion failed for value '{value}' to {arrow_type}: {e}")
            return None

    # For other types (e.g., strings), return as-is.
    return value

def execute_query_with_retry(cursor, query, retries, wait_sec):
    """
    Execute a query using the given cursor, retrying if an exception occurs.
    """
    attempt = 0
    while attempt <= retries:
        try:
            cursor.execute(query)
            return  # Successful execution.
        except Exception as e:
            print(f"Query execution failed on attempt {attempt+1}/{retries+1}: {e}")
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(wait_sec)


def plsqlx(query, params={}, con=None, retries=0, wait_sec=5, batch_size=10_00_000, debug=False):
    """
    Executes a SQL query and converts the results into a Polars DataFrame,
    leveraging the driver's metadata to enforce a target schema and converting
    values to the correct type.

    Optional parameters: 
      - debug: if True, prints a schema summary in a neat DataFrame.
      
    Also prints start time, end time, and total execution time.
    """
    start_time = dt.now_datetime()
    print(f"Execution started at: {start_time}")
    
    if con is None:
        con = trinocon()  # Replace with your connection function
    raw_conn = con.raw_connection()
    cursor = raw_conn.cursor()
    
    # Replace parameters in the query.
    for key, val in params.items():
        query = query.replace(key, val)
    
    # Use the retry helper for query execution.
    execute_query_with_retry(cursor, query, retries, wait_sec)
    
    description = cursor.description
    
    # Extract driver schema info.
    driver_type_codes = [str(desc[1]) for desc in description]
    column_names       = [desc[0]       for desc in description]

    # Trino uses the type code "BOOLEAN" for bool columns
    arrow_fields = []
    for name, type_code in zip(column_names, driver_type_codes):
        if type_code.upper() == "BOOLEAN":
            arrow_type = pa.bool_()
        else:
            arrow_type = get_arrow_type_from_type_code(type_code)
        arrow_fields.append(pa.field(name, arrow_type))

    target_schema = pa.schema(arrow_fields)
    
    # If debug is true, print a neat schema summary DataFrame.
    if debug:
        arrow_type_codes = [str(target_schema.field(col).type) for col in column_names]
        schema_df = pd.DataFrame([driver_type_codes, arrow_type_codes], 
                                 index=["Driver Type", "Arrow Type"],
                                 columns=column_names)
        print("Schema summary:")
        print(schema_df)
    
    arrow_tables = []
    total_rows = 0
    
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        total_rows += len(rows)
        
        # Transpose rows to get columns efficiently via zip.
        columns = list(zip(*rows))
        data_dict = {}
        for col, vals in zip(column_names, columns):
            # Replace "NaN" with None.
            cleaned_vals = np.where(np.array(vals, dtype=object) == "NaN", None, vals).tolist()
            arrow_type = target_schema.field(col).type
            
            if pa.types.is_boolean(arrow_type):
            # ensure each entry is True/False or None
                converted_vals = [
                    bool(v) if v is not None else None
                    for v in cleaned_vals
                ]
            
            # For numeric, date, timestamp, or decimal types, convert each value.
            elif (pa.types.is_integer(arrow_type) or 
                pa.types.is_floating(arrow_type) or 
                pa.types.is_date(arrow_type) or 
                pa.types.is_timestamp(arrow_type) or 
                pa.types.is_decimal(arrow_type)):
                converted_vals = [convert_value(v, arrow_type) for v in cleaned_vals]
            else:
                converted_vals = cleaned_vals
            data_dict[col] = converted_vals
            
            # Diagnostic: try converting each column individually.
            try:
                pa.array(data_dict[col], type=arrow_type)
            except Exception as e:
                print(f"Error in column '{col}': {e}")
        
        arrow_table_chunk = pa.Table.from_pydict(data_dict, schema=target_schema)
        arrow_tables.append(arrow_table_chunk)
    
    if arrow_tables:
        final_arrow_table = pa.concat_tables(arrow_tables)
    else:
        final_arrow_table = pa.Table.from_pydict({col: [] for col in column_names}, schema=target_schema)
    
    df = pl.from_arrow(final_arrow_table)
    end_time = dt.now_datetime()
    total_time = end_time - start_time
    print(f"Execution ended at: {end_time}")
    print(f"Total execution time: {total_time}")
    print("Total rows processed:", total_rows)
    print("DataFrame shape:", df.shape)
    return df

def plsqlx_arrow_fast(
    query: str,
    params: dict = None,
    con=None,
    retries: int = 0,
    wait_sec: int = 5,
    batch_size: int = 10_00_000,
    debug: bool = False,
) -> pl.DataFrame:
    """
    Pure‐Arrow loader with per‐column kernels:
      - direct pa.array for most types
      - C‐strptime only for dates/timestamps (with strip‐and‐parse)
    """

    start_time = dt.now_datetime()
    print(f"Execution started at: {start_time}")
    # param substitution
    if params:
        for k, v in params.items():
            query = query.replace(k, v)

    # raw cursor
    if con is None:
        con = trinocon()
    cur = con.raw_connection().cursor()

    # execute
    execute_query_with_retry(cur, query, retries, wait_sec)

    # schema build
    names      = [d[0] for d in cur.description]
    type_codes = [str(d[1]).upper() for d in cur.description]
    fields = []
    for n, tc in zip(names, type_codes):
        if tc == "BOOLEAN":
            t = pa.bool_()
        else:
            t = get_arrow_type_from_type_code(tc)
        fields.append(pa.field(n, t))
    schema = pa.schema(fields)

    batches = []
    total_rows = 0

    # fetch batches
    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break
        total_rows += len(rows)

        cols   = list(zip(*rows))
        arrays = []

        for (colname, vals), field in zip(zip(names, cols), schema):
            cleaned = [None if v == "NaN" else v for v in vals]

            # date32
            if pa.types.is_date32(field.type):
                s   = pa.array(cleaned, type=pa.string())
                ts  = pc.strptime(s, format="%Y-%m-%d", unit="s")
                arr = pc.cast(ts, pa.date32())

            # timestamp
            elif pa.types.is_timestamp(field.type):
                unit = field.type.unit
                stripped = [
                    None if v is None else
                    (v.split(".", 1)[0] if isinstance(v, str) else v)
                    for v in cleaned
                ]
                s   = pa.array(stripped, type=pa.string())
                ts  = pc.strptime(s, format="%Y-%m-%d %H:%M:%S", unit=unit)
                arr = pc.cast(ts, field.type)

            # everything else
            else:
                try:
                    arr = pa.array(cleaned, type=field.type, from_pandas=True)
                except pa.lib.ArrowTypeError:
                    raw = pa.array(cleaned, from_pandas=True)
                    arr = pc.cast(raw, field.type)

            arrays.append(arr)

        tbl = pa.Table.from_arrays(arrays, schema=schema)
        batches.append(tbl)

        if debug:
            print(f"  • fetched batch #{len(batches)}: {len(rows)} rows")

    # concat + Polars
    if not batches:
        return pl.DataFrame()
    full = pa.concat_tables(batches, promote=True)
    df   = pl.from_arrow(full)

    # if debug:
    #     print(f"✅ total_rows={total_rows}, batches={len(batches)}, shape={df.shape}")

    end_time = dt.now_datetime()
    total_time = end_time - start_time
    print(f"Execution ended at: {end_time}")
    print(f"Total execution time: {total_time}")
    print(f"✅ total_rows={total_rows}, batches={len(batches)}, shape={df.shape}")
    # print(f"Output Shape: {df.shape}")
    
    
    return df




def plsqlx_arrow_only(
    query: str,
    params: dict = None,
    con=None,
    retries: int = 0,
    wait_sec: int = 5,
    batch_size: int = 10_00_000,
    debug: bool = False,
) -> pl.DataFrame:
    """
    Executes a SQL query via Trino DBAPI and converts results into a Polars DataFrame,
    using PyArrow for all type conversions, with robust Python fallback casts.

    - query: SQL string with optional {{placeholders}} replaced by params.
    - params: dict for simple string replacement in the SQL.
    - con: optional Trino connection (DBAPI); if None, uses trinocon().
    - retries, wait_sec: retry logic for query execution.
    - batch_size: number of rows to fetch per batch.
    - debug: print detailed progress.
    """
    # 1) Record start and substitute parameters
    start_time = dt.now_datetime()
    print(f"Execution started at: {start_time}")
    if params:
        for key, val in params.items():
            query = query.replace(key, val)

    # 2) Open raw DB-API cursor
    if con is None:
        con = trinocon()
    cur = con.raw_connection().cursor()

    # 3) Execute with retry
    execute_query_with_retry(cur, query, retries, wait_sec)

    # 4) Build PyArrow schema from cursor.description
    names = [desc[0] for desc in cur.description]
    codes = [str(desc[1]).upper() for desc in cur.description]
    fields = []
    for name, code in zip(names, codes):
        if code == "BOOLEAN":
            arrow_type = pa.bool_()
        else:
            arrow_type = get_arrow_type_from_type_code(code)
        fields.append(pa.field(name, arrow_type))
    schema = pa.schema(fields)

    # 5) Fetch in batches, convert each batch
    batches = []
    total_rows = 0
    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break
        total_rows += len(rows)
        columns = list(zip(*rows))
        arrays = []

        for (col_name, vals), field in zip(zip(names, columns), schema):
            # replace literal "NaN" with None
            cleaned = [None if v == "NaN" else v for v in vals]

            # A) date32 columns: parse strings to date
            if pa.types.is_date32(field.type):
                s = pa.array(cleaned, type=pa.string())
                ts = pc.strptime(s, format="%Y-%m-%d", unit="s")
                arr = pc.cast(ts, pa.date32())

            # B) timestamp columns: strip fractions & parse
            elif pa.types.is_timestamp(field.type):
                unit = field.type.unit
                stripped = [
                    None if v is None else
                    (v.split('.', 1)[0] if isinstance(v, str) else v)
                    for v in cleaned
                ]
                s = pa.array(stripped, type=pa.string())
                ts = pc.strptime(s, format="%Y-%m-%d %H:%M:%S", unit=unit)
                arr = pc.cast(ts, field.type)

            # C) everything else: try one-shot typed array, fallback to raw+cast
            else:
                try:
                    arr = pa.array(cleaned, type=field.type, from_pandas=True)
                except pa.ArrowTypeError:
                    raw = pa.array(cleaned, from_pandas=True)
                    arr = pc.cast(raw, field.type)

            arrays.append(arr)

        # 6) Assemble batch Table and collect
        batch_tbl = pa.Table.from_arrays(arrays, schema=schema)
        batches.append(batch_tbl)
        if debug:
            print(f"  • batch fetched: {len(rows)} rows")

    # 7) Concatenate or return empty Polars df
    if not batches:
        return pl.DataFrame()
    full_table = pa.concat_tables(batches, promote=True)
    df = pl.from_arrow(full_table)

    # 8) Print timing and return
    end_time = dt.now_datetime()
    print(f"Execution ended at: {end_time}")
    print(f"Total rows: {total_rows}, DataFrame shape: {df.shape}")
    print(f"Total time: {end_time - start_time}")
    return df



def plsqlxy(
    query: str,
    params=None,
    con=None,
    retries: int = 0,
    wait_sec: int = 5,
    batch_size: int = 1_000_000,
    debug: bool = False,
    *,
    output_prefix=None,
    output_format: str = "parquet",
    modifier=None,
):
    """
    Fetch in Arrow‐batches, apply optional `modifier`, then either:
      - Collect into one Polars DF (if output_prefix is None)
      - Write each batch out to file and return list of paths.
    """
    
    start_time = datetime.now()
    print(f"Execution started at: {start_time}")

    # 1) Apply params & get cursor
    if params:
        for k, v in params.items():
            query = query.replace(k, v)
    if con is None:
        con = trinocon()
    cur = con.raw_connection().cursor()
    execute_query_with_retry(cur, query, retries, wait_sec)

    # 2) Build Arrow schema from cursor.description
    names = [d[0] for d in cur.description]
    codes = [str(d[1]).upper() for d in cur.description]
    fields = []
    for n, c in zip(names, codes):
        if c == "BOOLEAN":
            t = pa.bool_()
        else:
            t = get_arrow_type_from_type_code(c)
        fields.append(pa.field(n, t))
    schema = pa.schema(fields)

    # 3) In-memory branch
    if output_prefix is None:
        batches = []
        total = 0
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            total += len(rows)

            # build Arrow columns
            cols = list(zip(*rows))
            arrays = []
            for (_, vals), field in zip(zip(names, cols), schema):
                cleaned = [None if v == "NaN" else v for v in vals]
                if pa.types.is_date32(field.type):
                    s = pa.array(cleaned, type=pa.string())
                    ts = pc.strptime(s, format="%Y-%m-%d", unit="s")
                    arr = pc.cast(ts, pa.date32())
                elif pa.types.is_timestamp(field.type):
                    unit = field.type.unit
                    stripped = [None if v is None else (v.split('.', 1)[0] if isinstance(v, str) else v) for v in cleaned]
                    s = pa.array(stripped, type=pa.string())
                    ts = pc.strptime(s, format="%Y-%m-%d %H:%M:%S", unit=unit)
                    arr = pc.cast(ts, field.type)
                else:
                    try:
                        arr = pa.array(cleaned, type=field.type, from_pandas=True)
                    except pa.ArrowTypeError:
                        raw = pa.array(cleaned, from_pandas=True)
                        arr = pc.cast(raw, field.type)
                arrays.append(arr)

            batch_tbl = pa.Table.from_arrays(arrays, schema=schema)
            dfb = pl.from_arrow(batch_tbl)
            if modifier:
                dfb = modifier(dfb)

            batches.append(dfb)
            if debug:
                print(f"  • batch#{len(batches)}: {len(rows)} rows")

            # clean Python references (no forced GC here)
            del batch_tbl, arrays, cols, rows

        if not batches:
            return pl.DataFrame()

        # concat and free intermediate DataFrames
        df = pl.concat(batches, rechunk=True)
        if debug:
            print(f"Concatenated {len(batches)} batches → {df.shape}")
        # drop batch list to free memory
        del batches
        gc.collect()
        # release any unused Arrow buffers
        pa.default_memory_pool().release_unused()

        end_time = datetime.now()
        total_time = end_time - start_time
        print(f"Execution ended at: {end_time}")
        print(f"Total execution time: {total_time}")
        return df

    # 4) Streaming-to-disk branch
    else:
        paths = []
        batch_i = 0
        total = 0
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            total += len(rows)

            cols = list(zip(*rows))
            arrays = []
            for (_, vals), field in zip(zip(names, cols), schema):
                cleaned = [None if v == "NaN" else v for v in vals]
                if pa.types.is_date32(field.type):
                    s = pa.array(cleaned, type=pa.string())
                    ts = pc.strptime(s, format="%Y-%m-%d", unit="s")
                    arr = pc.cast(ts, pa.date32())
                elif pa.types.is_timestamp(field.type):
                    unit = field.type.unit
                    stripped = [None if v is None else (v.split('.', 1)[0] if isinstance(v, str) else v) for v in cleaned]
                    s = pa.array(stripped, type=pa.string())
                    ts = pc.strptime(s, format="%Y-%m-%d %H:%M:%S", unit=unit)
                    arr = pc.cast(ts, field.type)
                else:
                    try:
                        arr = pa.array(cleaned, type=field.type, from_pandas=True)
                    except pa.ArrowTypeError:
                        raw = pa.array(cleaned, from_pandas=True)
                        arr = pc.cast(raw, field.type)
                arrays.append(arr)

            batch_tbl = pa.Table.from_arrays(arrays, schema=schema)
            dfb = pl.from_arrow(batch_tbl)
            if modifier:
                dfb = modifier(dfb)

            fname = f"{output_prefix}_part{batch_i:03d}.{output_format}"
            if output_format == "parquet":
                dfb.write_parquet(fname)
            elif output_format == "csv":
                dfb.write_csv(fname)
            else:
                raise ValueError(f"Unsupported format: {output_format!r}")
            paths.append(fname)
            if debug:
                print(f"  • wrote batch#{batch_i}: {len(rows)} rows → {fname}")

            # free per-batch references
            del batch_tbl, arrays, cols, rows, dfb
            gc.collect()
            batch_i += 1

        if debug:
            print(f"Done: {total} rows in {batch_i} files")
        # release any unused Arrow buffers
        pa.default_memory_pool().release_unused()
        return paths


def nullify_infinite(arr: pa.Array) -> pa.Array:
    # Only operate on floating columns
    if not pa.types.is_floating(arr.type):
        return arr

    # Build masks using Arrays/Scalars only (no Expressions).
    # Detect NaN:
    nan_mask = pc.is_nan(arr)

    # Detect ±Infinity: |x| > 1e308 (well below 1.79e308 max for float64)
    abs_arr = pc.abs(arr)
    inf_mask = pc.greater(abs_arr, pa.scalar(1e308))  # pa.scalar, not pc.scalar

    mask = pc.or_(nan_mask, inf_mask)

    # Replacement must be a scalar of the same type; use a typed NULL scalar.
    null_scalar = pa.scalar(None, type=arr.type)

    # if_else(cond, left, right): when mask is True, put NULL; else keep value
    return pc.if_else(mask, null_scalar, arr)

def sqlpl(
    query: str,
    params=None,
    con=None,
    retries: int = 0,
    wait_sec: int = 5,
    batch_size: int = 1_000_000,
    debug: bool = False,
    *,
    output_prefix=None,
    output_format: str = "parquet",
    modifier=None,
    parquet_compression: str = "zstd",   # new: zstd is fast & small; set None for uncompressed
    parquet_statistics: bool = True,     # new: helps downstream filters/pruning
):
    """
    Fetch in Arrow‐batches, apply optional `modifier`, then either:
    - Collect into one Polars DF (if output_prefix is None)
    - Write each batch out to file and return list of paths.
    Faster & safer against 'Infinity'/'NaN' issues.
    """
    import gc, pyarrow as pa, pyarrow.compute as pc, polars as pl
    from datetime import datetime

    start_time = datetime.now()
    print(f"Execution started at: {start_time}")

    # ---------- helpers ----------
    INF_STRINGS = {"NaN", "Infinity", "-Infinity", ""}

    def _sanitize_py(vals):
        # vectorized-enough Python clean: map bad string sentinels -> None
        # NOTE: keep non-strings as-is; speeds up mixed-type columns
        return [None if (isinstance(v, str) and v in INF_STRINGS) else v for v in vals]

    def _build_arrow_array(field, vals):
        """
        Build a pyarrow array for one column, fast-pathing by target type.
        We avoid slow string parsing unless required.
        """
        t = field.type

        # sanitize once at the Python level (handles stringified infinities)
        cleaned = _sanitize_py(vals)

        # Dates: your cursor returns strings; parse once -> date32
        if pa.types.is_date32(t):
            # Try to detect if values are already date objects (rare). If strings, parse.
            # Building via string->timestamp->date32 is decently fast.
            s = pa.array(cleaned, type=pa.string())
            ts = pc.strptime(s, format="%Y-%m-%d", unit="s", error_is_null=True)
            return pc.cast(ts, pa.date32())

        # Timestamps: you were splitting off fractional seconds; keep but faster
        if pa.types.is_timestamp(t):
            unit = t.unit  # 's' expected in your schema mapping
            # Reduce Python work: only touch strings
            stripped = [
                (v.split(".", 1)[0] if isinstance(v, str) and v else v)
                for v in cleaned
            ]
            s = pa.array(stripped, type=pa.string())
            ts = pc.strptime(s, format="%Y-%m-%d %H:%M:%S", unit=unit, error_is_null=True)
            return pc.cast(ts, t)

        # Floats/Ints/Decimals: attempt direct build; fall back to cast if needed
        try:
            return pa.array(cleaned, type=t, from_pandas=True)
        except (pa.ArrowTypeError, pa.ArrowInvalid):
            raw = pa.array(cleaned, from_pandas=True)
            return pc.cast(raw, t, safe=False)

    # ---------- prepare query/cursor ----------
    if params:
        for k, v in params.items():
            query = query.replace(k, v)
    if con is None:
        con = trinocon()

    cur = con.raw_connection().cursor()
    # driver hint: larger arraysize can reduce round-trips
    try:
        cur.arraysize = max(1, min(batch_size, 1_000_000))
    except Exception:
        pass

    execute_query_with_retry(cur, query, retries, wait_sec)

    # ---------- Arrow schema ----------
    names = [d[0] for d in cur.description]
    codes = [str(d[1]).upper() for d in cur.description]
    fields = []
    for n, c in zip(names, codes):
        if c == "BOOLEAN":
            t = pa.bool_()
        else:
            t = get_arrow_type_from_type_code(c)
        fields.append(pa.field(n, t))
    schema = pa.schema(fields)

    # ---------- main loop ----------
    gc_was_enabled = gc.isenabled()
    gc.disable()  # fewer pauses during tight loops

    def _fetch_to_polars_batches(write_to_disk: bool):
        paths = []
        batches = []
        batch_i = 0
        total = 0
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            total += len(rows)
            if debug:
                print(f"  • fetched rows: {len(rows)}")

            # column-oriented quickly without copying twice
            # zip(*) is okay, but avoid keeping two large structures alive
            cols = list(zip(*rows)) if rows else [[] for _ in names]

            arrays = []
            for vals, field in zip(cols, schema):
                arr = _build_arrow_array(field, vals)
                # For float columns, replace any residual NaN/Inf with nulls (belt & suspenders)
                if pa.types.is_floating(field.type):
                    arr = nullify_infinite(arr)
                arrays.append(arr)

            batch_tbl = pa.Table.from_arrays(arrays, schema=schema)
            del arrays, cols, rows  # free memory early

            # Convert to Polars, apply modifier
            dfb = pl.from_arrow(batch_tbl)
            if modifier:
                dfb = modifier(dfb)

            if write_to_disk:
                fname = f"{output_prefix}_part{batch_i:03d}.{output_format}"
                if output_format == "parquet":
                    dfb.write_parquet(
                        fname,
                        compression=parquet_compression,
                        statistics=parquet_statistics,
                    )
                elif output_format == "csv":
                    dfb.write_csv(fname)
                else:
                    raise ValueError(f"Unsupported format: {output_format!r}")
                paths.append(fname)
                if debug:
                    print(f"  • wrote batch#{batch_i}: {len(dfb)} rows → {fname}")
                del dfb, batch_tbl
            else:
                batches.append(dfb)
                del batch_tbl

            batch_i += 1

        return batches, paths, total, batch_i

    if output_prefix is None:
        batches, _, total, nbatches = _fetch_to_polars_batches(write_to_disk=False)
        df = pl.concat(batches, how="vertical_relaxed", rechunk=True) if batches else pl.DataFrame()
        del batches
        if debug:
            print(f"Concatenated {nbatches} batches → {df.shape} (rows fetched: {total})")
        result = df
    else:
        _, paths, total, nbatches = _fetch_to_polars_batches(write_to_disk=True)
        if debug:
            print(f"Done: {total} rows in {nbatches} files")
        result = paths

    if gc_was_enabled:
        gc.enable()
    # release any unused Arrow buffers
    pa.default_memory_pool().release_unused()

    end_time = datetime.now()
    print(f"Execution ended at: {end_time}")
    print(f"Total execution time: {end_time - start_time}")
    return result

def ensure_parent_dirs(path: str) -> None:
    """
    Ensure that all parent directories of the given path exist. If they do not exist, create them.

    Parameters:
        path (str): The file or directory path for which to ensure parent directories.
    """
    # Approach 1: Using pathlib
    parent = Path(path).parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    # Approach 2: Using os.path and os.makedirs
    # parent_dir = os.path.dirname(path)
    # if parent_dir and not os.path.exists(parent_dir):
    #     os.makedirs(parent_dir, exist_ok=True)


def find_duplicate_rows(df, columns=None):
    """
    Finds duplicate rows in a DataFrame based on an optional list of columns.

    Parameters:
    - df (pd.DataFrame): The DataFrame to check for duplicates.
    - columns (list, optional): The list of column names to consider for duplicity. If None, all columns are considered.

    Returns:
    - pd.DataFrame: A DataFrame containing the duplicate rows.
    """
    if columns is not None:
        # Keep='first' marks duplicates as True except for the first occurrence.
        duplicate_rows = df[df.duplicated(subset=columns, keep=False)]
    else:
        # If no columns specified, check duplicates across all columns.
        duplicate_rows = df[df.duplicated(keep=False)]
    
    return duplicate_rows


def find_duplicates_pl(df, columns=None):
    if columns is not None:
        duplicates = (
        df.group_by(columns)
        .agg(pl.len().alias("count"))
        .filter(pl.col("count") > 1)
        )
    else:
        duplicates = (
        df.group_by(list(df.columns))
        .agg(pl.len().alias("count"))
        .filter(pl.col("count") > 1)
        )

    return duplicates

# Example usage:
# Assuming you have a DataFrame 'your_dataframe' and a list of columns 'your_columns'
# duplicate_rows = find_duplicate_rows(your_dataframe, your_columns)
# print(duplicate_rows)
def ensure_dict(param):
    """Ensure the parameter is a dictionary.

    Args:
        param: The input parameter to check and possibly convert to a dictionary.

    Returns:
        dict: The original dictionary, a converted dictionary from a string,
              or an empty dictionary if conversion fails or if the input is not a dictionary or string.
    """
    if isinstance(param, dict):
        # The parameter is already a dictionary
        return param
    elif isinstance(param, str):
        # The parameter is a string, attempt to convert it to a dictionary
        try:
            return json.loads(param)
        except json.JSONDecodeError:
            # Return an empty dictionary if conversion fails
            return {}
    else:
        # Return an empty dictionary if the parameter is neither a dictionary nor a string
        return {}


def pbx(string, op_name=None, params={}, channel_id=None) -> str:
    if op_name is None:
        notebook = "paper_run.ipynb"
        output_notebook = "paper_run_out.ipynb"
    else:
        notebook = f"{op_name}.ipynb"
        output_notebook = f"{op_name}_out.ipynb"

    with open(notebook, 'w') as file:
        file.write(string)

    def dicToparam(dic):
        def ml(dic):
            for k, v in dic.items():
                if k.startswith('#raw_'):
                    x = f'''-r {k.replace('#raw_', '')} "{v}"'''
                else:
                    x = f'''-p {k} "{v}"'''
                yield x
        return " ".join(list(ml(dic)))

    params = dicToparam(ensure_dict(params))

    if output_notebook is None:
        command = f'''papermill "{notebook}" "{notebook}" {params}'''
    else:
        command = f'''papermill "{notebook}" "{output_notebook}" {params}'''

    os.system(command.strip())

    if channel_id is not None:
        slack = islack.SlackWrapper()
        msg = f"PFA execution log of {op_name}:"
        slack.send_slack_message(channel_id, msg, file=output_notebook)

    return command


def fn_execute_notebook(notebook, params={}, output_notebook=None, channel_id=None) -> str:
    '''This fn executes a jupyter notebook via command line while optionally
        taking in dictionary style parameters. Make sure notebook is having parameters tag on a cell
        when you want to pass parameters to notebook.
        Parameters which are not to auto inferred for type should start with suffix #raw_
    '''

    def dicToparam(dic):
        def ml(dic):
            for k, v in dic.items():
                if k.startswith('#raw_'):
                    x = f'''-r {k.replace('#raw_', '')} "{v}"'''
                else:
                    x = f'''-p {k} "{v}"'''
                yield x
        return " ".join(list(ml(dic)))

    params = dicToparam(params)


    if output_notebook is None:
        command = f'''papermill "{notebook}" "{notebook}" {params}'''
    else:
        command = f'''papermill "{notebook}" "{output_notebook}" {params}'''

    os.system(command.strip())

    if channel_id is not None:
        slack = islack.SlackWrapper()
        msg = "PFA execution log"
        if output_notebook is None:
            slack.send_slack_message(channel_id, msg)
        else:
            slack.send_slack_message(channel_id, msg, file=output_notebook)

    return command



def hello():
    print("Hello user. Current Package Version is {0.10.8}")


def fn_pl_sql(qkey, q=None, params={}, read_from_csv=False, save=False, con=None):
    if(con is None):
        con = trinocon()
    if(q is None):
        return pl.DataFrame()
    raw_conn = con.raw_connection()
    cursor = raw_conn.cursor()

    if (type(q) == dict and len(q) == 0):
        return pl.DataFrame()

    query = q[qkey]

    for key, val in params.items():
        query = query.replace(key, val)

    fpara = json.dumps(params).replace("{","_").replace("}","").replace(": ", "_").replace("\"","").replace(", ", "_")
    if (fpara == "_"):
        fpara = ""
    fpath = f"qdata/{qkey}{fpara}.csv"
    if(not read_from_csv) or (not os.path.exists(fpath)):
        if not os.path.exists('qdata'):
            if(save):
                os.makedirs('qdata')

        # df = pl.read_database(query=query, connection=con)
                    # df = pl.read_database(query=query, connection=con)
        cursor.execute(query)
        rows = cursor.fetchall()
        # Get column names from cursor description
        column_names = [desc[0] for desc in cursor.description]
        # Build a dictionary for PyArrow Table creation
        # data_dict = {col: [row[i] for row in rows] for i, col in enumerate(column_names)}
        # Create a PyArrow Table
        columns = list(zip(*rows))
            # data_dict = {col: list(vals) for col, vals in zip(column_names, columns)}
        data_dict = {
            col: np.where(np.array(vals, dtype=object) == "NaN", None, vals).tolist()
            for col, vals in zip(column_names, columns)
        }

        arrow_table = pa.Table.from_pydict(data_dict)
        # Convert Arrow Table to Polars DataFrame
        df = pl.from_arrow(arrow_table)

        if(save):
            df.write_csv(fpath)

    #reading from file
    if(read_from_csv):
        df = pl.read_csv(fpath)

    return df


def fn_qsv(qkey, q=None, params={}, read_from_csv=False, save=False, con=None, custom_filename=None):
    if(con is None):
        con = trinocon()
    if(q is None):
        return pd.DataFrame()

    if (type(q) == dict and len(q) == 0):
        return pd.DataFrame()

    query = q[qkey]

    for key, val in params.items():
        query = query.replace(key, val)

    if(custom_filename is None):
        fpara = json.dumps(params).replace("{","_").replace("}","").replace(": ", "_").replace("\"","").replace(", ", "_")
    else:
        fpara = custom_filename
        
    if (fpara == "_"):
        fpara = ""
    fpath = f"qdata/{qkey}{fpara}.csv"
    if(not read_from_csv) or (not os.path.exists(fpath)):
        if not os.path.exists('qdata'):
            if(save):
                os.makedirs('qdata')
        df = pd.read_sql(sql=query, con=con)
        if(save):
            df.to_csv(fpath, index = False)

    #reading from file
    if(read_from_csv):
        df = pd.read_csv(fpath, index_col=False, low_memory=False)

    return df


def fn_qr(qkey, q=None, params={}, read_from_csv=False, save=False, con=None, retries=3, wait_sec=5):
    for attempt in range(retries+1):
        print(f"Read attempt: {attempt}... \nRun started at {dt.now()}")
        try:
            start = time.time()
            df = fn_qsv(qkey, q=q, params=params, save=save, read_from_csv=read_from_csv, con=con)
            end = time.time()
            if (end - start) > 60:
                print("Time: ", (end - start) / 60, "min")
            else:
                print("Time: ", end - start, "s")
            return df
            break
        except BaseException as e:
            print(e)
            time.sleep(wait_sec)


def sqlx(query, params={}, con=None, retries=0, wait_sec=5):
    for attempt in range(retries+1):
        print(f"Read attempt: {attempt}... \nRun started at {dt.now()}")
        try:
            start = time.time()
            if(con is None):
                con = trinocon()
            for key, val in params.items():
                query = query.replace(key, val)

            df = pd.read_sql(sql=query, con=con)
            end = time.time()
            if (end - start) > 60:
                print("Time: ", (end - start) / 60, "min")
            else:
                print("Time: ", end - start, "s")
            print(df.shape)
            return df
            break
        except BaseException as e:
            print(e)
            time.sleep(wait_sec)


def fn_sql(sqlpath, params={}, read_from_csv=True, save=True, con=None):
    if(con is None):
        con = redcon()

    if not os.path.exists(sqlpath):
        raise Exception("sql path does not exist")
    
    with open(sqlpath, 'r') as f:
        query = f.read()

    for key, val in params.items():
        query = query.replace(key, val)

    fpara = json.dumps(params).replace("{","_").replace("}","").replace(": ", "_").replace("\"","").replace(", ", "_")
    if (fpara == "_"):
        fpara = ""
    fpath = f"qdata/{os.path.basename(sqlpath).split('.', 1)[0]}{fpara}.csv"
    if(not read_from_csv) or (not os.path.exists(fpath)):
        if not os.path.exists('qdata'):
            if(save):
                os.makedirs('qdata')
        df = pd.read_sql(sql=query, con=con)
        if(save):
            df.to_csv(fpath, index = False)

    #reading from file
    if(read_from_csv):
        df = pd.read_csv(fpath, index_col=False, low_memory=False)

    return df


def remove_outlier(df_in, col_name):
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3-q1 #Interquartile range
    fence_low  = q1-1.5*iqr
    fence_high = q3+1.5*iqr
    df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    return df_out


def remove_outliers(df_in, col_name_list, iqr_multiple=1.5):
    for col_name in col_name_list:
        q1 = df_in[col_name].quantile(0.25)
        q3 = df_in[col_name].quantile(0.75)
        iqr = q3-q1 #Interquartile range
        fence_low  = q1-iqr_multiple*iqr
        fence_high = q3+iqr_multiple*iqr
        df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    return df_out


def get_ntile_rnk_output(df_in, col_name, cuts=100, cname='Ntile'):
    df_out = df_in.copy()
    df_out[cname] = pd.qcut(df_out[col_name].rank(method='first'), cuts, labels = range(1, cuts + 1))
    df_out[cname] = df_out[cname].astype(float)
    conditions = [
                (df_out[cname] >=0) & (df_out[cname] <= 6),
              (df_out[cname] >=7) & (df_out[cname] <= 14),
              (df_out[cname] >=15) & (df_out[cname] <= 23),
              (df_out[cname] >=24) & (df_out[cname] <= 36),
              (df_out[cname] >=37) & (df_out[cname] <= 55),
              (df_out[cname] >=56) & (df_out[cname] <= 75),
              (df_out[cname] >=76) & (df_out[cname] <= 86),
              (df_out[cname] >=87) & (df_out[cname] <= 94),
                (df_out[cname] >=95) & (df_out[cname] <= 100)
             ]
    choices = [0,1,2,3,4,5,6,7,8]
    df_out['rnk'] = np.select(conditions, choices)
    return df_out


def get_ntile_output(df_in, col_name, cuts=100, cname='Ntile'):
    df_out = df_in.copy()
    df_out[cname] = pd.qcut(df_out[col_name].rank(method='first'), cuts, labels = range(1, cuts + 1))
    df_out[cname] = df_out[cname].astype(float)
    return df_out


def make_flat_index(df_in):
    df_in.columns = ["_".join(map(str, a)).rstrip('_') for a in df_in.columns.to_flat_index()]
    return df_in

def pareto_test(df_in, col_name):
    df = get_ntile_output(df_in, col_name)
    gdf = pd.pivot_table(df, values = [col_name], index =['Ntile'],
                         columns =[], aggfunc = {col_name: [np.sum, 'count']}).reset_index()
    gdf.columns = ["_".join(a) for a in gdf.columns.to_flat_index()]
    gdf.rename({'Ntile_': 'Ntile'}, axis=1, inplace=True)
    col_name_sum = f"{col_name}_sum"
    col_name_count = f"{col_name}_count"
    
    gdf['top_x_perc'] = 100 - gdf['Ntile'] + 1
    gdf['contribution_perc'] = round((gdf[col_name_sum]/gdf[col_name_sum].sum())*100,1)
    gdf[col_name_sum] = gdf[col_name_sum].round(2)
    gdf['upto_contribution_perc'] = gdf.apply(lambda x: gdf[gdf['Ntile']>=x['Ntile']]['contribution_perc'].sum(),axis=1)
    gdf[f"upto_{col_name_sum}"] = gdf.apply(lambda x: gdf[gdf['Ntile']>=x['Ntile']][col_name_sum].sum(),axis=1)
    gdf[f"upto_{col_name_count}"] = gdf.apply(lambda x: gdf[gdf['Ntile']>=x['Ntile']][col_name_count].sum(),axis=1)
    
    cols = ['top_x_perc', 'upto_contribution_perc', f"upto_{col_name_sum}", f"upto_{col_name_count}", 'contribution_perc', col_name_sum, col_name_count, 'Ntile']
    gdf = gdf[cols]
    return gdf.sort_values('top_x_perc')

def describe_basis(df_in, col_name, col_seq):
    df_result = pd.DataFrame()
    if(col_name not in col_seq):
            col_seq.append(col_name)
    for val in sorted(list(df_in[col_name].unique())):
        df_work = df_in[col_seq]
        df2 = df_work[df_work[col_name]==val]
#         df2 = remove_outliers(df2, col_seq)
        df_out = df2.describe()
#         df_out['index1'] = df_out.index
        df_out.reset_index(level=0, inplace=True)
        df_out[col_name] = val
        df_out.sort_values(by=col_name, inplace = True)
        cols = df_out.columns
        df_out[cols[1:]] = df_out[cols[1:]].apply(pd.to_numeric, errors='coerce')
#         df_out = df_out.astype('float64')
        df_result = df_result.append(df_out, ignore_index=True)
    return df_result.pivot_table(index=col_name, columns=["index"], values=df_result.columns.difference(["index", col_name]))

def df_to_zip(df_dic, zipname="data", zipfolder="data", output_type='csv', clean_up = False, use_pl=False):
    if os.path.exists(zipfolder):
        shutil.rmtree(zipfolder)
    os.makedirs(zipfolder, exist_ok=True)
    for fname, df in df_dic.items():
        if(output_type == 'csv'):
            filename = f"{zipfolder}/{fname}.csv"
            if use_pl:
                df.write_csv(filename)
            else:
                df.to_csv(filename, index=False)
        else:
            filename = f"{zipfolder}/{fname}.xlsx"
            if use_pl:
                df.to_pandas().to_excel(filename, index=False)
            else:
                df.to_excel(filename, index=False)
    zipname = f"{zipname}"
    shutil.make_archive(zipname, "zip", zipfolder)
    if clean_up:
        shutil.rmtree(zipfolder)
    return f"{zipname}.zip"

def df2zip(df_dic, zipname="data", zipfolder="data", clean_up=False, use_pl=False):
    return df_to_zip(df_dic, zipname = zipname, zipfolder = zipfolder, clean_up=clean_up, use_pl=use_pl)


def fn_read_zip(zip_file_path, use_pl=False):
    # Unpack the ZIP archive
    extract_dir = 'extracted'
    shutil.unpack_archive(zip_file_path, extract_dir=extract_dir)
    
    # List files in the extracted directory
    extracted_files = os.listdir(extract_dir)
    
    if not extracted_files:
        raise Exception("No files found in the ZIP archive")
    
    # Create a dictionary to store DataFrames
    dataframes = {}
    
    for file_name in extracted_files:
        file_path = os.path.join(extract_dir, file_name)
        
        # Attempt to read only CSV files
        if file_name.endswith('.csv'):
            try:
                # Read each CSV file into a DataFrame
                if use_pl:
                    df = pl.read_csv(file_path)
                else:
                    df = pd.read_csv(file_path)
                # Use the file name (without extension) as the key
                key = os.path.splitext(file_name)[0]
                dataframes[key] = df
            except Exception as e:
                print(f"Error reading {file_name}: {e}")
    
    # Clean up the temporary files
    # os.remove(zip_file_path)
    shutil.rmtree(extract_dir)
    
    # Check if any DataFrames were created
    if not dataframes:
        raise Exception("No valid CSV files found in the ZIP archive")
    
    return dataframes


def fn_read_url_zipped(url, use_pl=False):
    # Download the file from the URL
    response = requests.get(url)
    
    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        raise Exception(f"Failed to download the file. Status code: {response.status_code}")
    
    # Save the content to a temporary ZIP file
    zip_file_path = 'temp.zip'
    with open(zip_file_path, 'wb') as f:
        f.write(response.content)
    
    # Unpack the ZIP file using shutil
    shutil.unpack_archive(zip_file_path, extract_dir='extracted')
    
    # List files in the extracted directory
    extracted_files = os.listdir('extracted')
    
    if not extracted_files:
        raise Exception("No files found in the ZIP archive")
    
    # Assuming the first file is the CSV file
    csv_file_path = os.path.join('extracted', extracted_files[0])
    
    # Read the CSV file into a pandas DataFrame
    if use_pl:
        df = pl.read_csv(csv_file_path)
    else:
        df = pd.read_csv(csv_file_path)
    
    # Clean up the temporary files
    os.remove(zip_file_path)
    shutil.rmtree('extracted')
    
    return df

def delete(filepath, path_type='file'):
    # Deleting the file
    if(path_type == 'file'):
        if os.path.exists(filepath):
            os.remove(filepath)
            print("File deleted successfully")
        else:
            print("The file does not exist")
    else:
        if os.path.exists(filepath):
            shutil.rmtree(filepath)


def df_to_excel_zip(df_dic, zipname="data", zipfolder="data", clean_up=False, use_pl=False):
    return df_to_zip(df_dic, zipname = zipname, zipfolder = zipfolder, output_type='excel', clean_up=clean_up, use_pl=use_pl)


class MyKmeanWay:
#     Within-Cluster-Sum-of-Squares
    def __init__(self, data, mparas=None, no_of_clusters=3):
        self.data = data
        self.mparas = mparas
        self.no_of_clusters = no_of_clusters
        if(mparas==None):
            self.selected_data = data
        else:
            self.selected_data = data[mparas]
    
    def get_kmeans_data(self, no_of_clusters: int=None):
        if(no_of_clusters==None):
            no_of_clusters=self.no_of_clusters
        self.kmeans = KMeans(no_of_clusters)
        identified_clusters = self.kmeans.fit_predict(self.selected_data)
        data_with_clusters = self.data.copy()
        data_with_clusters['Clusters'] = identified_clusters 
        return data_with_clusters
        
    def set_no_of_clusters(self, no_of_clusters):
        self.no_of_clusters = no_of_clusters
        
    def show_elbow(self):
        wcss=[]
        for i in range(1,10):
            kmeans = KMeans(i)
            kmeans.fit(self.selected_data.apply(zscore))
            wcss_iter = kmeans.inertia_
            wcss.append(wcss_iter)
        number_clusters = range(1,10)
        ax = sns.lineplot(x=number_clusters, y=wcss)
        ax.set_title('The Elbow title')
        ax.set_xlabel('Number of clusters')
        ax.set_ylabel('WCSS')
        plt.show()


class RfmWay:
    def __init__(self, df_in, rfm_cols, rfm_cuts, adjustment=0, adjustment_cols=None):
        self.df_in = df_in
        self.rfm_cols = rfm_cols
        self.rfm_cuts = rfm_cuts
        self.df_result = df_in
        self.rnks = []
        for col, cuts in zip(rfm_cols, rfm_cuts):
#             print(f"cuts: {cuts}")
            self.rnks.append(f'rnk_{col}')
            self.df_result = self.__get_ntile_output(self.df_result, col, cname=f'rnk_{col}', cuts = cuts)
            self.df_result['rnk'] = self.df_result[self.rnks].sum(axis=1) - adjustment
            if(adjustment_cols is not None):
                self.df_result['rnk'] = self.df_result['rnk'] - self.df_result[adjustment_cols].sum(axis=1)
#                 self.df_result['rnk'] = np.where(self.df_result['rnk']<0,0,self.df_result['rnk'])
            self.df_result['rnk'] = np.where(self.df_result['rnk']<0,0,self.df_result['rnk'])
    
    def set_new_adjustment(adjustment, adjustment_cols=None):
        self.df_result['rnk'] = self.df_result[self.rnks].sum(axis=1) - adjustment
        if(adjustment_cols is not None):
            self.df_result['rnk'] = self.df_result['rnk'] - self.df_result[adjustment_cols].sum(axis=1)
            self.df_result['rnk'] = np.where(self.df_result['rnk']<0,0,self.df_result['rnk'])
            
        
    def describe(self, col_seq):
        return self.__describe_basis(self.df_result, "rnk", col_seq)
    
#     def set_df_result(self, df_in):
#         self.df_result = df_in.copy()
    
    @staticmethod
    def __describe_basis(df_in, col_name, col_seq):
        df_result = pd.DataFrame()
        if(col_name not in col_seq):
            col_seq.append(col_name)
        for val in sorted(list(df_in[col_name].unique())):
            df_work = df_in[col_seq]
            df2 = df_work[df_work[col_name]==val]
    #         df2 = remove_outliers(df2, col_seq)
            df_out = df2.describe()
    #         df_out['index1'] = df_out.index
            df_out.reset_index(level=0, inplace=True)
            df_out[col_name] = val
            df_out.sort_values(by=col_name, inplace = True)
            cols = df_out.columns
            df_out[cols[1:]] = df_out[cols[1:]].apply(pd.to_numeric, errors='coerce')
    #         df_out = df_out.astype('float64')
            df_result = df_result.append(df_out, ignore_index=True)
        return df_result.pivot_table(index=col_name, columns=["index"], values=df_result.columns.difference(["index", col_name]))
   
    @staticmethod
    def __get_ntile_output(df_in, col_name, cuts=100, cname='Ntile'):
        df_out = df_in.copy()
        df_out[cname] = pd.qcut(df_out[col_name].rank(method='first'), cuts, labels = range(1, cuts + 1))
        df_out[cname] = df_out[cname].astype(float)
        return df_out
    
    @staticmethod
    def __remove_outliers(df_in, col_name_list, iqr_multiple=1.5):
        for col_name in col_name_list:
            q1 = df_in[col_name].quantile(0.25)
            q3 = df_in[col_name].quantile(0.75)
            iqr = q3-q1 #Interquartile range
            fence_low  = q1-iqr_multiple*iqr
            fence_high = q3+iqr_multiple*iqr
            df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
        return df_out
    
    def rnk_plot(self, axes=None):
        sns.histplot(ax=axes, data=self.df_result, x=self.df_result['rnk'])
        
    def rnk_share_plot(self, axes=None):
        sns.histplot(ax=axes, data=self.df_result, x=self.df_result['rnk'])
        
    
    def line_plot(self, col_seq, col_name="rnk", fig_size=(20,10), title=None):
        
        wdf = self.describe(col_seq)
        if(col_name in col_seq):
            col_seq.remove(col_name)
        
        no_of_fig_cols = 4
        ln = len(col_seq)
        fig, axes = plt.subplots(int(ln/no_of_fig_cols)+1, min(ln,no_of_fig_cols), figsize=fig_size)

#         print(col_seq)
        for index, col in enumerate(col_seq):
            ax0 = int(index/no_of_fig_cols)
            ay0 = index - int(index/no_of_fig_cols)*no_of_fig_cols
            tdf = wdf.loc[:,col]
            tdf = tdf[tdf.columns.difference(["count", "max", "25%", "75%", "min"])]
#             fdf.reset_index(level=0, inplace=True)
            fdf = tdf.stack().reset_index().rename(columns={0: "values"})
            if(int(ln/no_of_fig_cols+1)<=1):
                sns.lineplot(ax=axes[index], x=fdf[col_name], hue="Index", data=fdf).set_title(col)
            else:
                sns.lineplot(ax=axes[ax0, ay0], data=fdf, x=col_name, y="values", hue="index").set_title(col)
#                 sns.boxplot(ax=axes[ax0, ay0], x=fdf[col_name], hue="Index", data=fdf).set_title(col)

        fig.tight_layout()
        if(title is not None):
            fig.suptitle(title, size=16)
            fig.subplots_adjust(top=0.88)

        plt.show()

    @staticmethod
    def __show_values_on_bars(axs):
        def _show_on_single_plot(ax):        
            for p in ax.patches:
                _x = p.get_x() + p.get_width() / 2
                _y = p.get_y() + p.get_height()
                value = '{:.2f}'.format(p.get_height())
                ax.text(_x, _y, value, ha="center", va='top',rotation=90) 

        if isinstance(axs, np.ndarray):
            for idx, ax in np.ndenumerate(axs):
                _show_on_single_plot(ax)
        else:
            _show_on_single_plot(axs)

    def count_plot(self, title="Absolute", fig_size = (5,5)):
        wdf = self.describe(self.rfm_cols)

        tdf = wdf.loc[:,self.rfm_cols[0]]
        tdf = tdf.stack().reset_index().rename(columns={0: "values"})
        tdf = tdf[tdf["index"]=="count"]

        fig, axes = plt.subplots(1,1, figsize=fig_size)
        sns.barplot(x = 'rnk',
            y = 'values',
            data = tdf)
#         plt.xticks(rotation=70)
        plt.tight_layout()
        self.__show_values_on_bars(axes)
        if(title is not None):
            fig.suptitle(title, size=16)
            fig.subplots_adjust(top=0.88) 
        plt.show()

    def count_plot_perc(self, title="%Age", fig_size = (5,5)):
        wdf = self.describe(self.rfm_cols)
        tdf = wdf.loc[:,self.rfm_cols[0]]
        tdf["count%"] = (tdf["count"]/tdf["count"].sum())*100
        tdf = tdf.stack().reset_index().rename(columns={0: "values"})
        tdf = tdf[tdf["index"]=="count%"]
        fig, axes = plt.subplots(1,1, figsize=fig_size)
        sns.barplot(x = 'rnk',
            y = 'values',
            data = tdf)
#         plt.xticks(rotation=70)
        plt.tight_layout()
        self.__show_values_on_bars(axes) 
        if(title is not None):
            fig.suptitle(title, size=16)
            fig.subplots_adjust(top=0.88)
        plt.show()

    def box_plot(self, col_seq=None, col_name="rnk", fig_size=(10,5)):
        if(col_name not in col_seq):
            col_seq.append(col_name)

        if(col_seq is None):
            col_seq = self.df_result.columns

        ndf = self.df_result[col_seq]
#         ndf = pd.DataFrame()
#         for val in sorted(list(wdf[col_name].unique())):
#             df2 = wdf[wdf[col_name]==val]
#             df2 = self.__remove_outliers(df2, col_seq, iqr_multiple=1.5)
#             ndf = ndf.append(df2, ignore_index=True)

#         print(list(ndf.columns))
#         ndf[col_name] = ndf[col_name].astype('category')
        no_of_fig_cols = 4
        ln = len(col_seq) - 1
        fig_size_x = 4
        fig_size_y = 2 #(ln/no_of_fig_cols+1)*5
        fig, axes = plt.subplots(int(ln/no_of_fig_cols)+1, min(ln,no_of_fig_cols), figsize=fig_size)
        ls = [item for item in col_seq if item not in [col_name]]
        for index, col in enumerate(ls):
            ax0 = int(index/no_of_fig_cols)
            ay0 = index - int(index/no_of_fig_cols)*no_of_fig_cols
            max(0,(index - no_of_fig_cols*(ln/no_of_fig_cols)))
#             print(f"{ax0},{ay0}")
            if(int(ln/no_of_fig_cols+1)<=1):
                sns.boxplot(ax=axes[index], data=ndf, x=col_name, y=col, showfliers = False).set_title(col)
            else:
                sns.boxplot(ax=axes[ax0, ay0], data=ndf, x=col_name, y=col, showfliers = False).set_title(col)
        fig.tight_layout()
        plt.show()


fn_q = partial(fn_qsv, read_from_csv = False)
fn_q_nosave = partial(fn_qsv, read_from_csv = False, save=False)


def zip_file(filename, folder):
    from zipfile import ZipFile, ZipInfo
    # zif = ZipInfo.from_file(filename=filename)
    # print(type(zif))
    with ZipFile(f"{filename}.zip",'w') as zip:
        zip.write(f"{folder}/{filename}")
        # zip.write(os.path.join(os.getcwd(), filename))

def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    return ax

def bring_columns_to_front(columns: list, data: pd.DataFrame=None) -> pd.DataFrame:
    '''Brings the provided column list to front of the df in the specified order'''
    if data is None:
        print("data parameter is mandatory")
        return None
    df = data[columns + [col for col in data.columns if col not in columns]]
    return df

def fn_delta_df(df1, df2):
    df_delta = pd.merge(df1, df2, how='outer', indicator='Exist')
    df_delta = df_delta.loc[df_delta['Exist'] != 'both']
    return df_delta


class PdTable:
    dtypelist = []
    def __init__(self, in_df, table_name,
                 primary_key: list=None,
                 sort_key: list=None,
                 table_description="Table",
                 col_order=None,
                 front_cols=None,
                 load_type="upsert", 
                 schema="consumer",
                 add_create_timestamp=True
                 ):
        df = in_df.copy()
        df.columns = [x.lower() for x in df.columns]
        df.columns = df.columns.str.replace(' ','_')
        df.columns = df.columns.str.replace('.','_')
        df.columns = df.columns.str.replace('/','_')
        df.columns = df.columns.str.replace('(','')
        df.columns = df.columns.str.replace(')','')
        df.columns = df.columns.str.replace('%','perc')
        df.columns = df.columns.str.replace('&','n')
        df.columns = df.columns.str.replace('*','x')
        if add_create_timestamp:
            df["record_created_at_ist"] = date_fn.Cdt().now()
            df["record_created_at_ist"] = pd.to_datetime(df["record_created_at_ist"])
        if front_cols is not None:
            df = df[ front_cols + [ col for col in df.columns if col not in front_cols]]
        if col_order is not None:
            df = df[col_order]
        self.df = df
        self.table_description = table_description
        self.load_type = load_type
        self.table_name = table_name
        self.schema = schema
        self.primary_key = primary_key
        self.sort_key = sort_key
        # df_pnl.set_index(["outlet_id"]).index.is_unique
        
    def upload(self):
        kwargs = self.kwargs()
        # print(kwargs)
        pb.to_redshift(self.df, **kwargs)
        
    def set_column_dtype(self, name, type, description):
        self.dtypelist.append({"name": name, 
                   "type": type,
                   "description": description})


    def column_dtypes(self):
        dtypes = []
        for col in self.df.columns.tolist():
            dic = {"name": col, 
                   "type": self.__get_type(col),
                   "description": col}
            for dtp in self.dtypelist:
                if dtp['name'] == col:
                    dic = dtp
            dtypes.append(dic)
        return dtypes
    
    def kwargs(self):
        kwargs = {
        "schema_name": self.schema,
        "table_name": self.table_name,
        "column_dtypes": self.column_dtypes(),
        "primary_key": self.primary_key,
        "sortkey": self.sort_key,
        "force_upsert_without_increment_check": True,
        "load_type": self.load_type,
        "table_description":self.table_description
        }
        return kwargs

    def __get_type(self, col):
        typea = self.df[col].dtype
        if typea == "float64":
            return "float"
        elif typea == "int64":
            return "bigint"
        elif typea == "datetime64[ns]":
            return "datetime"
        else:
            return "character varying(500)"


class AdvDF:
    def __init__(self, df, index_cols=None):
        self.df = df
        self.index_cols = index_cols
        # df_pnl.set_index(["outlet_id"]).index.is_unique

    def numeric_cols(self):
        dtypes = []
        for col in self.df.columns.tolist():
            if self.__is_value(col):
                dtypes.append(col)
        return dtypes

    def non_numeric_cols(self):
        dtypes = []
        for col in self.df.columns.tolist():
            if not self.__is_value(col):
                dtypes.append(col)
        return dtypes

    def value_cols(self):
        if self.index_cols is not None:
            return [a for a in self.numeric_cols() if a not in self.index_cols]
        return self.numeric_cols()

    def suggested_index_cols(self):
        first_list = self.non_numeric_cols()
        second_list = []
        if self.index_cols is not None:
            second_list = self.index_cols
        return first_list + list(set(second_list) - set(first_list))

    def pivot(self, drop_cols=None):
        value_cols = self.value_cols()
        index_cols = self.suggested_index_cols()
        if drop_cols is not None:
            value_cols = [a for a in value_cols if a not in drop_cols]
            index_cols = [a for a in index_cols if a not in drop_cols]
        pvt = pd.pivot_table(
            self.df.fillna(0),
            values=value_cols,
            index=index_cols,
            columns=None,
            aggfunc = 'sum',
            fill_value=None,
            margins=False,
            dropna=True,
            margins_name='All',
            observed=False,
            sort=True,
        ).reset_index()
        return pvt

    def __is_value(self, col):
        typea = self.df[col].dtype
        if typea == "float64":
            return True
        elif typea == "int64":
            return True
        elif typea == "datetime64[ns]":
            return False
        else:
            return False

def merge_images_vertical(file1, file2, output_file):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """
    from PIL import Image
    image1 = Image.open(file1)
    image2 = Image.open(file2)

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    # result_width = width1 + width2
    # result_height = max(height1, height2)
    result_width = max(width1, width2)
    result_height = height1 + height2

    result = Image.new('RGB', (result_width, result_height), color=(255, 255, 255, 0))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(0, height1))
    result.save(output_file)
    return result

def merge_images_horizontal(file1, file2, output_file):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """
    from PIL import Image
    image1 = Image.open(file1)
    image2 = Image.open(file2)

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    result_width = width1 + width2
    result_height = max(height1, height2)
    # result_width = max(width1, width2)
    # result_height = height1 + height2

    result = Image.new('RGB', (result_width, result_height), color=(255, 255, 255, 0))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(width1, 0))
    result.save(output_file)
    return result

def upload2s3(filename: str, cloud_folder_path=f"pencilbox/wastage_bucket", expiry_in_seconds=3600*24*2):
    import boto3
    from botocore.exceptions import ClientError
    bucket_name = "grofers-prod-dse-sgp"
    def create_presigned_url(filename, object_name, expiration=expiry_in_seconds):
        # Generate a presigned URL for the S3 object
        try:
            s3_client = boto3.client('s3', **pb.get_secret("dse/iam_users/application-pencilbox-s3-access"))
            print("using pencilbox-s3-access")
        except Exception as e:
            print("using default secret")
            s3_client = boto3.client('s3')

        try:
            response = s3_client.generate_presigned_url('get_object',Params={'Bucket': bucket_name,'Key': object_name},ExpiresIn=expiration)
        except ClientError as e:
            return None
        # The response contains the presigned URL
        return response
    cloud_filepath = f"{cloud_folder_path}/{filename}"
    pb.to_s3(f"{filename}", bucket_name, cloud_filepath)
    File_Path_Link = create_presigned_url(bucket_name, object_name=cloud_filepath, expiration=expiry_in_seconds)
    return File_Path_Link




# def fn_read_zip(zip_file_path):
#     # Unpack the ZIP archive
#     extract_dir = 'extracted'
#     shutil.unpack_archive(zip_file_path, extract_dir=extract_dir)
    
#     # List files in the extracted directory
#     extracted_files = os.listdir(extract_dir)
    
#     if not extracted_files:
#         raise Exception("No files found in the ZIP archive")
    
#     # Create a dictionary to store DataFrames
#     dataframes = {}
    
#     for file_name in extracted_files:
#         file_path = os.path.join(extract_dir, file_name)
        
#         # Attempt to read only CSV files
#         if file_name.endswith('.csv'):
#             try:
#                 # Read each CSV file into a DataFrame
#                 df = pd.read_csv(file_path)
#                 # Use the file name (without extension) as the key
#                 key = os.path.splitext(file_name)[0]
#                 dataframes[key] = df
#             except Exception as e:
#                 print(f"Error reading {file_name}: {e}")
    
#     # Clean up the temporary files
#     # os.remove(zip_file_path)
#     shutil.rmtree(extract_dir)
    
#     # Check if any DataFrames were created
#     if not dataframes:
#         raise Exception("No valid CSV files found in the ZIP archive")
    
#     return dataframes


class Workflow:
    def __init__(self):
        self.workflow = [
        (self.__sample_function, [1, 2], {"c": 3}),  # first_task
        (self.__sample_function, [4, 5], {"c": 6}),  # second_task
        [
            (self.__sample_function, [7, 8], {"c": 9}),  # third_task
            (self.__sample_function, [10, 11], {"c": 12}) # fourth_task
        ]
        ]
       

    def __execute_function(self, func, *args, **kwargs):
        func(*args, **kwargs)

#     def __execute_in_parallel(self, functions):
#         processes = []
#         for func, args, kwargs in functions:
#             process = Process(target=self.__execute_function, args=(func, *args), kwargs=kwargs)
#             processes.append(process)
#             process.start()

#         for process in processes:
#             process.join()

    def __execute_in_parallel(self, functions):
        processes = []
        for item in functions:
            func = item[0]  # The function to execute
            if len(item) == 2 and not isinstance(item[1], (list, dict)):
                # If there is one argument and it's not a list or dict, treat it as a single argument
                args = [item[1]]
            elif len(item) > 1:
                args = item[1]  # A list of arguments
            else:
                args = []

            kwargs = item[2] if len(item) > 2 else {}  # Default to empty dict if kwargs are not provided

            process = Process(target=self.__execute_function, args=(func, *args), kwargs=kwargs)
            processes.append(process)
            process.start()

        for process in processes:
            process.join()


    def execute(self, workflow=None):
        if workflow is None:
            workflow = self.workflow
        for task in workflow:
            if isinstance(task, list):
                # Parallel execution
                self.__execute_in_parallel(task)
            elif callable(task):
                # Function with no arguments
                self.__execute_function(task)
            elif isinstance(task, tuple) and len(task) == 2:
                func, second_element = task
                if isinstance(second_element, dict):
                    # Function with only keyword arguments
                    self.__execute_function(func, **second_element)
                elif isinstance(second_element, list):
                    # Function with only positional arguments (list)
                    self.___execute_function(func, *second_element)
                else:
                    # Function with a single positional argument
                    self.__execute_function(func, second_element)
            else:
                # Function with both positional and keyword arguments
                func, args, kwargs = task
                self.__execute_function(func, *args, **kwargs)

    # Example usage
    @staticmethod
    def __sample_function(a, b, c=0):
        print(f"Function called with a={a}, b={b}, c={c}")


# import os
# import requests
# import pyarrow as pa
# import polars as pl
# from urllib.parse import urljoin, urlparse

# def plsqlx_json(
#     query: str,
#     params = None,
#     conn_dict = None,
#     verify_tls: bool = True,
#     debug: bool = False,
# ) -> pl.DataFrame:
#     # 1) Inline your {{…}} params
#     if params:
#         for k, v in params.items():
#             query = query.replace(k, v)

#     # 2) Load Vault secrets if needed
#     if conn_dict is None:
#         conn_dict = pb.connections.get_conn_dict(
#             "[Warehouse] Trino",
#         )

#     host     = conn_dict["host"]
#     port     = int(conn_dict["port"])
#     svc_user = conn_dict.get("user") or conn_dict.get("username")
#     svc_pass = conn_dict["password"]

#     # 2a) figure out catalog/schema
#     if "catalog" in conn_dict and "schema" in conn_dict:
#         catalog, schema = conn_dict["catalog"], conn_dict["schema"]
#     else:
#         p       = urlparse(conn_dict["uri"])
#         parts   = p.path.lstrip("/").split("/", 1)
#         catalog = parts[0]
#         schema  = parts[1] if len(parts) > 1 else None

#     # 2b) figure out the impersonated user
#     if "JUPYTERHUB_USER" in os.environ:
#         real_user = os.environ["JUPYTERHUB_USER"]
#         source    = "jhub"
#     else:
#         real_user = svc_user
#         source    = "common_airflow"

#     if debug:
#         print(f"catalog={catalog!r}, schema={schema!r}, user={real_user!r}, source={source!r}")

#     # 3) build HTTP session with BasicAuth for the service account
#     sess       = requests.Session()
#     sess.auth  = requests.auth.HTTPBasicAuth(svc_user, svc_pass)
#     sess.verify = verify_tls

#     base_url = f"https://{host}:{port}/" if verify_tls else f"http://{host}:{port}/"
#     headers  = {
#         "X-Trino-Catalog": catalog,
#         "X-Trino-Schema":  schema,
#         "X-Trino-Source":  source,
#         "X-Trino-User":    real_user,              # <<--- impersonation header
#         "Accept":          "application/json",
#     }

#     # 4) POST your SQL, walk the `nextUri` until you see `columns`
#     resp = sess.post(urljoin(base_url, "v1/statement"), data=query, headers=headers)
#     resp.raise_for_status()
#     job = resp.json()

#     while "columns" not in job and "error" not in job:
#         if debug:
#             print("waiting for first page…")
#         nxt = job.get("nextUri")
#         if not nxt:
#             raise RuntimeError(f"no nextUri & no columns in: {job!r}")
#         resp = sess.get(nxt, headers=headers)
#         resp.raise_for_status()
#         job = resp.json()

#     if job.get("error"):
#         err = job["error"]
#         raise RuntimeError(f"Trino error ({err.get('errorCode')}): {err.get('message')}")

#     cols  = job["columns"]
#     names = [c["name"] for c in cols]
#     rows  = job.get("data", [])
#     if debug:
#         print(f"first page: {len(rows)} rows")

#     # 5) page through the rest
#     while job.get("nextUri"):
#         resp = sess.get(job["nextUri"], headers=headers)
#         resp.raise_for_status()
#         job = resp.json()
#         if job.get("error"):
#             err = job["error"]
#             raise RuntimeError(f"mid-pagination error: {err.get('message')}")
#         batch = job.get("data", [])
#         rows.extend(batch)
#         if debug:
#             print(f"fetched page: {len(batch)} rows (total {len(rows)})")

#     # 6) build a single pyarrow.Table then convert to Polars
#     arrays = [pa.array([r[i] for r in rows]) for i in range(len(names))]
#     table  = pa.Table.from_arrays(arrays, names=names)
#     df     = pl.from_arrow(table)

#     if debug:
#         print("final shape:", df.shape)
#     return df