import os
import sqlite3


from scripts.generalfunctions import logfunc, tsv_output, csv_output, jsonl_output, get_column_headings, open_sqlite_db_readonly

def get_windows_notifications(files_found, report_folder, seeker, output_type):
    
    notifications_db = ''
    
    for file_found in files_found:
        file_found = str(file_found)
        
        if os.path.basename(file_found).lower() == 'wpndatabase.db': # skip -journal and other files
            notifications_db = file_found
            
    db = open_sqlite_db_readonly(notifications_db)
    cursor = db.cursor()
            
    sql_statement = '''
             SELECT n.'Order', n.Id, n.Type, nh.PrimaryId AS HandlerPrimaryId, 
                    nh.CreatedTime AS HandlerCreatedTime, 
                    nh.ModifiedTime AS HandlerModifiedTime, cast(n.Payload as text) as payload,
                    CASE WHEN n.ExpiryTime != 0 
                         THEN datetime((n.ExpiryTime/10000000)-11644473600, 'unixepoch') 
                         ELSE n.ExpiryTime END AS ExpiryTime,
                    CASE WHEN n.ArrivalTime != 0 
                         THEN datetime((n.ArrivalTime/10000000)-11644473600, 'unixepoch') 
                         ELSE n.ArrivalTime END AS ArrivalTime
               FROM Notification n, 
                    NotificationHandler nh 
              where n.HandlerID = nh.RecordID;
              '''
        
    cursor.execute(sql_statement)

    all_rows = cursor.fetchall()
    usage_entries = len(all_rows)
    if usage_entries > 0:
        data_headers = ('Order', 'id', 'type', 'handler_primary_id', 'handler_created_time', 'handler_modified_time', 'payload', 'expiry_time', 'arrival_time')
        data_list = []
        for row in all_rows:
            data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], 
                              row[8]))
            
        file_name = f'Windows Notifications'

        if 'tsv' in output_type:
            tsv_output(report_folder, data_headers, data_list, file_name)

        if 'csv' in output_type:
            csv_output(report_folder, data_headers, data_list, file_name)

        if 'jsonl' in output_type:
            jsonl_output(report_folder, data_headers, data_list, file_name)
            
    else:
        logfunc(f'No Windows Notifications available')
                
    db.close()
    
