import os
import sqlite3
try:
    import pyesedb
    from Registry import Registry
except ImportError:
    pass
import struct
import math
import datetime

from scripts.generalfunctions import logfunc, tsv_output, csv_output, jsonl_output, get_column_headings, open_sqlite_db_readonly, binary_sid_to_string
from scripts.known_values import luid_interfaces, known_sids

user_ids = {}
interface_ids = {}
srudbidmap = {}
application_resource_usage = []
network_usage = []
network_connectivity = []
SruDbIdMapTable = []
application_resource_usage_data_header = []
network_usage_data_header = []
network_connectivity_data_header = []
SruDbIdMapTable_data_header = []

#  'SruDbIdMapTable':'SruDbIdMapTable'
#  '{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}':'Application_Resource_Usage'
#  '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}':'Energy_Usage_Data'
#  '{97C2CE28-A37B-4920-B1E9-8B76CD341EC5}':'Energy_Estimation_Provider'
#  '{973F5D5C-1D90-4944-BE8E-24B94231A174}':'Network_Usage',
#  '{D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}':'Windows_Push_Notification'
#  '{DD6636C4-8929-4683-974E-22C046A43763}':'Network_Connectivity'
#  'SruDbCheckpointTable':'SruDbCheckpointTable'
#  '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}LT':'Energy_Usage_Provider'
#  '{5C8CF1C7-7257-4F13-B223-970EF5939312}':'App_Timeline_PRovider'
#  '{7ACBBAA3-D029-4BE4-9A7A-0885927F1D8F}':'vfuprov'
#  '{B6D82AF1-F780-4E17-8077-6CB9AD8A6FC4}':'Tagged_Energy_Provider'
#  '{DA73FB89-2BEA-4DDC-86B8-6E048C6DA477}':'Energy_Estiation_Provider2'


table_dict = {'SruDbIdMapTable':'SruDbIdMapTable','{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}':'Application_Resource_Usage', \
			  '{973F5D5C-1D90-4944-BE8E-24B94231A174}':'Network_Usage', '{DD6636C4-8929-4683-974E-22C046A43763}':'Network_Connectivity'}

table_dict_all = {'SruDbIdMapTable':'SruDbIdMapTable','{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}':'Application_Resource_Usage', \
              '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}':'Energy_Usage_Data','{97C2CE28-A37B-4920-B1E9-8B76CD341EC5}':'Energy_Estimation_Provider', \
			  '{973F5D5C-1D90-4944-BE8E-24B94231A174}':'Network_Usage','{D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}':'Windows_Push_Notification', \
			  '{DD6636C4-8929-4683-974E-22C046A43763}':'Network_Connectivity', 'MSysObjects':'MSysObjects', \
			  'MSysObjectsShadow':'MSysObjectsShadow', 'MSysObjids':'MSysObjids', 'MSysLocales':'MSysLocales', \
			  'SruDbCheckpointTable':'SruDbCheckpointTable', '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}LT':'Energy_Usage_Provider', \
              '{5C8CF1C7-7257-4F13-B223-970EF5939312}':'App_Timeline_Provider', '{7ACBBAA3-D029-4BE4-9A7A-0885927F1D8F}':'vfuprov', \
              '{B6D82AF1-F780-4E17-8077-6CB9AD8A6FC4}':'Tagged_Energy_Provider', '{DA73FB89-2BEA-4DDC-86B8-6E048C6DA477}':'Energy_Estimation_Provider2'}

def ole_date_bin_to_datetime(ole_date_bin):
    """
        Converts a OLE date from a binary 8 bytes little endian hex form to a datetime
    """
    #Conversion to OLE date float, where:
    # - integer part: days from epoch (1899/12/30 00:00) 
    # - decimal part: percentage of the day, where 0,5 is midday
    date_float = struct.unpack('<d', ole_date_bin)[0]
    date_decimal, date_integer = math.modf(date_float)
    date_decimal = abs(date_decimal)
    date_integer = int(date_integer)

    #Calculate the result
    res = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=date_integer) #adding days to epoch
    res = res + datetime.timedelta(seconds = 86400*date_decimal) #adding percentage of the day
    return res.strftime("%m/%d/%Y, %H:%M:%S")


def write_output(report_folder, data_headers, data_list, file_name, output_type):

    if 'tsv' in output_type:
        tsv_output(report_folder, data_headers, data_list, file_name)
 
    if 'csv' in output_type:
        csv_output(report_folder, data_headers, data_list, file_name)

    if 'jsonl' in output_type:
        jsonl_output(report_folder, data_headers, data_list, file_name)

def get_user_info(hive_file):

    # Find an existing key.
    try:
        hive = Registry.Registry(hive_file)
        key = hive.open("Microsoft\\Windows NT\\CurrentVersion\\ProfileList")
    except:
        return None

    user_id = {}

    # Print information about its subkeys.
    for sk in key.subkeys():
        if sk.values_number() > 0:
             #print (sk.name())
             user_sid = sk.name()
             sk_values = sk.values()
             for sk_value in sk_values:
                 #print (sk_value.name())
                 if sk_value.name() == 'ProfileImagePath':
                     (head, tail) = os.path.split(sk_value.value())
                     user_ids[user_sid] = tail[:-1]
    user_ids.update(known_sids)
    return True

