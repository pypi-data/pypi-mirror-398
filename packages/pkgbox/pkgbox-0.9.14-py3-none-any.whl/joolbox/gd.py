from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import re
from datetime import datetime
from datetime import timedelta
import io


scope = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform'
]
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

first_time_stamp = datetime.now() + timedelta(hours=5.5)

gauth = GoogleAuth()
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scopes=scope)

def run_folder_replacements(folder_id):
    new_folder = folder_id
    if(folder_id == '146i1OOUqlLwRt9uxuOJ_IY4MNhzOyHLi'):  # Jobs
        new_folder = '1X6L0RjJXq49aSmJR1P3aSP6xJw8A3AqY'
    if(folder_id == '1B3dyuFtN3PxNcqlXQJr4CyT0DGPT9YLx'):  # Alerts
        new_folder = '11FN-qqMcfxbNbA1s8WEDDpHgtP9UDScs'
    if(folder_id == '15lgDtar1j-TNczQP_HRjfxyFtdbBnMTp'):  # DN
        new_folder = '1nOpXhp4qZY4Yw_2dlL_pjXT4hVaaz1F0'
    if(folder_id == '1NwSsS1Hg93ozZBsYbk44cdln3unxhKKl'):  # PnLV6
        new_folder = '1IVV87SqggheQImEwIaz7ryf7bzaiw8Gl'
    if(folder_id == '1rdJKFfYBXmt3NWiqObRMBBrnBNFKSILn'):  # Transfer Loss
        new_folder = '1_zJR2tO401rtq4e49_tR19JEUBWG33BM'
    if(folder_id == '148r9xNGkNMBGQxof2PFzly86ehPTXRiE'):  # Queries
        new_folder = '126Lt9d19Mtf1MMMNqZ7JzTujmdUWY9fV'
    if(folder_id == '1-SWHTrU4o951ZURJDxk-FDQb2hJ5CbeO'):  # SQL
        new_folder = '1pZTrwu8RHd4vQZVO3Qb9OdBdIKrSYayy'
    return new_folder

def refresh_token():
    now = datetime.now() + timedelta(hours=5.5)
    if (now - first_time_stamp)/(1000 * 3600) > 0.5:
        return True
    else:
        return False

def drive(gauth=gauth):
    # if not gauth.credentials or not gauth.credentials.valid:
    if gauth.access_token_expired:
        gauth.Refresh()
    drive = GoogleDrive(gauth)
    return drive


def create_file(title=None, content=None, folder_id=None):
    '''creates a file in folder location by title'''
    if(title is None or folder_id is None):
        return
    folder_id = run_folder_replacements(folder_id)
    gfile = drive().CreateFile({
        'parents': [{'id': folder_id}],
        'title': title
    }
    )
    gfile.SetContentString(content)
    gfile.Upload()

def upload_file(title=None, path=None, folder_id=None):
    '''creates a file in folder location by title'''
    if(title is None or folder_id is None or path is None):
        return
    folder_id = run_folder_replacements(folder_id)
    gfile = drive().CreateFile({
        'parents': [{'id': folder_id}],
        'title': title
    }
    )
    gfile.SetContentFile(path)
    gfile.Upload()


def list_files(folder_id: str, filter_mime=None,
               sort_by='createdDate', ascending=True) -> list:
    '''List files in folder_id'''
    folder_id = run_folder_replacements(folder_id)
    file_list = drive().ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    final_file_list = []
    if(filter_mime is not None):
        for fl in file_list:
            if(fl['mimeType'] == filter_mime):
                final_file_list.append(fl)
    else:
        final_file_list = file_list
    final_file_list.sort(key=lambda r: r[sort_by], reverse=(not ascending))
    return final_file_list


