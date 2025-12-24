
import pandas as pd
import numpy as np
import datetime
import os
from pathlib import Path
from icecream import ic
from rich import print
from langchain.chains import create_extraction_chain
from langchain_community.llms import Ollama
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from typing import List, Tuple, Dict, Any, Optional


def df_import_clean_files(dir:Path=False, clean:bool=True, df:pd.DataFrame=False, dtypes:dict=False, julian_date_cols:list=False)->list[pd.DataFrame, list]:
    '''
    import multiple files from a folder into pandas dataframe
    dir:    Required:   Path to the folder containing the files
    clean:  Optional:   Clean the dataframe. Default is True
    df:     Optional:   Pass a dataframe. This is required if dir is false and clean is True
    dtypes  Optional:   Pass a dictionary of data types for the columns
    '''
    if dir != False:
        df = pd.DataFrame()
        files_skipped = []

        for file in os.listdir(dir):
            file_path = dir.joinpath(file)
            if file_path.suffix.lower() == '.csv':
                if dtypes == False:
                    df_temp = pd.read_csv(dir.joinpath(file))
                else:
                    df_temp = pd.read_csv(dir.joinpath(file), dtype=dtypes)
                df = pd.concat([df, df_temp], axis=0, ignore_index=True)
            elif file_path.suffix.lower() == '.xlsx':
                if dtypes == False:
                    df_temp = pd.read_excel(dir.joinpath(file))
                else:
                    df_temp = pd.read_excel(dir.joinpath(file), dtype=dtypes)
                df = pd.concat([df, df_temp], axis=0, ignore_index=True)
            else:
                files_skipped.append(file)

    date_cols = df.select_dtypes(include='datetime').columns
    object_cols = df.select_dtypes(include='object').columns
    float_cols = df.select_dtypes(include='float').columns
    int_cols = df.select_dtypes(include='int').columns

    # identify possible date, amount columns imported as object cols
    possible_date_cols = [col for col in object_cols if 'date' in col.lower()]
    possible_amount_cols = [col for col in object_cols if 'amount' in col.lower()]
    possible_amt_cols = [col for col in object_cols if 'amt' in col.lower()]

    if len(possible_amt_cols)>0:
        possible_amount_cols.extend(possible_amt_cols)
     
    del possible_amt_cols

    # possible columns which are not date or amount
    possible_id_cols = [col for col in df.columns if col not in possible_date_cols]
    possible_id_cols = [col for col in possible_id_cols if col not in possible_amount_cols]

    # clean date and amount cols
    if clean is True and df is not False:

        if julian_date_cols:
            for col in julian_date_cols:
                df[col] = pd.to_datetime(df[col], errors='coerce', unit='D', origin='1899-12-30')

        if len(possible_date_cols)>0:
            for col in possible_date_cols:
                print(f'Converting column: {col} to date')
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if len(possible_amount_cols)>0:
            for col in possible_amount_cols:
                print(f'Converting column: {col} to float')
                df[col] = df[col].str.replace(',', '').replace('-',0).astype(float)

    if clean is True and df is False:
        print('No dataframe to clean')
        return False

    return [df, possible_date_cols, possible_amount_cols, possible_id_cols, files_skipped]

def df_common_cols(df1:pd.DataFrame, df2:pd.DataFrame)->list:
    common_cols = df1.columns.intersection(df2.columns).tolist()
    different_cols = df1.columns.difference(df2.columns).tolist()
    return [common_cols, different_cols]

def df_find_unique_col(df:pd.DataFrame):
    df_counts = pd.DataFrame(columns=['Column', 'Count', 'Unique', 'Diff'])
    # object columns
    cols = df.select_dtypes(include='object').columns

    for col in cols:
        diff = df[col].count() - df[col].nunique()
        df_counts.loc[len(df_counts)] = [col, df[col].count(), df[col].nunique(), diff]
    
    return df_counts

