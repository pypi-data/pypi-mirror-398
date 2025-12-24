from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine import URL
from sqlalchemy import inspect
from sqlalchemy.sql import text
import pandas as pd
from operator import itemgetter
from krazy import utility_functions as uf
import psycopg
from typing import Optional, List
from psycopg import sql
from sqlalchemy import MetaData, Table, update, String, Float, Integer, Date
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.types import TIMESTAMP

'''
PostgresSql wrapper functions
For all functions, pass connected engine
'''

def create_connection(username, host, database, password):
    '''
    Create sqlalchemy connection for postgresql
    '''
    url = URL.create(
    drivername="postgresql",
    username=username,
    host=host,
    database=database,
    password=password
)
    return create_engine(url)

def get_schema_names(engine):
    '''
    Takes SQLAlchemy engine and returns schema names as list
    '''
    inspector = inspect(engine)
    return inspector.get_schema_names()

def get_table_names(engine)->dict:
    '''
    Takes SQLAlchemy engine and returns schema wise table names as dictionary
    '''
    inspector = inspect(engine)
    schemas = get_schema_names(engine)
    tables = {}
    for schema in schemas:
        tables[schema] = (inspector.get_table_names(schema=schema))

    return tables

def table_search(table_name: str, engine:create_engine)->list:
    '''
    Searches for given table name in tables on Postgressql Server
    Pass sqlalchemy engine with connection on
    '''

    table_names=get_table_names(engine)
    
    if table_names:
        srch_results = []
        for key in list(table_names.keys()):
            table_names_schema = table_names[key]
            for name in table_names_schema:
                if table_name in name.lower():
                    srch_results.append([key, name])
        return srch_results
    else:
        return None

def get_table_schema(schema:str, table:str, engine:create_engine, df_to_compare=pd.DataFrame())->list[pd.DataFrame, list]:
    '''
    Returns list containing table schema as dataframe and useful columns as list
    '''
    # check if schema and table exists and return schema as dataframe
    tables = get_table_names(engine)
    if table in tables[schema]:
        sql = f'''
        select *
        from information_schema.columns
        where table_schema = '{schema}'
        and table_name = '{table}';
        '''
        df_table_schema = pd.read_sql_query(sql, engine)
        useful_cols = ['table_name', 'column_name', 'udt_name', 'character_maximum_length']

        if df_to_compare.empty:
            pass
        else:
            cols_length = {}
            for col in df_to_compare.columns.tolist():
                cols_length[col] = df_to_compare[col].apply(lambda x: len(str(x))).max()
            
            df_table_schema['df_length'] = df_table_schema['column_name'].map(cols_length)
            df_table_schema.loc[df_table_schema['udt_name'].isin(['varchar']), 'Diff'] = df_table_schema.loc[df_table_schema['udt_name'].isin(['varchar']), 'character_maximum_length'] - df_table_schema.loc[df_table_schema['udt_name'].isin(['varchar']), 'df_length']

            useful_cols.append('df_length')
        
        useful_cols.append('Diff')

        return [df_table_schema, useful_cols]

    else:
        print(f'Table: {table} not found in schema: {schema}')
        return [None, None]

def table_delete(schema, table_name, engine:create_engine)->None:
    '''
    Deletes given tabe on postgresql server
    '''
    
    table_list = table_search(table_name, engine)
    
    cur = engine.connect()
    cur.execute(text(f'Drop table if exists "{schema}".{table_name};'))
    cur.commit()

def create_table(df:pd.DataFrame, schema, table_name, engine:create_engine)->None:
    '''
    Creates table in Postgresql server based on dataframe supplied
    '''

    df_dtypes = uf.dtype_to_df(df)

    df_dtypes['Data type'] = ''
    
    for ind, row in df_dtypes.iterrows():
        if row['Type'] == 'datetime64[ns]':
            df_dtypes.loc[ind, 'Data type'] = 'date'
        elif row['Type'] == 'float64':
            df_dtypes.loc[ind, 'Data type'] = 'float8'
        elif row['Type'] == 'float':
            df_dtypes.loc[ind, 'Data type'] = 'float8'
        elif row['Type'] == 'int':
            df_dtypes.loc[ind, 'Data type'] = 'int8'
        elif row['Type'] == 'int64':
            df_dtypes.loc[ind, 'Data type'] = 'int8'
        elif df[row['Col']].astype(str).str.len().max() <= 90:
            max_len = df[row['Col']].astype(str).str.len().max()
            df_dtypes.loc[ind, 'Data type'] = f'varchar({max_len+10})'
        else:
            df_dtypes.loc[ind, 'Data type'] = 'text'

    col_string = []
    for ind, row in df_dtypes.iterrows():
        col_string.append(f'''"{row['Col']}" {row['Data type']}''')

    col_string = ', '.join(col_string)

    sql = f'Create table "{schema}".{table_name} ({col_string});'
    
    with engine.begin() as conn:
        conn.execute(text(sql))    
    
    # cur = engine.connect()
    # cur.execute(sql)
    # cur.commit()

