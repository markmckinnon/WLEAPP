import os
import sqlite3

from scripts.generalfunctions import logfunc, tsv_output, csv_output, jsonl_output, get_column_headings, open_sqlite_db_readonly, binary_sid_to_string

def get_installed_program_metro_history(files_found, report_folder, seeker, output_type):
    
    for file_found in files_found:
        file_found = str(file_found)
        if not os.path.basename(file_found).lower() == 'staterepository-machine.srd': # skip -journal and other files
            continue

        sql_statement = '''
             Select userSid, 
                    (Select PackageFullName from PackageIdentity where PackageIdentity._PackageIdentityID = DeploymentHistory.PackageIdentity) PkgFullName,
                    ((WhenOccurred / 10000000) - 11644473600) when_occurred
               from DeploymentHistory, user
              where _UserId = User;'''
        
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute(sql_statement)

        all_rows = cursor.fetchall()
        usage_entries = len(all_rows)
        if usage_entries > 0:
            data_headers = ('user_sid', 'full_package_name', 'install_time')
            data_list = []
            for row in all_rows:
                data_list.append((binary_sid_to_string(row[0]), row[1], row[2]))
            
            file_name = f'Metro Installed Programs History'

            if 'tsv' in output_type:
                tsv_output(report_folder, data_headers, data_list, file_name)

            if 'csv' in output_type:
                csv_output(report_folder, data_headers, data_list, file_name)

            if 'jsonl' in output_type:
                jsonl_output(report_folder, data_headers, data_list, file_name)
            
        else:
            logfunc(f'No Metro Installed Program History data available')
        
        db.close()