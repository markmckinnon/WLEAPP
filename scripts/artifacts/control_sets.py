#!/usr/bin/env python3
#import json
#import datetime
#import os
from Registry import Registry
import struct

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline


def processControlSet(systemHive, win_parms):
    control_set_record = []
    systemRegFile = Registry.Registry(systemHive)
    currentKey = systemRegFile.open('Select')
    # Print information about its subkeys.
    for sk in currentKey.values():
        temp_list = []
        if sk.name() == "Current":
            control_set_number = sk.value()
            win_parms.set_control_set(control_set_number)
            temp_list.append(sk.name())
            temp_list.append(control_set_number)
        else:
            temp_list.append(sk.name())
            temp_list.append(sk.value())
        control_set_record.append(temp_list)
    control_set = win_parms.get_control_set()
    return control_set_record

def get_control_sets(files_found, report_folder, seeker, wrap_text, win_parms):
    
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        # Find an existing key.
        data_list = processControlSet(file_found, win_parms)
        num_entries = len(data_list)
        if num_entries > 0:
            report = ArtifactHtmlReport('Control Sets')
            report.start_artifact_report(report_folder, 'Control Sets')
            report.add_script()
            data_headers = ('Control Set', 'Control Set Number')

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Control Sets'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Control Sets'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Control Set Information data available')

