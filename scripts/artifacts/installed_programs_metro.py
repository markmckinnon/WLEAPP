import os
import sqlite3


from scripts.generalfunctions import logfunc, tsv_output, csv_output, jsonl_output, get_column_headings, open_sqlite_db_readonly, binary_sid_to_string

def get_installed_program_metro(files_found, report_folder, seeker, output_type):
    
    for file_found in files_found:
        file_found = str(file_found)
        if not os.path.basename(file_found).lower() == 'staterepository-machine.srd': # skip -journal and other files
            continue

        sql_statement = '''Select substr(packfam.PackageFamilyName, instr(packfam.PackageFamilyName, '.') + 1, instr(packfam.PackageFamilyName, '_') - 2 - instr(packfam.PackageFamilyName, '.') + 1) AppName,
              datetime(substr(packuser.installTime,1,11) - 11644473600, 'unixepoch') installTime,
              Case when instr(lower(pack.PublisherDisplayName), 'ms-resource') = 0 then pack.PublisherDisplayName
                   else '' end PublisherDIsplayName,
              packfam.publisherid, userkey.Usersid,
             case Architecture when 0 then 'X64'
                               when 9 then 'x86'
                               when 11 then 'Neutral'
                               else Architecture
             end Architecture,
             substr(pack.packageFullName, instr(pack.packageFullName, '_') + 1, instr(substr(pack.packageFullName, instr(pack.packageFullName, '_') + 1), '_') - 1)  version,
             case SignatureOrigin when 3 then 'System'
                                  when 2 then 'Store'
                                  else 'Unknown'
             end SignatureKind,
             packloc.installedLocation
        from PackageUser packuser, package pack, packageFamily packfam, packageLocation packloc, User userKey
        where packuser.package = pack._PackageId
          and pack.packageFamily = packfam._PackagefamilyId
          and packuser.user = userkey._UserId
          and packloc.package = pack._packageId
          and (pack.resourceId is null or pack.resourceId = 'neutral');'''
        
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute(sql_statement)

        all_rows = cursor.fetchall()
        usage_entries = len(all_rows)
        if usage_entries > 0:
            data_headers = ('application_name', 'install_time', 'publisher_display_name', 'publisher_id', 'user_sid', 'architecture', 'version', 'signature_kind', 'installed_location')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], binary_sid_to_string(row[4]), row[5], row[6], row[7], row[8]))
            
            file_name = f'Metro Installed Programs'

            if 'tsv' in output_type:
                tsv_output(report_folder, data_headers, data_list, file_name)

            if 'csv' in output_type:
                csv_output(report_folder, data_headers, data_list, file_name)

            if 'jsonl' in output_type:
                jsonl_output(report_folder, data_headers, data_list, file_name)
            
        else:
            logfunc(f'No Metro Installed Program data available')
        
        db.close()