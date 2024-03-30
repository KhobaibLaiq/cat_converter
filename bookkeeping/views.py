from django.shortcuts import render, redirect
from django.http import JsonResponse
from .Google import Create_Service
from cat_converter import settings
import os
import gspread
import pickle
import json

def index(request):
    # Retrieve success_message and error_message from the session (if they exist)
    success_message = request.session.pop('success_message', None)
    error_message = request.session.pop('error_message', None)
    return render(request, 'cat_index.html', {'success_message': success_message, 'error_message': error_message})

def check_search_library(request):
    try:
        # Load JSON data from the request body
        data = json.loads(request.body)
        search_data = data.get('searchData')
        print("Received search data:", search_data)  # Debug statement to check received data

        # Load credentials from token_drive_v3.pickle
        credentials_path = 'token_drive_v3.pickle'
        with open(credentials_path, 'rb') as token:
            credentials = pickle.load(token)

        # Authorize the client using the loaded credentials
        gc = gspread.authorize(credentials)

        # Open the spreadsheet
        worksheet = gc.open("search_library").sheet1

        # Search for the data in the first column
        cell = worksheet.find(search_data)

        # If found, return the corresponding data from the second column
        if cell:
            category_data = worksheet.cell(cell.row, 2).value
            print("Found category data:", category_data)  # Debug statement to check found data
            return JsonResponse({'categoryData': category_data})
        else:
            print("Category data not found")  # Debug statement for not found data
            return JsonResponse({'categoryData': None})

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        return JsonResponse({'categoryData': None})

    except Exception as e:
        print('Error:', e)  # Log any errors that occur
        return JsonResponse({'categoryData': None})


def list_files_and_folders(request):
    try:
        print("Listing files and folders from Google Drive.")
        # Get credentials and create Google Drive service
        CLIENT_SECRET_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')
        API_NAME = 'drive'
        API_VERSION = 'v3'
        SCOPES = ["https://www.googleapis.com/auth/drive"]

        service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

        folder = request.GET.get('folder_id', 'root')

        if folder == 'root':
            query = f"'{folder}' in parents"
        else:
            query = f"parents= '{folder}'"

        response = service.files().list(q=query).execute()
        items = response.get('files')

        # Extract relevant information (file names) from the response
        file_data = [[item['id'], item['name'], 'folder' if 'folder' in item['mimeType'] else 'file'] for item in items if
                     item['mimeType'] == 'application/vnd.google-apps.spreadsheet']

        return JsonResponse({'files': file_data})

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def letter_to_index(letter):
    """Converts a column letter to its corresponding index (1-based)."""
    return ord(letter.upper()) - 64  # Convert ASCII value to 1-based index

def update_or_add_data_to_search_library(search_data, new_data):
    try:
        # Load credentials from token_drive_v3.pickle
        credentials_path = 'token_drive_v3.pickle'
        with open(credentials_path, 'rb') as token:
            credentials = pickle.load(token)

        # Authorize the client using the loaded credentials
        client = gspread.authorize(credentials)

        # Open the search_library spreadsheet
        search_library_spreadsheet = client.open('search_library')
        search_library_sheet = search_library_spreadsheet.sheet1

        print("Search Library Sheet opened successfully.")  # Debugging statement

        # Convert search_data to lowercase
        search_data_lower = search_data.lower()

        print("Search data converted to lowercase:", search_data_lower)  # Debugging statement

        # Search for search_data in column A (case-insensitive)
        search_data_values = search_library_sheet.col_values(1)
        print("Search data values:", search_data_values)  # Debugging statement

        search_data_found_index = next((i for i, val in enumerate(search_data_values) if val.lower() == search_data_lower), -1)

        print("Search data found index:", search_data_found_index)  # Debugging statement

        # If search_data is found, update the corresponding row in column B
        if search_data_found_index != -1:
            search_library_sheet.update_cell(search_data_found_index + 1, 2, new_data)
            print(f"Updated existing entry for search_data: '{search_data}'")
        else:
            # If search_data is not found, add a new row with search_data in column A and new_data in column B
            last_row_search_library = len(search_data_values) + 1
            search_library_sheet.update_cell(last_row_search_library, 1, search_data)
            search_library_sheet.update_cell(last_row_search_library, 2, new_data)
            print(f"Added new entry for search_data: '{search_data}'")
            
    except Exception as e:
        # Log and rethrow any errors that occur during updating or adding to search library
        print('Error in update_or_add_data_to_search_library:', e)
        raise e