def matcher(df1, df2)->list[pd.DataFrame, pd.DataFrame]:
    '''
    takes two dataframes and returns the possible columns on which dataframes reconciles
    '''
    # get unique values in columns
    df1_counts = df_find_unique_col(df1)
    df2_counts = df_find_unique_col(df2)

    df1_counts.sort_values(by='Diff', ascending=True, inplace=True)
    df2_counts.sort_values(by='Diff', ascending=True, inplace=True)

    # find top 5 unique identifier columns - not used for now in favor of all columns
    # unique_identifier_1 = df1_counts[0:5]['Column'].tolist()
    # unique_identifier_2 = df2_counts[0:5]['Column'].tolist()

    # find unique identifier columns
    unique_identifier_1 = df1_counts['Column'].tolist()
    unique_identifier_2 = df2_counts['Column'].tolist()

    # Level 1: direct column name match
    matched_cols = []

    for col in unique_identifier_1:
        try:
            assert df2[col]
            matched_cols.append(col)
        except AssertionError:
            pass
        except Exception as e:
            pass

    matched_outcome_1 = pd.DataFrame(columns=['df1_Col','df2_Col', 'Matched_Percentage'])
    for col in matched_cols:
        df_merged = pd.merge(df1, df2, on=col, how='outer', indicator='Source')
        matched_perc = len(df_merged.loc[df_merged['Source']=='both'])/len(df_merged)
        matched_outcome_1[len(matched_outcome_1)] = [col, col, matched_perc]
    
    matched_outcome_1.sort_values(by='Matched_Percentage', ascending=False, inplace=True)
    matched_outcome_1['Reco_Level'] = 'Level 1 - Direct Col Name Match'

    # Level 2: top 5 column values match        
    matched_outcome_2 = pd.DataFrame(columns=['df1_Col','df2_Col', 'Matched_Percentage'])
    for col in unique_identifier_1:
        col_as_list = df1[col].tolist()
        for col2 in unique_identifier_2:
            col2_as_list = df2[col2].tolist()
            matched = set(col_as_list) & set(col2_as_list)
            matched_perc = len(matched)/len(set(col_as_list))
            matched_outcome_2.loc[len(matched_outcome_2)] = [col, col2, matched_perc]

    matched_outcome_2.sort_values(by='Matched_Percentage', ascending=False, inplace=True)
    matched_outcome_2['Reco_Level'] = 'Level 2 - Top 5 Col Values Match'

    # combine results
    matched_outcome = pd.concat([matched_outcome_1, matched_outcome_2], axis=0)
    matched_outcome.sort_values(by='Matched_Percentage', ascending=False, inplace=True)
    matched_outcome = matched_outcome.loc[matched_outcome['Matched_Percentage']>0]

    return matched_outcome


def search_any_col(df:pd.DataFrame, search_str:str)->pd.DataFrame:
    df_result = df.apply(lambda row: row.astype(str).str.contains(search_str).any(), axis=0)
    return df_result

def llm_extract_name()->create_extraction_chain:
    '''
    Extract names from a text string and returns name as string
    Returns: string
    '''
    model = OllamaFunctions(model='llama2', temperature=0)
    schema = {
        'properties': {
            'name':{'type':'string'}
        }
    }
    chain = create_extraction_chain(schema, model)

    return chain

# def match_one_to_many(one:list[pd.DataFrame, str], many:list[pd.DataFrame, str], col_from_one:list, col_from_many:list, match_return_col, tolerance:list=[1,-1])->list[pd.DataFrame, pd.DataFrame]:
#     '''
#     Takes:
#     df_one: DataFrame from where one row matches to many from other, dataframe name to use in match return column
#     df_many: DataFrame from where many rows match to one from other, dataframe name to use in match return column
#     col_from_one: Column from df_one to match, amount column
#     col_from_many: Column from df_many to match, and to sum
#     match_return_col: Column in which to return reco status
#     tolerance: Tolerance for matching for amounts. Default is 1 to -1

#     Returns a tuple of two DataFrames with reconciliation done in match_return_col
#     '''

#     df_one = one[0]
#     df_many = many[0]

#     # groupby many df
#     df_many_sum = df_many.groupby([col_from_many[0]]).agg({col_from_many[1]: 'sum'}).reset_index()