def dbase_col_checker_adder(
    schema: str,
    table_name: str,
    df_to_compare: pd.DataFrame,
    engine: Engine,
    speak: bool = False
) -> Optional[List[str]]:
    """
    Ensures that the columns in a DataFrame exist in a specified PostgreSQL table.
    Adds any missing columns and modifies column lengths if the DataFrame has longer values.

    Args:
        schema (str): Name of the schema in the database.
        table_name (str): Name of the table to compare with.
        df_to_compare (pd.DataFrame): DataFrame whose columns are to be compared.
        engine (Engine): SQLAlchemy engine connected to the target PostgreSQL database.
        speak (bool, optional): If True, prints the progress and actions performed. Defaults to False.

    Returns:
        Optional[List[str]]: List of newly added columns, or None if schema/table doesn't exist.
    """

    # ✅ Check if schema exists
    if schema not in get_schema_names(engine):
        if speak:
            print(f"Schema '{schema}' does not exist.")
        return None

    # ✅ Check if table exists
    if table_name not in get_table_names(engine)[schema]:
        if speak:
            print(f"Table '{table_name}' does not exist.")
        return None

    # ✅ Get existing table schema
    df_table_schema = get_table_schema(schema, table_name, engine, df_to_compare)[0]

    # ✅ Identify new columns to add
    df_cols = uf.dtype_to_df(df_to_compare)
    df_col_diff = df_cols.loc[~df_cols['Col'].isin(df_table_schema['column_name'].tolist())]

    postgres_dtype_map = {
        'datetime64[ns]': 'date',
        'float64': 'float8',
        'int': 'int8',
        'int64': 'int8',
        'object': 'text'
    }

    added_cols = []

    with psycopg.connect(engine.url.render_as_string(hide_password=False)) as conn:
        with conn.cursor() as cur:

            if df_col_diff.empty:
                if speak:
                    print("✅ No new columns to add.")
            else:
                if speak:
                    print("🛠 Adding new columns:")
                    print(df_col_diff[['Col', 'Type']])

                queries = []
                for _, row in df_col_diff.iterrows():
                    col_name = row["Col"]
                    col_type = postgres_dtype_map.get(str(row["Type"]), "text")
                    if speak:
                        print(f"➕ Adding column '{col_name}' of type {col_type}")
                    query = sql.SQL(
                        'ALTER TABLE {}.{} ADD COLUMN IF NOT EXISTS {} {} NULL;'
                    ).format(
                        sql.Identifier(schema),
                        sql.Identifier(table_name),
                        sql.Identifier(col_name),
                        sql.SQL(col_type)
                    )
                    added_cols.append(col_name)
                    queries.append(query)
                    if speak:
                        print(f'Qureiry to add column: {query}')

                for query in queries:
                    if speak:
                        print(f'Executing query: {query}')
                    cur.execute(query)
                

            # ✅ Handle column length corrections
            if speak:
                print("🔍 Checking for column length corrections...")

            if 'Diff' in df_table_schema.columns:
                df_length_mismatch = df_table_schema[df_table_schema['Diff'] < 0]
                for _, row in df_length_mismatch.iterrows():
                    col_name = row['column_name']
                    new_length = int(row['df_length'])
                    if speak:
                        print(f"🛠 Modifying column '{col_name}' to length {new_length}")
                    alter_query = sql.SQL(
                        'ALTER TABLE {}.{} ALTER COLUMN {} TYPE VARCHAR({})'
                    ).format(
                        sql.Identifier(schema),
                        sql.Identifier(table_name),
                        sql.Identifier(col_name),
                        sql.Literal(new_length)
                    )
                    cur.execute(alter_query)

                conn.commit()

    return added_cols

