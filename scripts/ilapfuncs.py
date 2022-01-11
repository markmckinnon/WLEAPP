import codecs
import csv
import datetime
import os
import pathlib
import re
import sqlite3
import sys
import simplekml
import magic
import shutil
import struct
from pathlib import Path

from bs4 import BeautifulSoup

user_name_dict = {}
current_control_set = 0

class windowsParameters:
    "these are parameters that can be passed around to different modules of data to use"

    def __init__(self):
        self.user_name_dict = {}
        self.current_control_set = 0
        self.network_interfaces = {}

    def set_control_set(self, current_control_set):
        self.current_control_set = current_control_set

    def get_control_set(self):
        return 'ControlSet00' + str(self.current_control_set)

    def add_network_interface(self, profile_index, channel_name):
        self.network_interfaces[profile_index] = channel_name

    def get_network_interface(self, profile_index, channel_name):
        return self.network_interfaces[profile_index]

    def add_user_sid(self, user_sid, user_name):
        self.user_name_dict[user_sid] = user_name

    def get_user_sids(self):
        return self.user_name_dict

    def get_user_sid(self, sid):
        return self.user_name_dict.get(sid, sid)

class OutputParameters:
    '''Defines the parameters that are common for '''
    # static parameters
    nl = '\n'
    screen_output_file_path = ''

    def __init__(self, output_folder):
        now = datetime.datetime.now()
        currenttime = str(now.strftime('%Y-%m-%d_%A_%H%M%S'))
        self.report_folder_base = os.path.join(output_folder, 'WLEAPP_Reports_' + currenttime) # aleapp , aleappGUI, ileap_artifacts, report.py
        self.temp_folder = os.path.join(self.report_folder_base, 'temp')
        OutputParameters.screen_output_file_path = os.path.join(self.report_folder_base, 'Script Logs', 'Screen Output.html')
        OutputParameters.screen_output_file_path_devinfo = os.path.join(self.report_folder_base, 'Script Logs', 'DeviceInfo.html')
        
        os.makedirs(os.path.join(self.report_folder_base, 'Script Logs'))
        os.makedirs(self.temp_folder)

def is_platform_windows():
    '''Returns True if running on Windows'''
    return os.name == 'nt'

def sanitize_file_path(filename, replacement_char='_'):
    '''
    Removes illegal characters (for windows) from the string passed. Does not replace \ or /
    '''
    return re.sub(r'[*?:"<>|\'\r\n]', replacement_char, filename)

def sanitize_file_name(filename, replacement_char='_'):
    '''
    Removes illegal characters (for windows) from the string passed.
    '''
    return re.sub(r'[\\/*?:"<>|\'\r\n]', replacement_char, filename)

def get_next_unused_name(path):
    '''Checks if path exists, if it does, finds an unused name by appending -xx
       where xx=00-99. Return value is new path.
       If it is a file like abc.txt, then abc-01.txt will be the next
    '''
    folder, basename = os.path.split(path)
    ext = None
    if basename.find('.') > 0:
        basename, ext = os.path.splitext(basename)
    num = 1
    new_name = basename
    if ext != None:
        new_name += f"{ext}"
    while os.path.exists(os.path.join(folder, new_name)):
        new_name = basename + "-{:02}".format(num)
        if ext != None:
            new_name += f"{ext}"
        num += 1
    return os.path.join(folder, new_name)

def open_sqlite_db_readonly(path):
    '''Opens an sqlite db in read-only mode, so original db (and -wal/journal are intact)'''
    if is_platform_windows():
        if path.startswith('\\\\?\\UNC\\'): # UNC long path
            path = "%5C%5C%3F%5C" + path[4:]
        elif path.startswith('\\\\?\\'):    # normal long path
            path = "%5C%5C%3F%5C" + path[4:]
        elif path.startswith('\\\\'):       # UNC path
            path = "%5C%5C%3F%5C\\UNC" + path[1:]
        else:                               # normal path
            path = "%5C%5C%3F%5C" + path
    return sqlite3.connect (f"file:{path}?mode=ro", uri=True)

