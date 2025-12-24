import sqlite3
import numpy as np
import pandas as pd


def get_table_list(conn:sqlite3.connect)->list:
    '''
    get list of tables from sqlite3 db and returns a list with success boolean
    '''
    cur = conn.cursor()
    try:
        table_names = cur.execute("Select name from sqlite_master where type='table';")
        response_list = list(table_names.fetchall())
        table_list = []
        for table in response_list:
            table_list.append(table[0])
        return [True, table_list]

    except Exception as err:
        return (False, err)


def get_col_names(conn:sqlite3.connect, table:str)->list:
    '''
    get names of columns in a table along with success boolean from sqlite3 db
    '''
    cur = conn.cursor()
    try:
        cur.execute(f'Select * from {table};')
        names = np.array(cur.description)[:,0]
        return [True, names]

    except Exception as err:
        return [False, err]

def del_table(conn: sqlite3.connect, tables:list)->list:
    '''
    Delete a tables from sqlite3 db from list of tables and returns list of list:
    [deleted_tables, failed_tables]
    '''
    cur = conn.cursor()
    deleted_tables = []
    failed_tables = []

    for table in tables:
        try:
            cur.execute(f'Drop table {table};')
            conn.commit()
            deleted_tables.append(table)

        except Exception as err:
            return failed_tables.append([table, err])
    
    return [deleted_tables, failed_tables]

def del_table_all(conn: sqlite3.connect)->list:
    '''
    deletes all tables in sqlite3 db and returns list of tables deleted
    '''
    table_list = get_table_list(conn)
    response = del_table(conn, table_list)
    return response

def empty_tables(conn: sqlite3.connect)->list:
    '''
    Delete all records from all tables from sqlite3 db and returns success boolean as list
    '''
    tables_emptied = []
    cur = conn.cursor()
    table_list = get_table_list(conn)
    for table in table_list:
        cur.execute(f'Delete from {table};')
        tables_emptied.append(table)
    
    conn.commit()

    return [True, tables_emptied]

def database_repair(conn):
    '''
    compresses the sqlite3 db
    '''
    conn.execute('VACUUM')