def dbase_updater(engine, schema:str, table_to_update:str, df_to_update:pd.DataFrame, unique_col:str)->None:
    """
    Updates records in a PostgreSQL table using a temporary staging table for comparison.

    This function performs an upsert-style update by:
    1. Creating a temporary table (`temp_table`) with the incoming DataFrame.
    2. Generating an `UPDATE` SQL statement that modifies only those records in the target table
       that differ in content (based on a hash comparison across selected columns).
    3. Committing the updates and cleaning up the temporary table.

    Only rows with a matching `unique_col` and differing data across compared columns
    will be updated. This avoids unnecessary writes and preserves unchanged data.

    Args:
        engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine connected to the database.
        schema (str): The schema in which the target table resides.
        table_to_update (str): The name of the target table to be updated.
        df_to_update (pd.DataFrame): The DataFrame containing updated values.
        unique_col (str): Column used to uniquely identify records for update matching.

    Returns:
        sqlalchemy.engine.CursorResult: The result set returned from the `UPDATE ... RETURNING *` query,
        containing rows that were updated.

        - The following columns are ignored from update comparison: `folder`, `file_name`.
        - Updates are based on hash comparisons (using `md5`) to detect any changes between existing
          and new records.
        - Columns not present in the existing table are ignored.
        - The function is safe for large-scale updates as it only modifies differing rows.

    Example:
        dbase_updater(
            engine=db_engine,
            schema='finance',
            table_to_update='expenses',
            df_to_update=updated_df,
            unique_col='invoice_id'
        )
    """
    # delete temp_table if exists
    cur = engine.connect()
    cur.execute(text(f'''drop table if exists "{schema}".temp_table;'''))
    cur.commit()

    # push data in temp table
    df_to_update.to_sql('temp_table', con=engine, schema=schema, if_exists='replace', index=False)

    # get table columns
    df_cols = pd.read_sql_query(f'''select * from "{schema}".{table_to_update} limit 1;''', engine)
    df_cols = df_cols.columns

    # generate update query
    update_query = f'''update "{schema}".{table_to_update} tab1 set '''
    for col in df_to_update.columns:
        if col in df_cols and col != unique_col:  # exclude unique_col
            update_query += f'''"{col}" = tem."{col}", '''
    update_query = update_query[:-2]  # remove trailing comma

    # prepare hash columns
    cols_temp, cols_tab1 = '', ''
    cols_list = df_to_update.columns.tolist()
    remove_cols = ['folder', 'file_name', unique_col]  # optionally exclude unique_col from hash
    cols_list = [col for col in cols_list if col not in remove_cols]

    for col in cols_list:
        if col in df_cols:
            cols_temp += f'''COALESCE(CAST(tem."{col}" AS TEXT), '') || '''
            cols_tab1 += f'''COALESCE(CAST(tab1."{col}" AS TEXT), '') || '''
    if cols_temp.endswith(' || '):
        cols_temp = cols_temp[:-4]
    if cols_tab1.endswith(' || '):
        cols_tab1 = cols_tab1[:-4]

    # add FROM clause
    update_query += f''' from "{schema}".temp_table as tem where tab1."{unique_col}" = 
        tem."{unique_col}" and
        md5(cast(({cols_temp}) as text)) != md5(cast(({cols_tab1}) as text)) returning *;'''

    # execute and cleanup
    results = cur.execute(text(update_query))
    cur.commit()
    cur.execute(text(f'''drop table if exists "{schema}".temp_table;'''))

    return results

