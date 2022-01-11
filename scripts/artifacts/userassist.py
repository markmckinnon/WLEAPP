#!/usr/bin/env python3
#import json
#import datetime
#import os
from Registry import Registry
import struct
import codecs

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline


def processUserHive(systemHive, win_parms):
    services_record = []
    systemRegFile = Registry.Registry(systemHive)
    control_set = win_parms.get_control_set()
    try:
        currentKey = systemRegFile.open('Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist')
    except:
        return
    # Print information about its subkeys.
    for sk in currentKey.subkeys():
        version = 0
        guids = sk.subkeys()
        for guid in guids:
            sk_values = sk.values()
            for sk_value in sk_values:
                if sk_value.name() == 'Version':
                    version = sk_value.raw_data()
            


    return services_record

def get_userassist(files_found, report_folder, seeker, wrap_text, win_parms):
    
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        # Find an existing key.
        data_list = processUserHive(file_found, win_parms)
        num_entries = len(data_list)
        if num_entries > 0:
            report = ArtifactHtmlReport('Registry User Assist')
            report.start_artifact_report(report_folder, 'Rgistry User Assist')
            report.add_script()
            data_headers = ('Name', 'display name', 'image path', 'type', 'start', 'group', 'last modified')

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Windows Services'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = f'SAM Information'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No SAM Information data available')

