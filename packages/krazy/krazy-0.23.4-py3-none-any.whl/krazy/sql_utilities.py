import numpy as np
import pandas as pd
import pyodbc
import configparser
import sqlalchemy as sa
import urllib
from krazy import utility_functions as uf

# MS Sql erver related code below _____________________________

def connection_pyodbc(config_file_path)->pyodbc.connect:
    '''
    takes path to config file and connects to MS SQL server and returns pyodbc connection
    '''
    # read server config file

    config = configparser.ConfigParser()
    try:
        config.read(config_file_path)
        server = config['server_config']['server']
        database = config['server_config']['database']
        username = config['server_config']['username']
        password = config['server_config']['password']

        # connect to MS Sql Server

        # ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
        conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+server+';DATABASE='+database+';ENCRYPT=yes;UID='+username+';PWD='+ password)

        return conn

    except Exception as err:
        print('Connection failure')
        print(err)
        return False

def connection_sqlalchemy(config_file_path)->sa.engine:
    '''
    takes path to config file and connects to MS SQL server and returns sqlalchemy connection
    '''
    # read server config file
    config = configparser.ConfigParser()
    try:
        config.read(config_file_path)
        server = config['server_config']['server']
        database = config['server_config']['database']
        username = config['server_config']['username']
        password = config['server_config']['password']
        
        # connect to MS Sql Server
        
        # ENCRYPT defaults to yes starting in ODBC Driver 18. It's good to always specify ENCRYPT=yes on the client side to avoid MITM attacks.
        conn = "Driver=SQL Server;Server="+server+";Database="+database+";uid="+username+";pwd="+password
        conn = urllib.parse.quote_plus(conn)
        engine = sa.create_engine('mssql+pyodbc:///?odbc_connect={}'.format(conn))
        
        return engine
    
    except Exception as err:
        print('Connection failure')
        print(err)
        return False
    
def get_table_names(conn, conn_type:str='sqlalchemy'):
    '''
    Get all tables names from MS SQL Server
    '''

    if conn_type == 'pyodbc':
        cursor = conn.cursor()
        table_list = []
        for row in cursor.tables():
            table_list.append(row.table_name)
        return table_list
    
    elif conn_type == 'sqlalchemy':
        table_list = sa.inspect(conn).get_table_names()
        return table_list
    
    else:
        return None

def table_search(table_name: str, conn, conn_type:str='sqlalchemy')->list:
    '''
    Searches for given table name in tables on MS SQL Server
    '''
    if conn_type=='pyodbc':
        table_names = get_table_names(conn, 'pyodbc')
    elif conn_type=='sqlalchemy':
        table_names=get_table_names(conn)
    else:
        table_names=False
    
    if table_name:
        srch_results = []
        for name in table_names:
            if table_name in name.lower():
                srch_results.append(name)
        return srch_results
    else:
        return None

def table_delete(table_name, conn:pyodbc.connect)->bool:
    '''
    Deletes given tabe on MS SQL Server
    '''
    table_list = table_search(table_name, conn, 'pyodbc')
    if table_name in table_list:
        cur = conn.cursor()
        cur.execute(f'Drop table {table_name};')
        conn.commit()
        return True
    else:
        return False

def get_col_types(table, conn:pyodbc.connect)->dict:
    cur = conn.cursor()
    col_types = cur.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}';").fetchall()
    col_dict = {}
    for elem in col_types:
        col_dict[elem[0]] = elem[1]
    
    return col_dict

def create_table(df:pd.DataFrame, table_name, conn_pyodbc:pyodbc.connect)->None:
    '''
    Creates table in MS SQL server based on dataframe supplied
    '''

    df_dtypes = uf.dtype_to_df(df)

    df_dtypes['Data type'] = ''
    for ind, row in df_dtypes.iterrows():
        if row['Type'] == 'datetime64[ns]':
            df_dtypes['Data type'][ind] = 'datetime'
        elif row['Type'] == 'float64':
            df_dtypes['Data type'][ind] = 'real'
        elif row['Type'] == 'float':
            df_dtypes['Data type'][ind] = 'real'
        elif row['Type'] == 'int':
            df_dtypes['Data type'][ind] = 'real'
        elif row['Type'] == 'int64':
            df_dtypes['Data type'][ind] = 'real'
        else:
            df_dtypes['Data type'] = 'varchar(400)'

    col_string = ''
    for ind, row in df_dtypes.iterrows():
        col_string += f"[{row['Col']}] {row['Data type']},"

    col_string = col_string[:-2] + ')'

    sql = f'Create table {table_name} ({col_string});'
    cur = conn_pyodbc.cursor()
    cur.execute(sql)
    conn_pyodbc.commit()

def dbase_writer(df: pd.DataFrame, table, conn_pyodbc:pyodbc.connect, append=True)->None:
    '''
    writes data to table. Accepts following arguments for append:
    True = append to existing data
    False = deletes all rows and then insert data into existing table
    delete_table = delete table, recreate table and writes data
    '''
    cur = conn_pyodbc.cursor()

    if append=='delete_table':
        # delete table
        table_delete(table_name=table, conn=conn_pyodbc)
        print(f'Table: {table} deleted')

        # create table
        create_table(df, table, conn_pyodbc)
        print(f'Table: {table} re-created')

    elif append==False:
        # delete rows
        cur.execute(f'Delete * from {table}')
        print(f'Deleted all data from table: {table}')

    for col in df.columns:
        if df[col].dtypes == 'float' or df[col].dtypes == 'float64' or df[col].dtypes == 'int' or df[col].dtypes == 'int64':
            pass
        else:
            if df[col].astype(str).str.len().max() > 225:
                df[col] = df[col].str.slice(start=0, stop=399)
                print(f'Characters truncated for column {col} beyond 400 characters')

    # write data
    data = df.values.tolist()
    cols = df.columns.tolist()
    cols2 = []
    for col in cols:
        cols2.append('[' + col + ']')
    cols = cols2.copy()
    del cols2
    cols = '(' + ', '.join(cols) + ')'

    data_str = "?," * len(df.columns.tolist())
    data_str = '(' + data_str[:-1] + ')'
    sql = f'Insert into {table} {cols} values {data_str};'

    cur.executemany(sql, data)
    conn_pyodbc.commit()
    print(f'Data written to table {table}')