def getNextEmptyColumn(target_sheet, row, start_column_index, new_data, new_data_color, replace_data_color):
    """Add the new data to the specified column in the row if it's empty."""
    cell_value = target_sheet.cell(row, start_column_index).value
    if not cell_value:
        # If the cell is empty, add the new data
        target_sheet.update_cell(row, start_column_index, new_data)
        print(f"Added '{new_data}' to row {row} in column {start_column_index}")

        # Convert hex color to RGB triplet
        rgb_color = hex_to_rgb(new_data_color)
        # Apply background color to the cell
        cell_range_new_not_overwrite = gspread.utils.rowcol_to_a1(row, start_column_index)
        target_sheet.format(cell_range_new_not_overwrite, {
            "backgroundColor": {
                "red": rgb_color[0] / 255,
                "green": rgb_color[1] / 255,
                "blue": rgb_color[2] / 255
            }
        })
        print(f"Background color applied to cell: {cell_range_new_not_overwrite}")

    else:
        # If the cell is not empty, find the next empty column
        for col_index in range(start_column_index + 1, len(target_sheet.row_values(row)) + 2):
            cell_value = target_sheet.cell(row, col_index).value
            if not cell_value:
                # Found an empty cell, add the new data
                target_sheet.update_cell(row, col_index, new_data)
                print(f"Added '{new_data}' to row {row} in column {col_index} (appended)")

                # Convert hex color to RGB triplet
                rgb_color = hex_to_rgb(new_data_color)
                # Apply background color to the cell
                cell_range_new_not_empty_overwrite = gspread.utils.rowcol_to_a1(row, col_index)
                target_sheet.format(cell_range_new_not_empty_overwrite, {
                    "backgroundColor": {
                        "red": rgb_color[0] / 255,
                        "green": rgb_color[1] / 255,
                        "blue": rgb_color[2] / 255
                    }
                })
                print(f"Background color applied to cell: {cell_range_new_not_empty_overwrite}")

                break
        else:
            # If no empty cell found, add the new data in a new cell
            new_column_index = len(target_sheet.row_values(row)) + 1
            target_sheet.update_cell(row, new_column_index, new_data)

            # Convert hex color to RGB triplet
            rgb_color = hex_to_rgb(replace_data_color)
            # Apply background color to the cell
            cell_range_replace_not_empty_overwrite = gspread.utils.rowcol_to_a1(row, new_column_index)
            target_sheet.format(cell_range_replace_not_empty_overwrite, {
                "backgroundColor": {
                    "red": rgb_color[0] / 255,
                    "green": rgb_color[1] / 255,
                    "blue": rgb_color[2] / 255
                }

            })
            print(f"Background color applied to cell: {cell_range_replace_not_empty_overwrite}")

            print(f"Added '{new_data}' to row {row} in a new column")



        