def does_column_exist_in_db(db, table_name, col_name):
    '''Checks if a specific col exists'''
    col_name = col_name.lower()
    try:
        db.row_factory = sqlite3.Row # For fetching columns by name
        query = f"pragma table_info('{table_name}');"
        cursor = db.cursor()
        cursor.execute(query)
        all_rows = cursor.fetchall()
        for row in all_rows:
            if row['name'].lower() == col_name:
                return True
    except sqlite3.Error as ex:
        print(f"Query error, query={query} Error={str(ex)}")
        pass
    return False

def does_table_exist(db, table_name):
    '''Checks if a table with specified name exists in an sqlite db'''
    try:
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        cursor = db.execute(query)
        for row in cursor:
            return True
    except sqlite3Error as ex:
        logfunc(f"Query error, query={query} Error={str(ex)}")
    return False

class GuiWindow:
    '''This only exists to hold window handle if script is run from GUI'''
    window_handle = None # static variable 
    progress_bar_total = 0
    progress_bar_handle = None

    @staticmethod
    def SetProgressBar(n):
        if GuiWindow.progress_bar_handle:
            GuiWindow.progress_bar_handle.UpdateBar(n)

def logfunc(message=""):
    with open(OutputParameters.screen_output_file_path, 'a', encoding='utf8') as a:
        print(message)
        a.write(message + '<br>' + OutputParameters.nl)

    if GuiWindow.window_handle:
        GuiWindow.window_handle.refresh()
        
def logdevinfo(message=""):
    with open(OutputParameters.screen_output_file_path_devinfo, 'a', encoding='utf8') as b:
        b.write(message + '<br>' + OutputParameters.nl)
    
""" def deviceinfoin(ordes, kas, vas, sources): # unused function
    sources = str(sources)
    db = sqlite3.connect(reportfolderbase+'Device Info/di.db')
    cursor = db.cursor()
    datainsert = (ordes, kas, vas, sources,)
    cursor.execute('INSERT INTO devinf (ord, ka, va, source)  VALUES(?,?,?,?)', datainsert)
    db.commit() """
    
def html2csv(reportfolderbase):
    #List of items that take too long to convert or that shouldn't be converted
    itemstoignore = ['index.html',
                    'Distribution Keys.html', 
                    'StrucMetadata.html',
                    'StrucMetadataCombined.html']
                    
    if os.path.isdir(os.path.join(reportfolderbase, '_CSV Exports')):
        pass
    else:
        os.makedirs(os.path.join(reportfolderbase, '_CSV Exports'))
    for root, dirs, files in sorted(os.walk(reportfolderbase)):
        for file in files:
            if file.endswith(".html"):
                fullpath = (os.path.join(root, file))
                head, tail = os.path.split(fullpath)
                if file in itemstoignore:
                    pass
                else:
                    data = open(fullpath, 'r', encoding='utf8')
                    soup=BeautifulSoup(data,'html.parser')
                    tables = soup.find_all("table")
                    data.close()
                    output_final_rows=[]

                    for table in tables:
                        output_rows = []
                        for table_row in table.findAll('tr'):

                            columns = table_row.findAll('td')
                            output_row = []
                            for column in columns:
                                    output_row.append(column.text)
                            output_rows.append(output_row)
        
                        file = (os.path.splitext(file)[0])
                        with codecs.open(os.path.join(reportfolderbase, '_CSV Exports',  file +'.csv'), 'a', 'utf-8-sig') as csvfile:
                            writer = csv.writer(csvfile, quotechar='"', quoting=csv.QUOTE_ALL)
                            writer.writerows(output_rows)

def tsv(report_folder, data_headers, data_list, tsvname, source_file=None):
    report_folder = report_folder.rstrip('/')
    report_folder = report_folder.rstrip('\\')
    report_folder_base, tail = os.path.split(report_folder)
    tsv_report_folder = os.path.join(report_folder_base, '_TSV Exports')
    
    if os.path.isdir(tsv_report_folder):
        pass
    else:
        os.makedirs(tsv_report_folder)

    if os.path.exists(os.path.join(tsv_report_folder, tsvname +'.tsv')):
        with codecs.open(os.path.join(tsv_report_folder, tsvname +'.tsv'), 'a', encoding="utf-8") as tsvfile:
            tsv_writer = csv.writer(tsvfile, delimiter='\t')
            for i in data_list:
                if source_file == None:
                    tsv_writer.writerow(i)
                else:
                    row_data = list(i)
                    row_data.append(source_file)
                    tsv_writer.writerow(tuple(row_data))
    else:    
        with codecs.open(os.path.join(tsv_report_folder, tsvname +'.tsv'), 'a', 'utf-8-sig') as tsvfile:
            tsv_writer = csv.writer(tsvfile, delimiter='\t')
            if source_file ==  None:
                tsv_writer.writerow(data_headers)
                for i in data_list:
                    tsv_writer.writerow(i)
            else:
                data_hdr = list(data_headers)
                data_hdr.append("source file")
                tsv_writer.writerow(tuple(data_hdr))
                for i in data_list:
                    row_data = list(i)
                    row_data.append(source_file)
                    tsv_writer.writerow(tuple(row_data))
            