def search_interfaces_subkey(subkey, subkey_name):

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
                       interface_ids[str(profileIndex)] = str(channelName)
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

def get_interfaces_info(hive_file):

    # Find an existing key.
    try:
        hive = Registry.Registry(hive_file)
        key = hive.open("Microsoft\\WlanSvc\\Interfaces")
    except:
        return None
    # Find an existing key.

    search_interfaces_subkey(key, "METADATA")

    return True
   
def Check_Column_Type(EsedbTable_Record, Column_Type, Column_Number, Record_List, convertSid):
    if (Column_Type == 0):   # Null
       return "NULL"
    elif (Column_Type == 1): #Boolean
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('NULL')
       else:
          return Record_List.append(str(EsedbTable_Record.get_value_data(Column_Number).decode('utf-16', 'ignore')))	
    elif (Column_Type == 2): #INTEGER_8BIT_UNSIGNED
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))
    elif (Column_Type == 3): #INTEGER_16BIT_SIGNED
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	
    elif (Column_Type == 4): #INTEGER_32BIT_SIGNED	
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))
    elif (Column_Type == 5): #CURRENCY
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	
    elif (Column_Type == 6): #INTEGER_8BIT_UNSIGNED
       return Record_List.append(EsedbTable_Record.get_value_data_as_floating_point(Column_Number))
    elif (Column_Type == 7): #DOUBLE_64BIT
       return Record_List.append(EsedbTable_Record.get_value_data_as_floating_point(Column_Number))	
    elif (Column_Type == 8): #DATETIME	
       #return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('')
       else:
          #print (EsedbTable_Record.get_value_data(Column_Number))
          return Record_List.append(ole_date_bin_to_datetime(EsedbTable_Record.get_value_data(Column_Number)))
    elif (Column_Type == 9): #BINARY_DATA
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('')
       else:
          return Record_List.append("Blob Record that is not supported at this time")
          return Record_List.append(EsedbTable_Record.get_value_data(Column_Number))
    elif (Column_Type == 10): #TEXT	
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('')
       else:
          if convertSid:
              #binString3 = EsedbTable_Record.get_value_data(Column_Number)
              #binString2 = binary_sid_to_string(EsedbTable_Record.get_value_data(Column_Number))
              return Record_List.append(binary_sid_to_string(EsedbTable_Record.get_value_data(Column_Number)))
          else:
              return Record_List.append(EsedbTable_Record.get_value_data(Column_Number).decode('utf-16', 'ignore'))
    elif (Column_Type == 11): #LARGE_BINARY_DATA
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('')
       else:
          return Record_List.append(EsedbTable_Record.get_value_data(Column_Number))
    elif (Column_Type == 12): #LARGE_TEXT	
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('')
       else:
          compressed_text = EsedbTable_Record.get_value_data(Column_Number)
          comp_text = compressed_text[1]
          if comp_text == 24:
             #print ("This text is EXPRESS Compressed")
             return Record_List.append(EsedbTable_Record.get_value_data(Column_Number).decode('utf-16', 'ignore'))
          if comp_text >= 23:
              compressed_data_index = 0
              compressed_data = compressed_text
              uncompressed_data_index = 0
              compressed_data_size = len(compressed_data)
              value_16bit = 0
              bit_index = 0
              compressed_data_index = 1
              comp_data = 0
              uncompressed_data = []
              while compressed_data_index < compressed_data_size:
                  comp_data = compressed_data[compressed_data_index]
                  value_16bit |= comp_data << bit_index
                  uncompressed_data_index = uncompressed_data_index + 1
                  uncompressed_data.append(chr(value_16bit & 127))
                  value_16bit >>= 7
                  bit_index += 1
                  if bit_index == 7:
                      uncompressed_data_index = uncompressed_data_index + 1
                      uncompressed_data.append(chr(value_16bit & 127))
                      value_16bit >>= 7
                      bit_index = 0
                  compressed_data_index += 1

              last_char = uncompressed_data.pop()
              out = ('').join(uncompressed_data)
              return Record_List.append(out)
          return Record_List.append(EsedbTable_Record.get_value_data(Column_Number).decode('utf-16', 'ignore'))
    elif (Column_Type == 13): #SUPER_LARGE_VALUE
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	
    elif (Column_Type == 14): #INTEGER_32BIT_UNSIGNED	
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	
    elif (Column_Type == 15): #INTEGER_64BIT_SIGNED
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	
    elif (Column_Type == 16): #GUID	
       if (EsedbTable_Record.get_value_data(Column_Number) == None):
          return Record_List.append('')
       else:
          return Record_List.append(str(EsedbTable_Record.get_value_data(Column_Number).decode('utf-16', 'ignore')))
    elif (Column_Type == 17): #INTEGER_16BIT_UNSIGNED
       return Record_List.append(EsedbTable_Record.get_value_data_as_integer(Column_Number))	

