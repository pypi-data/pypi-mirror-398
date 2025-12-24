
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# grspread documentation
## https://docs.gspread.org/en/latest/
# gspread can work with service account login as well as OAuth client ID

def google_workbook_open(csjson:str, file_name: str, file_id:str, file_url:str) -> object:

    '''
    takes csjson as path to client secret json file
    takes file_name as google sheet name
    returns google workbook object
    
    '''


    # define the scope
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(csjson, scope)

    # authorize the clientsheet 
    client = gspread.authorize(creds)

    # get the instance of the Spreadsheet

    ## by file id if its given
    try:
        if file_id not in [None,'']:
            wb = client.open_by_key(file_id)
        elif file_name not in [None,'']:
            wb = client.open(file_name)
        elif file_url not in [None,'']:
            wb = client.open_by_url(file_url)
        else:
            return ['Not Found']
        return ['Success',wb]

    except:
        return ['Error']


# # grspread documentation
# ## https://docs.gspread.org/en/latest/
# # gspread can work with service account login as well as OAuth client ID

# # define the scope
# scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# # add credentials to the account
# creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

# # authorize the clientsheet 
# client = gspread.authorize(creds)

# # get the instance of the Spreadsheet
# wb = client.open('PythonTestFile')

# # get list of worksheets in the file
# ws_list = wb.worksheets()

# # get the first sheet of the Spreadsheet
# sheet_instance = wb.get_worksheet(0) # 0 index
# ## or
# # sheet_instance = wb.sheet1

# # get worksheet by name
# sheet_instance = wb.worksheet('Sheet1')

# # get data from sheet in form of dictionery
# data_dict = sheet_instance.get_all_records() # returns all records in python dictionery

# # get data from sheet in form of list of list
# data_list = sheet_instance.get_all_values() # returns all records in python list of list

# # get value of a particular cell
# cell_val = sheet_instance.cell(1, 2).value

# # get first row
# row_val = sheet_instance.row_values(1) # 1 index
# print(row_val)

# # get first column
# col_val = sheet_instance.col_values(1) # 1 index

# # change value in a cell
# sheet_instance.update_cell(2,2,5000)

# # update multiple cells in a row
# cell_coordinates = 'A' + '5' + ':' + 'C' + '6'
# sheet_instance.update(cell_coordinates,[[1,7000,'AAA'],[7,10000,'BBB']])

# # insert row at specified index. If there is data at that index then it shifts existing data below inserted row.
# row = [3,5000,'XYZ']
# sheet_instance.insert_row(row,2)

# # get row count
# rowcount = sheet_instance.row_count

# # delete row
# sheet_instance.delete_rows(4)

# # findnig all matched cells
# cell_list = sheet_instance.findall("Rug store") # all matched cells
# cell = sheet_instance.find('Rug Store') # first matched cell

# # convert to dataframe
# df = pd.DataFrame.from_dict(data_dict)