def timeline(report_folder, tlactivity, data_list, data_headers):
    report_folder = report_folder.rstrip('/')
    report_folder = report_folder.rstrip('\\')
    report_folder_base, tail = os.path.split(report_folder)
    tl_report_folder = os.path.join(report_folder_base, '_Timeline')

    if os.path.isdir(tl_report_folder):
        tldb = os.path.join(tl_report_folder, 'tl.db')
        db = sqlite3.connect(tldb)
        cursor = db.cursor()
        cursor.execute('''PRAGMA synchronous = EXTRA''')
        cursor.execute('''PRAGMA journal_mode = WAL''')
    else:
        os.makedirs(tl_report_folder)
        #create database
        tldb = os.path.join(tl_report_folder, 'tl.db')
        db = sqlite3.connect(tldb, isolation_level = 'exclusive')
        cursor = db.cursor()
        cursor.execute(
        """
        CREATE TABLE data(key TEXT, activity TEXT, datalist TEXT)
        """
            )
        db.commit()
    
    a = 0
    length = (len(data_list))
    while a < length: 
        modifiedList = list(map(lambda x, y: x + ': ' +  str(y), data_headers, data_list[a]))
        cursor.executemany("INSERT INTO data VALUES(?,?,?)", [(str(data_list[a][0]), tlactivity, str(modifiedList))])
        a += 1
    db.commit()
    db.close()
    
def kmlgen(report_folder, kmlactivity, data_list, data_headers):
    report_folder = report_folder.rstrip('/')
    report_folder = report_folder.rstrip('\\')
    report_folder_base, tail = os.path.split(report_folder)
    kml_report_folder = os.path.join(report_folder_base, '_KML Exports')
    
    if os.path.isdir(kml_report_folder):
        latlongdb = os.path.join(kml_report_folder, '_latlong.db')
        db = sqlite3.connect(latlongdb)
        cursor = db.cursor()
        cursor.execute('''PRAGMA synchronous = EXTRA''')
        cursor.execute('''PRAGMA journal_mode = WAL''')
        db.commit()
    else:
        os.makedirs(kml_report_folder)
        latlongdb = os.path.join(kml_report_folder, '_latlong.db')
        db = sqlite3.connect(latlongdb)
        cursor = db.cursor()
        cursor.execute(
        """
        CREATE TABLE data(key TEXT, latitude TEXT, longitude TEXT, activity TEXT)
        """
            )
        db.commit()
    
    kml = simplekml.Kml(open=1)
    
    a = 0
    length = (len(data_list))
    while a < length:
        modifiedDict = dict(zip(data_headers, data_list[a]))
        times = modifiedDict['Timestamp']
        lon = modifiedDict['Longitude']
        lat = modifiedDict['Latitude']
        if lat:
            pnt = kml.newpoint()
            pnt.name = times
            pnt.description = f"Timestamp: {times} - {kmlactivity}"
            pnt.coords = [(lon, lat)]
            cursor.execute("INSERT INTO data VALUES(?,?,?,?)", (times, lat, lon, kmlactivity))
        a += 1
    db.commit()
    db.close()
    kml.save(os.path.join(kml_report_folder, f'{kmlactivity}.kml'))
    
