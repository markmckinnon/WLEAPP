#!/usr/bin/env python3
#import json
#import datetime
#import os
from Registry import Registry
import struct

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline

def processSYSTEMHive(systemHive, win_parms):
    bam_record = []
    systemRegFile = Registry.Registry(systemHive)
    control_set = win_parms.get_control_set()
    try:
        currentKey = systemRegFile.open(win_parms.get_control_set() + '\\services\\bam\\UserSettings')
    except:
        currentKey = systemRegFile.open(win_parms.get_control_set() + '\\services\\bam\\State\\UserSettings')
    # Print information about its subkeys.
    for sk in currentKey.subkeys():
        if sk.values_number() > 0:
            registry_key = sk.name()
            sk_values = sk.values()
            for sk_value in sk_values:
                if sk_value.name() == 'SequenceNumber' or sk_value.name() == 'Version':
                    pass
                else:
                    ind_record = []
                    msTime = struct.unpack('<qqq', sk_value.raw_data())[0]
                    linuxTime = int(str(msTime)[0:11]) - 11644473600
                    u_id = registry_key[registry_key.rfind("-") + 1:]
                    if u_id in win_parms.get_user_sids().keys():
                        ind_record.append(win_parms.get_user_sid(u_id))
                    else:
                        ind_record.append(registry_key)

                    ind_record.append(str(sk_value.name()))
                    ind_record.append(str(linuxTime))
                    bam_record.append(ind_record)
    return bam_record

def get_bam(files_found, report_folder, seeker, wrap_text, win_parms):
    
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        # Find an existing key.
        data_list = processSYSTEMHive(file_found, win_parms)
        num_entries = len(data_list)
        if num_entries > 0:
            report = ArtifactHtmlReport('BAM Program Execution')
            report.start_artifact_report(report_folder, 'BAM Program Execution')
            report.add_script()
            data_headers = ('user_name', 'program_name', 'last run time')

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'BAM Program Execution'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = f'BAM Program Execution'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No BAM Program Execution data available')