def dbase_writer(df: pd.DataFrame, schema, table, engine:create_engine, append=True)->None:
    """
    Writes a pandas DataFrame to a PostgreSQL database table with flexible options for data persistence.

    This function performs one of the following based on the `append` parameter:
    - `"delete_table"`: Drops the table if it exists, recreates it using the schema inferred from the DataFrame, and inserts the data.
    - `False`: Deletes all rows from the existing table (without dropping the table structure) and inserts the new data.
    - `True` (default): Appends new rows to the existing table.

    Additionally, this function checks for new columns in the DataFrame not present in the database table,
    and adds them automatically before performing the insert operation.

    Args:
        df (pd.DataFrame): The DataFrame containing data to be written to the database.
        schema (str): The target database schema.
        table (str): The name of the table to write data into.
        engine (sqlalchemy.engine.base.Engine): SQLAlchemy engine connected to the database.
        append (Union[bool, str], optional): 
            - `True` (default): Append to existing table.
            - `False`: Delete all existing rows and insert fresh data.
            - `"delete_table"`: Drop and recreate the table before inserting data.

    Returns:
        None

    Raises:
        ValueError: If the provided schema does not exist in the database.

    Notes:
        - Automatically handles schema evolution by adding new columns found in the DataFrame.
        - Relies on helper functions: `get_schema_names`, `get_table_names`, `table_delete`, `create_table`, and `dbase_col_checker_adder`.

    Example:
        dbase_writer(df=my_df, schema="finance", table="expenses", engine=db_engine, append=True)
    """
    cur = engine.connect()

    if schema not in get_schema_names(engine):
        print(f'Schema {schema} does not exist')
        return None
    
    tables = get_table_names(engine)

    if append=='delete_table':
        
        # delete table
        table_delete(schema=schema, table_name=table, engine=engine)
        print(f'Table: {table} deleted')

        # create table
        create_table(df, schema, table, engine)
        print(f'Table: {table} re-created')

    elif append==False:
                        
        # delete rows
        cur.execute(text(f'Delete from "{schema}".{table};'))
        print(f'Deleted all data from table: {table}')

    else:
        pass

    # check and add columns
    new_cols = dbase_col_checker_adder(schema, table, df, engine, speak=False)
    if new_cols is not None:
        print(f'New columns added: {new_cols}')

    # write to db
    df.to_sql(table, engine, if_exists='append', index=False, schema=schema)

def dbase_writer_dup_handled(
        engine, df_purge:pd.DataFrame, 
        schema:str, 
        table_name:str, 
        unique_col:str=None, 
        files_processed:pd.DataFrame=None,
        update_dup:bool=False)->Optional[int]:
    """
    Writes a DataFrame to a PostgreSQL database table while handling duplicates and maintaining audit of processed files.

    This function performs the following operations:
    1. Checks if the target table exists in the database. If not, it creates the table and adds a surrogate `row_id` primary key.
    2. If `unique_col` is provided:
       - Fetches existing values from the target table.
       - Filters out already existing records from `df_purge`.
       - If `update_dup=True`, updates duplicate records in the database using the `dbase_updater` function.
    3. Appends the remaining (new) records in `df_purge` to the database using `dbase_writer`.
    4. Optionally logs the processed files to the `settings.file_control` table if `files_processed` is provided.

    Args:
        engine (sqlalchemy.engine.base.Engine): SQLAlchemy database engine for PostgreSQL.
        df_purge (pd.DataFrame): DataFrame to be written to the database.
        schema (str): Schema where the target table resides.
        table_name (str): Name of the target database table.
        unique_col (str, optional): Column name used to identify duplicates. Defaults to None.
        files_processed (pd.DataFrame, optional): DataFrame containing metadata about files processed for audit logging. Defaults to None.
        update_dup (bool, optional): Whether to update existing records in the database that match the `unique_col`. Defaults to False.

    Returns:
        int:
            - `True` (1) if new data was written or updated.
            - `None` if no changes were made to the database (i.e., no new or updated records).
    """
    files_written = False
    cur = engine.connect()
    print(f'length of data: {len(df_purge)}')
    if df_purge.empty:
        print('No data to push')
        return None
    else:
        # check if table exists
        dbase_tables = get_table_names(engine)

        if table_name in dbase_tables[schema]:
            pass
        else:
            # create table
            create_table(df_purge, schema, table_name, engine)
            # establish primary key
            cur.execute(text(f'''alter table "{schema}".{table_name} add row_id serial NOT NULL;'''))
            cur.execute(text(f'''alter table "{schema}".{table_name} add constraint {table_name}_pk primary key (row_id);'''))
            cur.commit()

        if unique_col==None:
            pass
        else:
            ## get unique ID in database
            data = cur.execute(text(f'''select distinct "{unique_col}" from "{schema}".{table_name} ;''')).fetchall()
            ## get first element from each element from list of lists
            ref_id = list(map(itemgetter(0), data))

            if update_dup:
                # get duplicates
                df_duplicates = df_purge.loc[df_purge[unique_col].isin(ref_id)]
                # update duplicate in database
                print(f'Updating {len(df_duplicates)} existing records in database')
                results = dbase_updater(engine, schema, table_name, df_duplicates, unique_col) # updates only those columns which are already present in the database
                files_written = True

            ## remove already existing items
            df_purge = df_purge.loc[~df_purge[unique_col].isin(ref_id)]

        # push data to database
        if df_purge.empty:
            print(f'No new records to push to database')
        else:
            print(f'Pushing {len(df_purge)} records to database')
            dbase_writer(df_purge, schema, table_name, engine, append=True)
            files_written = True
            print(f'Pushed {len(df_purge)} records to database')            

        # push files processed to database
        if files_written and files_processed is not None:
            if 'file_control' not in dbase_tables['settings']:
                create_table(files_processed, 'settings', 'file_control', engine)
            
            dbase_writer(files_processed, 'settings', 'file_control', engine, append=True)
            print(f'Pushed files processed to database')

            return True
        
        else:
            # return none if no file written
            return None