"""
Copyright 2021, CCL Forensics
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
def utf8_in_extended_ascii(input_string, *, raise_on_unexpected=False):
    """Returns a tuple of bool (whether mis-encoded utf-8 is present) and str (the converted string)"""
    output = []  # individual characters, join at the end
    is_in_multibyte = False  # True if we're currently inside a utf-8 multibyte character
    multibytes_expected = 0
    multibyte_buffer = []
    mis_encoded_utf8_present = False
    
    def handle_bad_data(index, character):
        if not raise_on_unexpected: # not raising, so we dump the buffer into output and append this character
            output.extend(multibyte_buffer)
            multibyte_buffer.clear()
            output.append(character)
            nonlocal is_in_multibyte
            is_in_multibyte = False
            nonlocal multibytes_expected
            multibytes_expected = 0
        else:
            raise ValueError(f"Expected multibyte continuation at index: {index}")
            
    for idx, c in enumerate(input_string):
        code_point = ord(c)
        if code_point <= 0x7f or code_point > 0xf4:  # ASCII Range data or higher than you get for mis-encoded utf-8:
            if not is_in_multibyte:
                output.append(c)  # not in a multibyte, valid ascii-range data, so we append
            else:
                handle_bad_data(idx, c)
        else:  # potentially utf-8
            if (code_point & 0xc0) == 0x80:  # continuation byte
                if is_in_multibyte:
                    multibyte_buffer.append(c)
                else:
                    handle_bad_data(idx, c)
            else:  # start-byte
                if not is_in_multibyte:
                    assert multibytes_expected == 0
                    assert len(multibyte_buffer) == 0
                    while (code_point & 0x80) != 0:
                        multibytes_expected += 1
                        code_point <<= 1
                    multibyte_buffer.append(c)
                    is_in_multibyte = True
                else:
                    handle_bad_data(idx, c)
                    
        if is_in_multibyte and len(multibyte_buffer) == multibytes_expected:  # output utf-8 character if complete
            utf_8_character = bytes(ord(x) for x in multibyte_buffer).decode("utf-8")
            output.append(utf_8_character)
            multibyte_buffer.clear()
            is_in_multibyte = False
            multibytes_expected = 0
            mis_encoded_utf8_present = True
        
    if multibyte_buffer:  # if we have left-over data
        handle_bad_data(len(input_string), "")
    
    return mis_encoded_utf8_present, "".join(output)

def media_to_html(media_path, files_found, report_folder):
    
    def relative_paths(source, splitter):
        splitted_a = source.split(splitter)
        for x in splitted_a:
            if 'LEAPP_Reports_' in x:
                report_folder = x
                
        splitted_b = source.split(report_folder)
        return '.'+ splitted_b[1]
    
    platform = is_platform_windows()
    if platform:
        media_path = media_path.replace('/', '\\')
        splitter = '\\'
    else:
        splitter = '/'
        
    thumb = media_path
    for match in files_found:
        filename = os.path.basename(match)
        if filename.startswith('~'):
            continue
        if filename.startswith('._'):
            continue
        
        if media_path in match:
            
            dirs = os.path.dirname(report_folder)
            dirs = os.path.dirname(dirs)
            env_path = os.path.join(dirs, 'temp')
            if env_path in match:
                source = match
                source = relative_paths(source, splitter)
            else:
                path = os.path.dirname(match)
                dirname = os.path.basename(path)
                filename = Path(match)
                filename = filename.name
                locationfiles = Path(report_folder).joinpath(dirname)
                Path(f'{locationfiles}').mkdir(parents=True, exist_ok=True)
                shutil.copy2(match, locationfiles)
                source = Path(locationfiles, filename)
                source = relative_paths(source, splitter)
                
            mimetype = magic.from_file(match, mime = True)
            
            if 'video' in mimetype:
                thumb = f'<video width="320" height="240" controls="controls"><source src="{source}" type="video/mp4">Your browser does not support the video tag.</video>'
            elif 'image' in mimetype:
                thumb = f'<img src="{source}"width="300"></img>'
            else:
                thumb = f'<a href="{source}"> Link to {mimetype} </>'
    return thumb

def usergen(report_folder, data_list_usernames):
    report_folder = report_folder.rstrip('/')
    report_folder = report_folder.rstrip('\\')
    report_folder_base, tail = os.path.split(report_folder)
    udb_report_folder = os.path.join(report_folder_base, '_Usernames DB')

    if os.path.isdir(udb_report_folder):
        usernames = os.path.join(udb_report_folder, '_usernames.db')
        db = sqlite3.connect(usernames)
        cursor = db.cursor()
        cursor.execute('''PRAGMA synchronous = EXTRA''')
        cursor.execute('''PRAGMA journal_mode = WAL''')
        db.commit()
    else:
        os.makedirs(udb_report_folder)
        usernames = os.path.join(udb_report_folder, '_usernames.db')
        db = sqlite3.connect(usernames)
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE data(username TEXT, appname TEXT, artifactname text, html_report text, data TEXT)
            """
        )
        db.commit()

    a = 0
    length = (len(data_list_usernames))
    while a < length:
        user = data_list_usernames[a][0]
        app = data_list_usernames[a][1]
        artifact = data_list_usernames[a][2]
        html_report = data_list_usernames[a][3]
        data = data_list_usernames[a][4]
        cursor.execute("INSERT INTO data VALUES(?,?,?,?,?)", (user, app, artifact, html_report, data))
        a += 1
    db.commit()
    db.close()


