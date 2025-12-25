import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

json_dict = {
    "type": "service_account",
    "project_id": "grofers-331605",
    "private_key_id": "1bf05a90aefb8e723f0d7ea0442e82e9fec3a7e9",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDegQYjuR7dY829\nmy1egLluKxt+nHWXK5DWW6vCijyKwM8/Ph9o7zBrCOIkpzt06GIBwVrevWLP78AA\nQjOl+b4Q4/Vt0AGpqdyKx/VaRaHDtcuSVOSlFQOZ5fu9A+G+vmuloILcPKdHsnuu\nUa65Cyscpqwpn4EiWXt9Vh6cnc2j8KX4CSQFvmQAJZJQ+uJ5N7Oytjgn9HBk9GPy\nwSQMLfHve3iV/yzUjjYyXEhDixUNdokvfhYkY7c6wv/b7Zql0vEqAumxhHjle/pq\ntHOHZlIIRdusqw0C+seJo/CbfdX3DoTIesJvkIciqKHVIBm1TFKHacJKzzzhSZlH\n+oN9gnJtAgMBAAECggEAAPKQNeE72X9WDjS7C/q6L2xVZ46KLVIKbHCYqeaq93/2\n3KMAARNPA7mr4DI/yCbq2e06nOsLYMLO22wXamFxTC2dqzF2Ua8PPnO3tAIgEaRf\nIPj7E0fkYMilr9+fG7qVse9zIeB2lDvVQoAHDDMuZGbCTMK+NZ5SGWMfP2qoSEaD\n9LbwnQ850m8fgyHKTXxDXWVjOT8milntTcyZjVLV27Hva7jKLfBt2VR8yU0GDCwF\nB4W+xMp70VjGWUNNMoGsq0uFavtCcLTnrnYcXyB5I9Fvnqdu6uI4KvzgLr6izdSH\nNa38I17XNEh0fCwNCvip1QGsntsxB/SR+e+NuQQAUQKBgQDu0AaAzxNM9K2AEa9m\noy6Y/lOkWK+PGbWmhMLLu01jY+oAsHLiY+79hYsYFTgjUG/qlOdfTMBZka6OhPyP\nXPMzk7mNM0BDJ1EQHgsiG4RBiOaT+eG+K4M/o4DFsyqrG34MjS3gE8w2chauUYA3\nOGIX2Q5QV8+YKEICR1X9cGZaUQKBgQDuhIXQiyE5JL6s4dYN5ApP1nm0oeb6Dx26\nZNUggg4tlyW7yOs+iNSeVTaYQhExATnNk4icg3mHjXnt+th3eLDMNxigSzG05RCl\nUdIPsZYkt2j39uxAj/IYLpArLeZFaeXk0PIWPdJPz9dXw6YbzEzxEM6Z5lQ2viJ7\ntSsRHB2zXQKBgFP3msHBjXS6dyKXlUeOSr0Kd1hKwnebP45sEZ3WnpA6ujVB1TMa\nlhZX1R9Dnrhz+NXPQ0bz0pHrsid0ROUXdn+FCnHGOmsiMNNs7NcyO59bRk9zRdc6\nr2w5zfY1V+RPx1McdKvb6iqelLD4AQ/paDwgWnMPXPOP/B2W/XoeAi7xAoGBAL6G\nQVXKLSm2PlFevFuwMsR/cAxn31cTyA1iChTDjovAVrXf0nnLVvt62fdZnt3kOsYJ\n+W/8XZF341PDsjIMyDz4LcWtCvGSoG9OIlvC4UpG76RTK3iPAzVpzGORcIU2CBt1\nBEvb6ikyvrMuZ3uBAFz3rfClWdO4oVbr6pDqQpdJAoGAMTWZ4/DmT2FNgdo+rM8M\nQoGdD4JM34Fsgo9y4hyQkltyCWblhGyzGpU2GzdZ8C88oiU32sJ4oNGwkj6L4TJe\nxn8rb11eEirO7MkHZnREtay0MTQoY906ARPUDLZK8mMX9MWsc7iTlh3pIxGAcN0X\nwymMh9Ck6et3kCZ1JT7WqSI=\n-----END PRIVATE KEY-----\n",
    "client_email": "grofers-service-account@grofers-331605.iam.gserviceaccount.com",
    "client_id": "103272509230355853672",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/grofers-service-account%40grofers-331605.iam.gserviceaccount.com"
}


# Define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)

# Authorize the clientsheet
client = gspread.authorize(creds)


def append_sheet(data, hyperlink_dic=None, sheet_name=None, spreadsheet_key=None):
    """
    Appends a row to the end of the worksheet and adds hyperlinks to specified cells.

    :param data: A list of values to append. For cells with hyperlinks, this should be the link text.
    :param hyperlink_dic: A dictionary where each key is the index of a cell in the row (0-based)
                              and the corresponding value is a tuple (url, link_label).
                              For example, {1: ('http://example.com', 'Example')} means the cell
                              in column 2 will be a hyperlink to http://example.com with display text 'Example'.
    """

    if spreadsheet_key is None or sheet_name is None:
        raise Exception('spreadsheet_key and sheet_name is mandatory')
    # Open the spreadhseet
    spreadsheet = client.open_by_key(spreadsheet_key)
    sheet = spreadsheet.worksheet(sheet_name)
    # # Find the number of rows in the worksheet
    # num_rows = len(workshsheeteet.get_all_values())
    # # The next empty row is one more than the number of filled rows
    # next_row = num_rows + 1
    # Append the data
    sheet.append_row(data)
    if hyperlink_dic is not None:
        _append_row_with_hyperlinks(sheet, hyperlink_dic)


def _append_row_with_hyperlinks(worksheet, hyperlink_indices):
    """
    Appends a row to the end of the worksheet and adds hyperlinks to specified cells.

    :param worksheet: The gspread worksheet object to append the row to.
    :param data: A list of values to append. For cells with hyperlinks, this should be the link text.
    :param hyperlink_indices: A dictionary where each key is the index of a cell in the row (0-based)
                              and the corresponding value is a tuple (url, link_label).
                              For example, {1: ('http://example.com', 'Example')} means the cell
                              in column 2 will be a hyperlink to http://example.com with display text 'Example'.
    """

    row_number = len(worksheet.get_all_values())
    # Prepare a batch update for hyperlinks
    requests = []
    for col_index, (url, link_label) in hyperlink_indices.items():
        # gspread is 1-indexed, so add 1 to the column index
        cell_address = gspread.utils.rowcol_to_a1(row_number, col_index + 1)
        formula = f"=HYPERLINK(\"{url}\", \"{link_label}\")"
        requests.append({
            'range': cell_address,
            'values': [[formula]]
        })

    # Execute the batch update for hyperlinks
    if requests:
        worksheet.batch_update(requests, value_input_option='USER_ENTERED')
