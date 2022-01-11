import os
import sqlite3


from scripts.generalfunctions import logfunc, tsv_output, csv_output, jsonl_output, get_column_headings, open_sqlite_db_readonly

def get_windows_activities_cache(files_found, report_folder, seeker, output_type):
    
    global_db = ''
    
    for file_found in files_found:
        file_found = str(file_found)
        
        if os.path.basename(file_found).lower() == 'activitiescache.db': # skip -journal and other files
            activitiescache_db = file_found

    db = open_sqlite_db_readonly(activitiescache_db)
    cursor = db.cursor()
            
    sql_statement = '''
             select hex(id) ID, appId, cast(Payload as Text) Payload, ActivityType, 
                    ActivityStatus, startTime, EndTime,
                    LastModifiedTime, ExpirationTime, createdInCloud, 
                    LastModifiedOnClient, OriginalLastModifiedOnClient, isLocalOnly, 
                    Etag, packageIdHash, PlatformDeviceId 
               from smartlookup;
           '''
        
    cursor.execute(sql_statement)

    all_rows = cursor.fetchall()
    usage_entries = len(all_rows)
    if usage_entries > 0:
        data_headers = ('id', 'app_id', 'payload', 'activity_type', 'activity_status', 'start_time', 'end_time', 'last_modified_time', 'Expiration_time', 'created_in_cloud', 'last_modified_on_client', 'original_last_modified_on_client', 'is_local_only', 'etag', 'package_id_hash', 'platform_device_id')
        data_list = []
        for row in all_rows:
            data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], 
                              row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15]))
            
        file_name = f'Windows Activities Cache'

        if 'tsv' in output_type:
            tsv_output(report_folder, data_headers, data_list, file_name)

        if 'csv' in output_type:
            csv_output(report_folder, data_headers, data_list, file_name)

        if 'jsonl' in output_type:
            jsonl_output(report_folder, data_headers, data_list, file_name)
            
    else:
        logfunc(f'No Windows Activities cache available')
                
    db.close()
    