def upsert_postgres_from_dataframe(
    engine: Engine,
    df: pd.DataFrame,
    schema: str,
    table_name: str,
    key_column: Optional[str] = None,
    mode: str = "upsert",
    add_cols: bool = False,
    alter_cols: bool = False
) -> bool:
    """
    Flexible DataFrame-to-Postgres sync function.
    Returns True if operation is successful, else returns False and prints/logs the error.
    Parameters:
        engine: SQLAlchemy engine
        df: pandas DataFrame
        schema: str, schema name
        table_name: str, table name
        key_column: str or None, column to match for upsert/insert/update. If None, only insert is allowed.
        mode: 'upsert' (default), 'insert', or 'update'
        add_cols: bool, if True add missing columns to DB, else skip them (default: False)
        alter_cols: bool, if True alter column types/lengths to fit DataFrame, else skip (default: False)
    Behavior:
        - If key_column is None, only insert is allowed (mode is forced to 'insert').
        - 'upsert': Upsert if key_column is unique/PK, else insert only new rows. Respects add_cols/alter_cols.
        - 'insert': Insert only new rows (ignore existing). Respects add_cols/alter_cols.
        - 'update': Update only existing rows (ignore new). Respects add_cols/alter_cols.
    """
    try:
        # Convert NaN/NaT to None so they map to SQL NULLs
        df = df.astype(object).where(pd.notnull(df), None)
        
        print(f"[INFO] Starting sync to {schema}.{table_name} (mode={mode}, add_cols={add_cols}, alter_cols={alter_cols}, key_column={key_column})")
        metadata = MetaData(schema=schema)
        table = Table(table_name, metadata, autoload_with=engine)
        db_columns = {col.name: col for col in table.columns}
        df_columns = set(df.columns)
        missing_columns = df_columns - set(db_columns.keys())
        dtype_map = {
            'object': String,
            'float64': Float,
            'int64': Integer,
            'datetime64[ns]': Date,
            'bool': Integer,
            'float32': Float,
            'int32': Integer,
            'datetime64[ns, UTC]': TIMESTAMP
        }
        # Add missing columns if requested
        if add_cols:
            print(f"[INFO] Adding missing columns: {missing_columns}")
            for col in missing_columns:
                dtype = str(df[col].dropna().dtype)
                col_type = dtype_map.get(dtype, String)
                if col_type == String:
                    max_len = df[col].dropna().astype(str).map(len).max() or 255
                    col_type = String(int(max_len))
                if isinstance(col_type, type):
                    col_type_instance = col_type()
                else:
                    col_type_instance = col_type
                alter_sql = f'ALTER TABLE "{schema}"."{table_name}" ADD COLUMN IF NOT EXISTS "{col}" {col_type_instance.compile(dialect=engine.dialect)}'
                with engine.begin() as conn:
                    conn.execute(text(alter_sql))
            print(f"[INFO] Columns added (if any were missing). Reloading table metadata.")
            metadata = MetaData(schema=schema)
            table = Table(table_name, metadata, autoload_with=engine)
            db_columns = {col.name: col for col in table.columns}
        # Optionally alter columns
        if alter_cols:
            print(f"[INFO] Checking for column length/type corrections...")
            for col, db_col in db_columns.items():
                if col in df.columns:
                    dtype = str(df[col].dropna().dtype)
                    if isinstance(db_col.type, String):
                        max_len = df[col].dropna().astype(str).map(len).max() or 1
                        if db_col.type.length is not None and max_len > db_col.type.length:
                            alter_sql = f'ALTER TABLE "{schema}"."{table_name}" ALTER COLUMN "{col}" TYPE VARCHAR({max_len})'
                            with engine.begin() as conn:
                                conn.execute(text(alter_sql))
            print(f"[INFO] Column length/type corrections complete.")
        # Only use columns present in DB
        valid_columns = set(table.columns.keys())
        use_columns = [col for col in df.columns if col in valid_columns]
        df = df[use_columns]
        unique_cols = set()
        pk_cols = set()
        if key_column is None:
            print(f"[INFO] key_column is None. Only insert operations are allowed. Forcing mode to 'insert'.")
            mode = "insert"
        else:
            inspector = inspect(engine)
            unique_constraints = inspector.get_unique_constraints(table_name, schema=schema)
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            for uc in unique_constraints:
                unique_cols.update(uc['column_names'])
            pk_cols = set(pk_constraint.get('constrained_columns', []))
        # Helper: get existing keys
        def get_existing_keys():
            with engine.connect() as conn:
                result = conn.execute(text(f'SELECT "{key_column}" FROM "{schema}"."{table_name}"'))
                return set(row[0] for row in result)
        if mode == "insert" or (mode == "upsert" and (key_column is None or (key_column not in unique_cols and key_column not in pk_cols))):
            if mode == "upsert" and key_column is not None:
                print(f"[WARN] '{key_column}' is not a unique or primary key in {schema}.{table_name}. Falling back to insert-only for new rows.")
            if key_column is not None:
                existing_keys = get_existing_keys()
                df_new = df[~df[key_column].isin(existing_keys)]
            else:
                df_new = df
            if not df_new.empty:
                print(f"[INFO] Inserting {len(df_new)} new rows into {schema}.{table_name}.")
                data = df_new.to_dict(orient='records')
                stmt = insert(table).values(data)
                with engine.begin() as conn:
                    conn.execute(stmt)
            else:
                print(f"[INFO] No new rows to insert for {schema}.{table_name}.")
            print(f"[INFO] Insert operation complete.")
            return True
        elif mode == "update":
            if key_column is None:
                print(f"[ERROR] key_column must be provided for update mode. Aborting.")
                return False
            existing_keys = get_existing_keys()
            df_existing = df[df[key_column].isin(existing_keys)]
            if not df_existing.empty:
                print(f"[INFO] Updating {len(df_existing)} existing rows in {schema}.{table_name}.")
                with engine.begin() as conn:
                    for _, row in df_existing.iterrows():
                        update_dict = row.to_dict()
                        if key_column in update_dict:
                            update_dict = {k: v for k, v in update_dict.items() if k != key_column}
                        stmt = (
                            update(table)
                            .where(getattr(table.c, key_column) == row[key_column])
                            .values(**update_dict)
                        )
                        conn.execute(stmt)
            else:
                print(f"[INFO] No existing rows to update for {schema}.{table_name}.")
            print(f"[INFO] Update operation complete.")
            return True
        # Default: upsert (key_column is unique or PK)
        if key_column is not None:
            print(f"[INFO] Performing upsert for {len(df)} rows in {schema}.{table_name}.")
            with engine.begin() as conn:
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    stmt = insert(table).values(**row_dict)
                    update_dict = row.to_dict()
                    if key_column in update_dict:
                        update_dict = {k: v for k, v in update_dict.items() if k != key_column}
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[key_column],
                        set_=update_dict
                    )
                    conn.execute(stmt)
            print(f"[INFO] Upsert operation complete.")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def build_sql_select(cols:list, table:str, schema:str, follow_through:str=None)->str:
    '''
    builds select sql string based on table name, schema and follow_through given
    '''
    cols = '","'.join(cols) #type: ignore
    if follow_through:
        if cols=='*':
            sql = f'select * from "{schema}".{table} {follow_through};'
        else:
            sql = f'select "{cols}" from "{schema}".{table} {follow_through};'
    else:
        if cols=='*':
            sql = f'select * from "{schema}".{table};'
        else:
            sql = f'select "{cols}" from "{schema}".{table};'

    return sql

def list_to_sql_list_converter(list_to_convert:list)->str:
    '''Convert a list to a postgressql style list'''
    if len(list_to_convert)>0:
        list_converted = "(" + ",".join([f"'{str(x)}'" for x in list_to_convert]) + ")"
    else:
        list_converted = "('')"
    return list_converted