def hex_to_rgb(hex_color):
    """Converts a color in hexadecimal format to RGB triplet."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def on_form_fill(sheet_name, search_column_input, search_data, target_column_input, overwrite_checkbox, new_data,
                 new_data_color, library_checkbox, replace_data_color):
    try:


        # Load credentials from token_drive_v3.pickle
        credentials_path = 'token_drive_v3.pickle'
        with open(credentials_path, 'rb') as token:
            credentials = pickle.load(token)

        # Authorize the client using the loaded credentials
        client = gspread.authorize(credentials)

        # Open the Google Sheets document
        spreadsheet = client.open(sheet_name)
        target_sheet = spreadsheet.sheet1  # Assuming the first sheet is the target sheet
        if library_checkbox:
            update_or_add_data_to_search_library(search_data, new_data)

        # Convert column letter to index
        search_column_index = letter_to_index(search_column_input)
        target_column_index = letter_to_index(target_column_input)
        
        # Get all values from the column, skipping the first row
        values_list = target_sheet.col_values(search_column_index)

        # Perform case-insensitive search for search_data in values_list
        found_indices = [i + 1 for i, value in enumerate(values_list) if search_data.lower() in value.lower()]
        if found_indices:
            print("Found at indices:", found_indices)

            # Add new_data to the rows corresponding to found_indices in target_column_input
            for index in found_indices:
                if overwrite_checkbox:
                    cell_value = target_sheet.cell(index, target_column_index).value
                    if not cell_value:
                        target_sheet.update_cell(index, target_column_index, new_data)

                        # Convert hex color to RGB triplet
                        rgb_color = hex_to_rgb(new_data_color)
                        # Apply background color to the cell
                        cell_range_new = gspread.utils.rowcol_to_a1(index, target_column_index)
                        target_sheet.format(cell_range_new, {
                            "backgroundColor": {
                                "red": rgb_color[0] / 255,
                                "green": rgb_color[1] / 255,
                                "blue": rgb_color[2] / 255
                            }
                        })
                    else:
                        target_sheet.update_cell(index, target_column_index, new_data)

                        # Convert hex color to RGB triplet
                        rgb_color = hex_to_rgb(replace_data_color)
                        # Apply background color to the cell
                        cell_range_replace_color = gspread.utils.rowcol_to_a1(index, target_column_index)
                        target_sheet.format(cell_range_replace_color, {
                            "backgroundColor": {
                                "red": rgb_color[0] / 255,
                                "green": rgb_color[1] / 255,
                                "blue": rgb_color[2] / 255
                            }
                        })

                else:
                    getNextEmptyColumn(target_sheet, index, target_column_index, new_data, new_data_color,
                                       replace_data_color)
            
            # Return success message with sheet name
            success_message = f"Form Data Processed Successfully For : {sheet_name}"
            return success_message

        
    except Exception as e:
        error_message = f"An error occurred during form submission: {e}"
        print(error_message)
        raise e

    


def get_data(request):
    try:
        print("Fetching data from Google Sheets.")

        # Get credentials and create Google Drive service
        CLIENT_SECRET_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')
        API_NAME = 'drive'
        API_VERSION = 'v3'
        DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

        drive_service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, DRIVE_SCOPES)

        # Get the selected sheet ID (Google Sheets file ID) from the form
        selected_sheet_id = request.POST.get('sheetid')
        if not selected_sheet_id:
            raise ValueError("Sheet ID is required.")

        # Call the Drive API to fetch the content of the Google Sheets file
        sheet_file = drive_service.files().get(fileId=selected_sheet_id, fields='name').execute()
        sheet_name = sheet_file.get('name')

        print(f"Fetching data from Google Sheets file: {sheet_name}")

        # Now, you have the name of the Google Sheets file, you can use it to access the data within the file

        # Get other form data
        search_column = request.POST.get('searchColumnInput')
        search_data = request.POST.get('searchData')
        target_column_input = request.POST.get('targetColumnInput')
        new_data = request.POST.get('newData')
        new_data_color = request.POST.get('newDataColor')
        overwrite_checkbox = request.POST.get('OverwriteCheckbox')
        replace_data_color = request.POST.get('replaceDataColor')
        library_checkbox = request.POST.get('libraryCheckbox')

        if not all([search_column, search_data, target_column_input, new_data]):
            raise ValueError("Required form data is missing.")


        success_message = on_form_fill(sheet_name, search_column, search_data, target_column_input, overwrite_checkbox, new_data,
                     new_data_color, library_checkbox, replace_data_color)

         # Store the success message in the session
        request.session['success_message'] = success_message
        
        # Redirect to the homepage ('/')
        return redirect('/')
    
    except Exception as e:
        error_message = str(e)
        # Store the error message in the session
        request.session['error_message'] = error_message
        # Redirect to the homepage ('/')S
        return redirect('/')