def get_latest_excel_file_in_folder(folder_id):
    folder_id = run_folder_replacements(folder_id)
    gfile = list_files(folder_id, ascending=False, filter_mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file_name = gfile[0]['title']
    downloaded = drive().CreateFile({'id': gfile[0]['id']})
    downloaded.GetContentFile(file_name)
    return file_name


def get_file_by_name_in_gfolder(name, folder_id='126Lt9d19Mtf1MMMNqZ7JzTujmdUWY9fV'):  # folder id of queries folder
    folder_id = run_folder_replacements(folder_id)
    gfiles = list_files(folder_id, ascending=False)
    for gfile in gfiles:
        file_name = gfile['title']
        if(file_name == name):
            downloaded = drive().CreateFile({'id': gfile['id']})
            downloaded.GetContentFile(file_name)
            return file_name
    return None

def get_sql_gfolder(name, folder_id='126Lt9d19Mtf1MMMNqZ7JzTujmdUWY9fV'):  # folder id of queries folder
    folder_id = run_folder_replacements(folder_id)
    gfiles = list_files(folder_id, ascending=False)
    for gfile in gfiles:
        file_name = gfile['title']
        if(file_name == name):
            downloaded = drive().CreateFile({'id': gfile['id']})
            # downloaded.GetContentFile(file_name)
            content = downloaded.GetContentString(mimetype='text/plain')
            return content
    return None

def get_gdoc(name, folder_id='126Lt9d19Mtf1MMMNqZ7JzTujmdUWY9fV'):  # folder id of queries folder
    folder_id = run_folder_replacements(folder_id)
    download_mimetype = 'text/plain'
    gfile = list_files(folder_id, ascending=False)
    file_name = gfile[0]['title']
    if(file_name == name):
        downloaded = drive().CreateFile({'id': gfile[0]['id']})
        downloaded.GetContentFile(file_name, mimetype=download_mimetype)
        return file_name
    else:
        return None

def get_content_from_vault(name, folder_id='16Ge0xkyMqQli91I7HY-1EhhfsGUHuZH6'):  # folder id of vault
    folder_id = run_folder_replacements(folder_id)
    actual_mimetype = 'application/vnd.google-apps.document'
    download_mimetype = 'text/plain'
    gfiles = list_files(folder_id, ascending=False, filter_mime=actual_mimetype)
    for gfile in gfiles:
        file_name = gfile['title']
        if(file_name.lower() == name.lower()):
            downloaded = drive().CreateFile({'id': gfile['id']})
            content = downloaded.GetContentString(mimetype=download_mimetype)
            return content
        else:
            continue
    return None

def get_query_from_gdoc(query, doc=None, folder_id=None) -> str:

    if(folder_id is None):
        folder_id = '126Lt9d19Mtf1MMMNqZ7JzTujmdUWY9fV'

    folder_id = run_folder_replacements(folder_id)

    actual_mimetype = 'application/vnd.google-apps.document'
    download_mimetype = 'text/plain'
    gfiles = list_files(folder_id, ascending=False, filter_mime=actual_mimetype)
    # try:
    for gfile in gfiles:
        file_name = gfile['title']
        if(file_name == doc):
            downloaded = drive().CreateFile({'id': gfile['id']})
            # downloaded.GetContentFile(file_name, mimetype=download_mimetype, )
            content = downloaded.GetContentString(mimetype=download_mimetype)
            # print(content)
            # with open(file_name) as f:
            #     content = f.read()
            split_content = content.split('\n')
            for line in split_content:
                query_name_list = [m.group(1) for m in re.finditer(">([\w\W]*?)`sql`", line)]
                for x in query_name_list:
                    # print(x)
                    if x.strip().lower() == query.strip().lower():
                        query = x
                if query in query_name_list:
                    sql = content.split(f"{query}`sql`")[1]
                    sql_content = [m.group(1) for m in re.finditer("```([\w\W]*?)```", sql)][0]
                    # print(sql_content)
                    return sql_content
        else:
            continue
    # except():
    #     pass

    return ''

def update_txt_file(content, file_name=None, folder_id=None):
    # file_name = 'my_file.txt'
    if file_name is None:
        print('Filename not provided')
        return

    if folder_id is None:
        file_list = drive().ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    else:
        file_list = drive().ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    file_id = None
    for file in file_list:
        if file['title'] == file_name:
            file_id = file['id']
            break
    if file_id is None:
        print('File not found so creating the file')
        file = drive().CreateFile({'parents': [{'id': folder_id}], 'title': file_name})
        current_content = ""
    else:
        file = drive().CreateFile({'id': file_id})
        file.FetchMetadata(fetch_all=True)
        current_content = file.GetContentString(mimetype='text/plain')
    current_content = current_content + '\n' + content
    file.SetContentString(current_content)
    file.Upload()

def read_txt_file(file_name, folder_id=None):
    if folder_id is None:
        file_list = drive().ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    else:
        file_list = drive().ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    file_id = None
    for file in file_list:
        if file['title'] == file_name:
            file_id = file['id']
            break
    if file_id is None:
        print('File not found')
        return
    else:
        file = drive().CreateFile({'id': file_id})
        file.FetchMetadata(fetch_all=True)
        current_content = file.GetContentString(mimetype='text/plain')
        return current_content





# notebook = get_file_by_name_in_gfolder('BFAttribution.ipynb', folder_id='146i1OOUqlLwRt9uxuOJ_IY4MNhzOyHLi')
# print(notebook)