#     for index, row in df_one.loc[~df_one[match_return_col].str.contains('Matched')].iterrows():
#         df_many_amt = df_many_sum.loc[df_many_sum[col_from_many[0]]==row[col_from_one[0]],[col_from_many[1]]]
#         if df_many_amt.empty:
#             pass
#         else:
#             df_many_amt = df_many_sum.loc[df_many_sum[col_from_many[0]]==row[col_from_one[0]],[col_from_many[1]]].values[0][0]
#             diff_amt = abs(row[col_from_one[1]]) - abs(df_many_amt)

#             if tolerance[1] < diff_amt < tolerance[0]:
#                 df_one.loc[index, match_return_col] = f'Matched with Happay Report on {col_from_many[0]} from col {col_from_one[0]}'
#                 df_many.loc[df_many[col_from_many[0]]==row[col_from_one[0]], match_return_col] = f'Matched with GL on {col_from_many[0]} in col {col_from_one[0]}'
    
#     return [df_one, df_many]

def match_one_to_many(df_one:pd.DataFrame, df_many:pd.DataFrame, col_from_one:list, col_from_many:list, match_return_col, tolerance:list=[1,-1])->list[pd.DataFrame, pd.DataFrame]:
    '''
    Takes:
    df_one: DataFrame from where one row matches to many from other
    df_many: DataFrame from where many rows match to one from other
    col_from_one: Column from df_one to match, amount column should be the last item in the list
    col_from_many: Column from df_many to match, amount column should be the last item in the list
    match_return_col: Column in which to return reco status
    tolerance: Tolerance for matching for amounts. Default is 1 to -1

    Returns a tuple of two DataFrames with reconciliation done in match_return_col
    '''

    one_cols = col_from_one[0:-1]
    many_cols = col_from_many[0:-1]
    one_amt_col = col_from_one[-1]
    many_amt_col = col_from_many[-1]

    # create unique column
    df_one['unique_code_temp'] = ''
    for col in one_cols:
        df_one['unique_code_temp'] = df_one['unique_code_temp'] + ':' + df_one[col].astype(str)
    df_many['unique_code_temp'] = ''
    for col in many_cols:
        df_many['unique_code_temp'] = df_many['unique_code_temp'] + ':' + df_many[col].astype(str)

    # groupby many df
    df_many_sum = df_many.groupby(['unique_code_temp']).agg({many_amt_col: 'sum'}).reset_index()
    
    # merge dataframes
    df_merged = pd.merge(
        left=df_one, 
        right=df_many_sum, 
        on='unique_code_temp',
        suffixes=('_x', '_y'),
        how='inner',
        indicator='Source')
    
    # keep rows in both dataframes
    df_merged = df_merged.loc[df_merged['Source']=='both']

    # rename amount cols if same in both dataframes
    if one_amt_col == many_amt_col:
        one_amt_col = one_amt_col + '_x'
        many_amt_col = many_amt_col + '_y'

    # calculate difference
    df_merged['Diff'] = df_merged[one_amt_col] - df_merged[many_amt_col]

    # reconcile
    condition = df_merged['Diff'].between(tolerance[1], tolerance[0])
    df_merged.loc[condition, match_return_col] = 'Matched'
    matched_list = df_merged.loc[condition, 'unique_code_temp'].tolist()

    # map the result back to both dataframes
    df_one.loc[df_one['unique_code_temp'].isin(matched_list), match_return_col] = 'Matched'
    df_many.loc[df_many['unique_code_temp'].isin(matched_list), match_return_col] = 'Matched'

    # drop the unique code column
    df_one.drop(columns='unique_code_temp', inplace=True)
    df_many.drop(columns='unique_code_temp', inplace=True)
    
    return [df_one, df_many]