def parse_esedb_table(EsedbTable, Table_name):

    esedb_record = []
    esedb_column_headers = []
    number_of_columns = EsedbTable.get_number_of_columns()
    table_record = EsedbTable.get_record(0)
    for i in range(0,number_of_columns):
        esedb_column_headers.append(str(table_record.get_column_name(i)))

#    print ("table column names")
#    print (esedb_column_headers)
    
    for i in range(0,EsedbTable.get_number_of_records()):
       EsedbTable_Record = EsedbTable.get_record(i)
       esedb_temp_record = []
       Column_Name = EsedbTable_Record.get_column_name(0)
       idType = 0
       if Column_Name == 'IdType':
           id_type_rec = []
           Check_Column_Type(EsedbTable_Record, EsedbTable_Record.get_column_type(0), 0, id_type_rec, True)
           idType = id_type_rec[0]
       for x in range(0, number_of_columns):
           Column_Name = EsedbTable_Record.get_column_name(x)
           Column_Type = EsedbTable_Record.get_column_type(x)
           if Column_Name == 'IdBlob':
              if idType == 3:
                 Check_Column_Type(EsedbTable_Record, 10, x, esedb_temp_record, True)
              else:
                 Check_Column_Type(EsedbTable_Record, 10, x, esedb_temp_record, False)   
           else:
              if Column_Name == "AppId":
                  temp_record = []
                  Check_Column_Type(EsedbTable_Record, Column_Type, x, temp_record, False)
                  esedb_temp_record.append(srudbidmap.get(temp_record[0], temp_record[0]))
              elif Column_Name == "UserId":
                  temp_record = []
                  Check_Column_Type(EsedbTable_Record, Column_Type, x, temp_record, False)
                  esedb_temp_record.append(user_ids.get(srudbidmap.get(temp_record[0], temp_record[0]), srudbidmap.get(temp_record[0], temp_record[0])))
              elif Column_Name == "L2ProfileId":
                  temp_record = []
                  Check_Column_Type(EsedbTable_Record, Column_Type, x, temp_record, False)
                  esedb_temp_record.append(interface_ids.get(temp_record[0], temp_record[0]))              
              else:
                  Check_Column_Type(EsedbTable_Record, Column_Type, x, esedb_temp_record, False)

       esedb_record.append(esedb_temp_record) 
            
    return esedb_record, esedb_column_headers
			  
def Populate_ESEDB_DB(File_To_Parse, report_folder, output_type):
   idType = None
   tables_to_process = table_dict.keys()
   file_object = open(File_To_Parse, "rb")
   esedb_file = pyesedb.file()
   esedb_file.open_file_object(file_object)
   Num_Of_tables = esedb_file.get_number_of_tables()
   for i in range (0, Num_Of_tables):
        table = esedb_file.get_table(i) 
#        print ("Processing table => " + table.get_name())
        if table.get_name() in tables_to_process:
            Table_name = table.get_name()
            EsedbTable = esedb_file.get_table_by_name(Table_name)

            if Table_name == 'SruDbIdMapTable':
                (SruDbIdMapTable, SruDbIdMapTable_data_header) = parse_esedb_table(EsedbTable, Table_name)
                for sruId in SruDbIdMapTable:
                    srudbidmap[sruId[1]] = sruId[2]
            elif Table_name == '{973F5D5C-1D90-4944-BE8E-24B94231A174}':
                (network_usage, network_usage_data_header) = parse_esedb_table(EsedbTable, Table_name)
            elif Table_name == '{DD6636C4-8929-4683-974E-22C046A43763}':
                (network_connectivity, network_connectivity_data_header) = parse_esedb_table(EsedbTable, Table_name)


   if network_usage: 
       file_name = f'SRU Network Usage'
       write_output(report_folder, network_usage_data_header, network_usage, file_name, output_type) 
   else:
       logfunc(f'No Network Usage data available')

   if network_connectivity: 
       file_name = f'SRU Network Connectivity Usage'
       write_output(report_folder, network_connectivity_data_header, network_connectivity, file_name, output_type) 
   else:
       logfunc(f'No Network Connectivity data available')

   esedb_file.close()


def get_windows_sru_network(files_found, report_folder, seeker, output_type):
    
    hive_file = ''
    sru_db = ''
    
    for file_found in files_found:
        file_found = str(file_found)
        if os.path.basename(file_found).lower().endswith('.dat'): # skip -journal and other files
            sru_db = file_found
        if os.path.basename(file_found).lower().endswith('software'): # skip -journal and other files
            hive_file = file_found        
    
    found_user = get_user_info(hive_file)
    found_interface = get_interfaces_info(hive_file)

    if found_user == None and found_interface == None:
        return

    Populate_ESEDB_DB(sru_db, report_folder, output_type)
    

