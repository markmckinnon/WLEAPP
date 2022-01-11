#!/usr/bin/env python3
import json
import datetime
import os
import pyscca

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows

def get_prefetch(files_found, report_folder, seeker, wrap_text, win_parms):
    
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        if not '.pf' in os.path.basename(file_found):   # skip -Non prefetch files
            continue
           
        prefetchRecord = []
        try:
            scca = pyscca.open(file_found)
            #print("File Name is ==> " + file_found)
            prefetchRecord.append(file_found)
            prefetchRecord.append(scca.get_executable_filename())
            prefetchExecutableFileName = scca.get_executable_filename()
            prefetchExecutableFilePath = ""
            prefetchExecutablePath = ""
            try:
                if scca.get_run_count() is None:
                    prefetchRecord.append(0)
                else:
                    prefetchRecord.append(scca.get_run_count())
            except:
                prefetchRecord.append(0)
            #print ("Run Count ==> " + str(scca.get_run_count()))
            for i in range(8):
                try:
                    if scca.get_last_run_time_as_integer(i) is None or scca.get_last_run_time_as_integer(i) == 0:
                        prefetchRecord.append(0)
                    else:
                        prefetchRecord.append(int(str(scca.get_last_run_time_as_integer(i))[:11]) - 11644473600)
                        #print ("Last Run Tine ==> " + str(scca.get_last_run_time_as_integer(i)))
                except:
                    prefetchRecord.append(0)
                    #print ("Last Run time ==> 0")
            #print (scca.get_number_of_file_metrics_entries)
            #prefetchRecord.append(scca.get_prefetch_hash)
            data_list.append(prefetchRecord)
        except:
            print ("Error reading prefetch file")

    num_entries = len(data_list)
    if num_entries > 0:
        report = ArtifactHtmlReport('Basic Prefetch Information')
        report.start_artifact_report(report_folder, 'Basic Prefetch Information')
        report.add_script()
        data_headers = ('Prefetch File Name','Executable File Name','Run Count','Time 1', 'Time 2', 'Time 3', 'Time 4', 'Time 5', 'Time 6', 'Time 7', 'Time 8') 
        
        report.write_artifact_data_table(data_headers, data_list, file_found)
        report.end_artifact_report()
        
        tsvname = f'Basic Prefetch Information'
        tsv(report_folder, data_headers, data_list, tsvname)
        
        tlactivity = f'Basic Prefetch Information'
        timeline(report_folder, tlactivity, data_list, data_headers)
    else:
        logfunc('No Basic Prefetch Information data available')
        
    