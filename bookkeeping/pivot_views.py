from django.shortcuts import render, redirect
from .Google import Create_Service
from cat_converter import settings
import os
import gspread
import pickle
from django.http import JsonResponse
from .views import list_files_and_folders

def index(request):
    # Retrieve success_message and error_message from the session (if they exist)
    success_message = request.session.pop('success_message', None)
    error_message = request.session.pop('error_message', None)
    return render(request, 'index.html', {'success_message': success_message, 'error_message': error_message})

def pivotformtable(sheet_name_pivot, credit_column_name, debit_column_name, cat_column_letter):
    try:
        # Load credentials from token_drive_v3.pickle
        credentials_path = 'token_drive_v3.pickle'
        with open(credentials_path, 'rb') as token:
            credentials = pickle.load(token)

        # Authorize the client using the loaded credentials
        client = gspread.authorize(credentials)
        # Open the selected spreadsheet
        spreadsheet = client.open_by_key(sheet_name_pivot)

        # Try to get the existing "Pivot Table" sheet
        try:
            pivot_sheet = spreadsheet.worksheet("Pivot Table")
        except gspread.exceptions.WorksheetNotFound:
            # If "Pivot Table" sheet doesn't exist, create a new one
            pivot_sheet = spreadsheet.add_worksheet("Pivot Table", 1000, 10)

        # Clear existing data in the "Pivot Table" sheet
        pivot_sheet.clear()
        
        # Apply formatting to the header row
        header_format = {
            "backgroundColor": {"red": 206 / 255, "green": 206 / 255, "blue": 206 / 255},
            "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}, "bold": True},
            "horizontalAlignment": "CENTER"

        }
        pivot_sheet.format("A1:C1", header_format)
        # Set the headers
        pivot_sheet.update_cell(1, 1, "Category Name")
        pivot_sheet.update_cell(1, 2, "Sum Of Credits")
        pivot_sheet.update_cell(1, 3, "Sum Of Debits")

        
        # Get the data from the specified columns
        category_column = getColumnValues(spreadsheet, cat_column_letter)
        credits_column = getColumnValues(spreadsheet, credit_column_name)
        debits_column = getColumnValues(spreadsheet, debit_column_name)

        # Create a unique set of category names
        unique_categories = list(set(category_column))

        # Iterate over unique categories and calculate the sum of credits and debits
        for category in unique_categories:
            sum_credits = calculateSumByCategory(category, category_column, credits_column)
            sum_debits = calculateSumByCategory(category, category_column, debits_column)

            # Find the next available row in the "Pivot Table" sheet
            next_row = len(pivot_sheet.col_values(1)) + 1

            # Set the values in the "Pivot Table" sheet
            pivot_sheet.update_cell(next_row, 1, category)
            pivot_sheet.update_cell(next_row, 2, sum_credits)
            pivot_sheet.update_cell(next_row, 3, sum_debits)

        # Add a footer with the total count of each category and the sum of credits and debits
        last_row = len(pivot_sheet.col_values(1))
        footer_format = {
            "backgroundColor": {"red": 0 / 255, "green": 58 / 255, "blue": 5 / 255},
            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True},
            "horizontalAlignment": "CENTER"
        }
        pivot_sheet.format(f"A{last_row + 1}:C{last_row + 2}", footer_format)
        
        pivot_sheet.update_cell(last_row + 1, 1, "Total Category")
        pivot_sheet.update_cell(last_row + 2, 1, f"=COUNTA(A2:A{last_row})")
        pivot_sheet.update_cell(last_row + 1, 2, "Total Credits")
        pivot_sheet.update_cell(last_row + 2, 2, f"=SUM(B2:B{last_row})")
        pivot_sheet.update_cell(last_row + 1, 3, "Total Debits")
        pivot_sheet.update_cell(last_row + 2, 3, f"=SUM(C2:C{last_row})")




        # Return success message with sheet name
        success_message = f"For Sheet: '{sheet_name_pivot}', Pivot Table Created Successfully!"
        return success_message    
    except Exception as e:
        print('Error in pivotformtable:', e)
        raise e
    
    
def format_cell_range(sheet, row_start, col_start, row_end, col_end, format_params):
    cell_range = sheet.range(row_start, col_start, row_end, col_end)
    for cell in cell_range:
        for key, value in format_params.items():
            setattr(cell, key, value)
    sheet.update_cells(cell_range)

def getColumnValues(spreadsheet, column_letter):
    sheet = spreadsheet.sheet1
    last_row = len(sheet.col_values(ord(column_letter) - 64)) + 1

    # Get the values in the specified column
    column_values = sheet.col_values(ord(column_letter) - 64)[1:last_row]

    return column_values

def calculateSumByCategory(category, category_column, values_column):
    sum_value = 0

    # Iterate over the category_column and values_column to calculate the sum
    for i in range(len(category_column)):
        if category_column[i] == category and values_column[i]:  # Check if the value is not empty
            sum_value += float(values_column[i])  # Convert to float for numerical calculations

    return sum_value

def pivot_table(request):
    try:
        print("Fetching data from Google Sheets For Pivot.")

        # Get credentials and create Google Drive service
        CLIENT_SECRET_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')
        API_NAME = 'drive'
        API_VERSION = 'v3'
        DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

        drive_service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, DRIVE_SCOPES)
        
        # Get the selected sheet ID (Google Sheets file ID) from the form
        pivot_sheet_id = request.POST.get('pivot_sheetid')  # Assuming the dropdown ID for form2 is 'fileDropdown2'
        if not pivot_sheet_id:
            raise ValueError("Sheet ID is required.")

        # Call the Drive API to fetch the content of the Google Sheets file
        sheet_file = drive_service.files().get(fileId=pivot_sheet_id, fields='name').execute()
        sheet_name = sheet_file.get('name')


        # Now, you have the name of the Google Sheets file, you can use it to access the data within the file

        # Get other form data
        credits_column = request.POST.get('credits_column')
        debits_column = request.POST.get('debits_column')
        cat_column = request.POST.get('cat_column')
        

        if not all([credits_column, debits_column, cat_column]):
            raise ValueError("Required form data is missing in pivot form.")

        
        success_message = pivotformtable(pivot_sheet_id, credits_column, debits_column, cat_column)  
        # Store the success message in the session
        request.session['success_message'] = success_message

        return redirect('/')
    
    except Exception as e:
        error_message = str(e)
        # Store the error message in the session
        request.session['error_message'] = error_message
        # Redirect to the homepage ('/')
        return redirect('/')


