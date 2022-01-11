#!/usr/bin/env python3
#import json
#import datetime
#import os
from Registry import Registry
import struct

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline

typeDict = {1: 'Kernel driver',
             2: 'File system driver',
             16: 'Own_Process',
             32: 'Share_Process',
             256: 'Interactive'}

startDict = {0: 'Boot Start',
             1: 'System Start',
             2: 'Auto Start',
             3: 'Manual',
             4: 'Disabled'}

def processSYSTEMHive(systemHive, win_parms):
    services_record = []
    systemRegFile = Registry.Registry(systemHive)
    control_set = win_parms.get_control_set()
    try:
        currentKey = systemRegFile.open(win_parms.get_control_set() + '\\services')
    except:
        currentKey = systemRegFile.open(win_parms.get_control_set() + '\\services')
    # Print information about its subkeys.
    for sk in currentKey.subkeys():
        if sk.values_number() > 0:
            sk_values = sk.values()
            type = 0
            start = 0
            name = sk.name()
            imagePath = ""
            displayName = ""
            group = ""
            lastModified = sk.timestamp()
            ind_record = []
            for sk_value in sk_values:
                if sk_value.name() == 'Group':
                    group = sk_value.value()
                if sk_value.name() == 'ImagePath':
                    imagePath = sk_value.value()
                if sk_value.name() == 'Type':
                    type = sk_value.value()
                if sk_value.name() == 'Start':
                    start = sk_value.value()
                if sk_value.name() == 'DisplayName':
                    displayName = sk_value.value()

            ind_record.append(name)
            ind_record.append(displayName)
            ind_record.append(imagePath)
            ind_record.append(typeDict.get(type, "Unknown"))
            ind_record.append(startDict.get(type, "Unknown"))
            ind_record.append(group)
            ind_record.append(lastModified)
            services_record.append(ind_record)
    return services_record

def get_services(files_found, report_folder, seeker, wrap_text, win_parms):
    
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        # Find an existing key.
        data_list = processSYSTEMHive(file_found, win_parms)
        num_entries = len(data_list)
        if num_entries > 0:
            report = ArtifactHtmlReport('Windows Services')
            report.start_artifact_report(report_folder, 'Windows Services')
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