def match_one_to_one(one:list[pd.DataFrame, str], two:list[pd.DataFrame, str], col_from_one:list, col_from_two:list, match_return_col, tolerance:list=[1,-1])->list[pd.DataFrame, pd.DataFrame]:
    '''
    Takes:
    df_one: DataFrame from where one row matches to many from other, dataframe name to use in match return column
    df_two: DataFrame from where one rows match to one from other, dataframe name to use in match return column
    col_from_one: Column from df_one to match, amount column
    col_from_two: Column from df_many to match, and to sum
    match_return_col: Column in which to return reco status
    tolerance: Tolerance for matching for amounts. Default is 1 to -1

    Returns a tuple of two DataFrames with reconciliation done in match_return_col
    '''

    df_one = one[0]
    df_two = two[0]

    for index, row in df_one.loc[~df_one[match_return_col].str.contains('Matched')].iterrows():
        df_two_amt = df_two.loc[df_two[col_from_two[0]]==row[col_from_one[0]],[col_from_two[1]]]
        if df_two_amt.empty:
            pass
        else:
            two_amt = df_two_amt.loc[:,[col_from_two[1]]].values[0][0]
            diff_amt = abs(row[col_from_one[1]]) - abs(two_amt)

            if tolerance[1] < diff_amt < tolerance[0]:
                df_one.loc[index, match_return_col] = f'Matched with Happay Report on {col_from_two[0]} from col {col_from_one[0]}'
                df_two.loc[df_two_amt.index, match_return_col] = f'Matched with GL on {col_from_two[0]} in col {col_from_one[0]}'
    
    return [df_one, df_two]

def match_many_to_many(
    one: Tuple[pd.DataFrame, str],
    two: Tuple[pd.DataFrame, str],
    col_from_one: Tuple[str, str],
    col_from_two: Tuple[str, str],
    match_return_col: str,
    match_word: str = 'Matched',
    tolerance: List[float] = [1, -1]
) -> List[pd.DataFrame]:
    """
    Reconciles two dataframes where one row in df_one can match many in df_two based on a key and a summed amount.
    
    Args:
        one: Tuple of (DataFrame, name) for the primary dataframe.
        two: Tuple of (DataFrame, name) for the secondary dataframe.
        col_from_one: Tuple of (join key column, amount column) from df_one.
        col_from_two: Tuple of (join key column, amount column) from df_two.
        match_return_col: Column to write match result into.
        match_word: Match indicator text (default: 'Matched').
        tolerance: Allowed difference [positive, negative] between amounts (default: [1, -1]).
    
    Returns:
        List of updated [df_one, df_two] with match info written to `match_return_col`.
    """
    if tolerance is None:
        tolerance = [1, -1]

    # Extract dataframes and names
    df_one, name_one = one
    df_two, name_two = two

    join_key_one, amt_col_one = col_from_one
    join_key_two, amt_col_two = col_from_two

    # Filter unprocessed rows
    df_one_filtered = df_one[df_one[match_return_col].fillna('').str.contains(match_word, case=False) == False]
    df_two_filtered = df_two[df_two[match_return_col].fillna('').str.contains(match_word, case=False) == False]

    # Group and sum
    df_one_grouped = df_one_filtered.groupby(join_key_one, as_index=False)[amt_col_one].sum()
    df_two_grouped = df_two_filtered.groupby(join_key_two, as_index=False)[amt_col_two].sum()

    # Merge on join key
    df_merged = pd.merge(
        df_one_grouped,
        df_two_grouped,
        left_on=join_key_one,
        right_on=join_key_two,
        how='inner',
        suffixes=('_one', '_two'),
        indicator=False
    )

    # Calculate difference
    df_merged['Diff'] = abs(df_merged[amt_col_one]) - abs(df_merged[amt_col_two])

    # Identify matches
    match_mask = (df_merged['Diff'] <= tolerance[0]) & (df_merged['Diff'] >= tolerance[1])
    df_matched = df_merged[match_mask].copy()
    if df_matched.empty:
        return [df_one, df_two]

    # Create match descriptions
    msg_one = f'{match_word} with {name_two} on column {join_key_two}'
    msg_two = f'{match_word} with {name_one} on column {join_key_one}'

    # Update df_one
    matched_keys_one = df_matched[join_key_one].unique().tolist()
    df_one.loc[df_one[join_key_one].isin(matched_keys_one), match_return_col] = msg_one

    # Update df_two
    matched_keys_two = df_matched[join_key_two].unique().tolist()
    df_two.loc[df_two[join_key_two].isin(matched_keys_two), match_return_col] = msg_two

    return [df_one, df_two]