def ipgen(report_folder, data_list_ipaddress):
    report_folder = report_folder.rstrip('/')
    report_folder = report_folder.rstrip('\\')
    report_folder_base, tail = os.path.split(report_folder)
    udb_report_folder = os.path.join(report_folder_base, '_IPAddress DB')

    if os.path.isdir(udb_report_folder):
        ipaddress = os.path.join(udb_report_folder, '_ipaddresses.db')
        db = sqlite3.connect(ipaddress)
        cursor = db.cursor()
        cursor.execute('''PRAGMA synchronous = EXTRA''')
        cursor.execute('''PRAGMA journal_mode = WAL''')
        db.commit()
    else:
        os.makedirs(udb_report_folder)
        ipaddress = os.path.join(udb_report_folder, '_ipaddresses.db')
        db = sqlite3.connect(ipaddress)
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE data(ipaddress TEXT, appname TEXT, artifactname text, html_report text, data TEXT)
            """
        )
        db.commit()

    a = 0
    length = (len(data_list_ipaddress))
    while a < length:
        ip_address = data_list_ipaddress[a][0]
        app = data_list_ipaddress[a][1]
        artifact = data_list_ipaddress[a][2]
        html_report = data_list_ipaddress[a][3]
        data = data_list_ipaddress[a][4]
        cursor.execute("INSERT INTO data VALUES(?,?,?,?,?)", (ip_address, app, artifact, html_report, data))
        a += 1
    db.commit()
    db.close()


def binary_sid_to_string(sid_str):
    #Original form Source: https://github.com/google/grr/blob/master/grr/parsers/wmi_parser.py
    """Converts a binary SID to its string representation.
     https://msdn.microsoft.com/en-us/library/windows/desktop/aa379597.aspx
    The byte representation of an SID is as follows:
      Offset  Length  Description
      00      01      revision
      01      01      sub-authority count
      02      06      authority (big endian)
      08      04      subauthority #1 (little endian)
      0b      04      subauthority #2 (little endian)
      ...
    Args:
      sid: A byte array.
    Returns:
      SID in string form.
    Raises:
      ValueError: If the binary SID is malformed.
    """
    if not sid_str:
        return ""
#    sid = codecs.decode(sid_str,"hex")
    #print (sid_str)
    sid = sid_str
    str_sid_components = [sid[0]]
    # Now decode the 48-byte portion
    if len(sid) >= 8:
        subauthority_count = sid[1]
        identifier_authority = struct.unpack(">H", sid[2:4])[0]
        identifier_authority <<= 32
        identifier_authority |= struct.unpack(">L", sid[4:8])[0]
        str_sid_components.append(identifier_authority)
        start = 8
        for i in range(subauthority_count):
            authority = sid[start:start + 4]
            if not authority:
                break
            if len(authority) < 4:
                raise ValueError("In binary SID '%s', component %d has been truncated. "
                         "Expected 4 bytes, found %d: (%s)",
                         ",".join([str(ord(c)) for c in sid]), i,
                         len(authority), authority)
            str_sid_components.append(struct.unpack("<L", authority)[0])
            start += 4
            sid_str = "S-%s" % ("-".join([str(x) for x in str_sid_components]))
    sid_name = sid_str
    return sid_name

