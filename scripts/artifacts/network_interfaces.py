#!/usr/bin/env python3
from Registry import Registry
import struct

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline


def search_interfaces_subkey(subkey, subkey_name, win_parms):

    for curr_subkey in subkey.subkeys():
        if curr_subkey.subkeys_number() > 0:
           #print ("Next => " + curr_subkey.name())
           channelName = search_interfaces_subkey(curr_subkey, subkey_name)
           if channelName != None:
               sk1_values = curr_subkey.values()
               profileIndex = ""
               for sk1_value in sk1_values:
                   if sk1_value.name() == "ProfileIndex":
                       profileIndex = sk1_value.value()
                       win_parms.add_network_interface(profileIndex, channelName)
                       #interface_ids[str(profileIndex)] = str(channelName)
        else:
           #print ("last => " + curr_subkey.name())
           sk_values = curr_subkey.values()
           for sk_val in sk_values:
               if sk_val.name() == "Channel Hints":
                   channelhintraw = sk_val.raw_data()
                   hintlength = struct.unpack("I", channelhintraw[0:4])[0]
                   name = channelhintraw[4:hintlength+4]
                   #print ("channel Hint => " + str(name))
                   return name

def processNetworkInterfaces(hive_file, win_parms):

    # Find an existing key.
    try:
        hive = Registry.Registry(hive_file)
        key = hive.open('Microsoft\\WlanSvc\\Interfaces')
    except:
        return None
    # Find an existing key.

    search_interfaces_subkey(key, "METADATA", win_parms)
    print ("Stop Here")

def get_network_interfaces(files_found, report_folder, seeker, wrap_text, win_parms):
    
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        # Find an existing key.
        data_list = processNetworkInterfaces(file_found, win_parms)
        if data_list is None:
            logfunc('No Network Interfaces data available')
            return
        num_entries = len(data_list)
        if num_entries > 0:
            report = ArtifactHtmlReport('Network Interfaces Sets')
            report.start_artifact_report(report_folder, 'Control Sets')
            report.add_script()
            data_headers = ('profile Index', 'Channel name')

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Network Interfaces'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Network Interfaces'
            timeline(report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Control Set Information data available')

