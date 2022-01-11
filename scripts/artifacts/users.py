#!/usr/bin/env python3
import json
#import datetime
#import os
from Registry import Registry
import struct
import os
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline

known_sids = {"S-1-5-32-545": "Users", "S-1-5-32-544": "Administrators", "S-1-5-32-547": "Power Users",
              "S-1-5-32-546": "Guests",
              "S-1-5-32-569": "BUILTIN\\Cryptographic Operators", "S-1-16-16384": "System Mandatory Level",
              "S-1-5-32-551": "Backup Operators",
              "S-1-16-8192": "Medium Mandatory Level", "S-1-5-80": "NT Service", "S-1-5-32-548": "Account Operators",
              "S-1-5-32-561": "BUILTIN\\Terminal Server License Servers", "S-1-5-64-14": "SChannel Authentication",
              "S-1-5-32-562": "BUILTIN\\Distributed COM Users", "S-1-5-64-21": "Digest Authentication",
              "S-1-5-19": "NT Authority", "S-1-3-0": "Creator Owner",
              "S-1-5-80-0": "All Services", "S-1-5-20": "NT Authority", "S-1-5-18": "Local System",
              "S-1-5-32-552": "Replicators",
              "S-1-5-32-579": "BUILTIN\\Access Control Assistance Operators", "S-1-16-4096": "Low Mandatory Level",
              "S-1-16-12288": "High Mandatory Level",
              "S-1-2-0": "Local", "S-1-16-0": "Untrusted Mandatory Level", "S-1-5-3": "Batch", "S-1-5-2": "Network",
              "S-1-5-1": "Dialup", "S-1-5-7": "Anonymous",
              "S-1-5-6": "Service", "S-1-5-4": "Interactive", "S-1-5-9": "Enterprise Domain Controllers",
              "S-1-5-8": "Proxy", "S-1-5-32-550": "Print Operators",
              "S-1-0-0": "Nobody", "S-1-5-32-559": "BUILTIN\\Performance Log Users",
              "S-1-5-32-578": "BUILTIN\\Hyper-V Administrators", "S-1-5-32-549": "Server Operators",
              "S-1-2-1": "Console Logon", "S-1-3-1": "Creator Group",
              "S-1-5-32-575": "BUILTIN\\RDS Remote Access Servers", "S-1-3-3": "Creator Group Server",
              "S-1-3-2": "Creator Owner Server", "S-1-5-32-556": "BUILTIN\\Network Configuration Operators",
              "S-1-5-32-557": "BUILTIN\\Incoming Forest Trust Builders",
              "S-1-5-32-554": "BUILTIN\\Pre-Windows 2000 Compatible Access",
              "S-1-5-32-573": "BUILTIN\\Event Log Readers", "S-1-5-32-576": "BUILTIN\\RDS Endpoint Servers",
              "S-1-5-83-0": "NT VIRTUAL MACHINE\\Virtual Machines", "S-1-16-28672": "Secure Process Mandatory Level",
              "S-1-5-11": "Authenticated Users", "S-1-1-0": "Everyone",
              "S-1-5-32-555": "BUILTIN\\Remote Desktop Users", "S-1-16-8448": "Medium Plus Mandatory Level",
              "S-1-5-17": "This Organization",
              "S-1-5-32-580": "BUILTIN\\Remote Management Users", "S-1-5-15": "This Organization",
              "S-1-5-14": "Remote Interactive Logon", "S-1-5-13": "Terminal Server Users",
              "S-1-5-12": "Restricted Code", "S-1-5-32-577": "BUILTIN\\RDS Management Servers",
              "S-1-5-10": "Principal Self", "S-1-3": "Creator Authority",
              "S-1-2": "Local Authority", "S-1-1": "World Authority", "S-1-0": "Null Authority",
              "S-1-5-32-574": "BUILTIN\\Certificate Service DCOM Access",
              "S-1-5": "NT Authority", "S-1-4": "Non-unique Authority",
              "S-1-5-32-560": "BUILTIN\\Windows Authorization Access Group",
              "S-1-16-20480": "Protected Process Mandatory Level", "S-1-5-64-10": "NTLM Authentication",
              "S-1-5-32-558": "BUILTIN\\Performance Monitor Users"}


def get_users(files_found, report_folder, seeker, wrap_text, win_parms):
    
    for file_found in files_found:
        file_found = str(file_found)
        # Find an existing key.
        if file_found.lower().endswith('sam'):
            data_list = []
            try:
                hive = Registry.Registry(file_found)
                key = hive.open("SAM\\Domains\\Account\\Users")
            except:
                return None

            user_id = {}

            # Print information about its subkeys.
            for sk in key.subkeys():
                if sk.values_number() > 0:
                    registry_key = sk.name()
                    sk_values = sk.values()
                    user_name = ""
                    full_name = ""
                    comment = ""
                    user_sid = ""
                    user_name_decoded = ""
                    user_name_create_dttm = 0
                    last_login_date = 0
                    pwd_reset_date = 0
                    acct_exp_date = 0
                    pwd_fail_date = 0
                    user_rid = ""
                    user_acb_flags = ""
                    user_failed_count = ""
                    user_login_count = ""
                    given_name = ""
                    sur_name = ""
                    internet_name = ""
                    pw_hint = ""
                    security_question_1 = ""
                    security_answer_1 = ""
                    security_question_2 = ""
                    security_answer_2 = ""
                    security_question_3 = ""
                    security_answer_3 = ""
                    temp_list = []

                    for sk_value in sk_values:
                        if sk_value.name() == 'V':
                            bin_data = sk_value.raw_data()
                            pos_1 = int(str(struct.unpack_from('<l', bin_data[4:])[0]))
                            pos_3 = int(str(struct.unpack_from('<l', bin_data[12:])[0])) + 204
                            pos_4 = int(str(struct.unpack_from('<l', bin_data[16:])[0]))
                            pos_6 = int(str(struct.unpack_from('<l', bin_data[24:])[0])) + 204
                            pos_7 = int(str(struct.unpack_from('<l', bin_data[28:])[0]))
                            pos_9 = int(str(struct.unpack_from('<l', bin_data[36:])[0])) + 204
                            pos_10 = int(str(struct.unpack_from('<l', bin_data[40:])[0]))
                            fmt_string_name = ">" + str(pos_4) + "s"
                            fmt_string_fullname = ">" + str(pos_7) + "s"
                            fmt_string_comment = ">" + str(pos_10) + "s"
                            user_name = struct.unpack_from(fmt_string_name, bin_data[pos_3:])[0]
                            full_name_temp = struct.unpack_from(fmt_string_fullname, bin_data[pos_6:])[0]
                            comment_temp = struct.unpack_from(fmt_string_comment, bin_data[pos_9:])[0]
                            full_name = full_name_temp.decode("utf-16")
                            comment = comment_temp.decode("utf-16")
                            user_sid = str(int(registry_key, 16))
                            user_name_decoded = user_name.decode("utf-16")

                            win_parms.add_user_sid(user_sid, user_name_decoded)

                            #user_name_create_dttm = sk_value.timestamp()
                        elif sk_value.name() == 'F':
                            bin_data = sk_value.raw_data()
                            last_login_date = int(str(struct.unpack_from('<q', bin_data[8:])[0])[0:11]) - 11644473600
                            pwd_reset_date = int(str(struct.unpack_from('<q', bin_data[24:])[0])[0:11]) - 11644473600
                            acct_exp_date = int(str(struct.unpack_from('<q', bin_data[32:])[0])[0:11]) - 11644473600
                            pwd_fail_date = int(str(struct.unpack_from('<q', bin_data[40:])[0])[0:11]) - 11644473600
                            if last_login_date < 0:
                                last_login_date = 0
                            if pwd_reset_date < 0:
                                pwd_reset_date = 0
                            if acct_exp_date < 0:
                                acct_exp_date = 0
                            if pwd_fail_date < 0:
                                pwd_fail_date = 0
                            user_rid = struct.unpack_from('<l', bin_data[48:])[0]
                            user_acb_flags = int(str(struct.unpack_from('<l', bin_data[56:])[0]))
                            user_failed_count = int(str(struct.unpack_from('<h', bin_data[64:])[0]))
                            user_login_count = int(str(struct.unpack_from('<h', bin_data[66:])[0]))

                        elif sk_value.name() == 'ResetData':
                            bin_data = sk_value.raw_data()
                            reset_data = json.loads(bin_data.decode("utf-16"))
                            question_list = reset_data["questions"]
                            question_1 = question_list[0]
                            question_2 = question_list[1]
                            question_3 = question_list[2]
                            security_question_1 = question_1["question"]
                            security_answer_1 = question_1["answer"]
                            security_question_2 = question_2["question"]
                            security_answer_2 = question_2["answer"]
                            security_question_3 = question_3["question"]
                            security_answer_3 = question_3["answer"]

                        elif sk_value.name() == 'GivenName':
                            bin_data = sk_value.raw_data()
                            fmt_given_name = ">" + str(len(bin_data)) + "s"
                            given_name = struct.unpack_from(fmt_given_name, bin_data[0:])[0]

                        elif sk_value.name() == 'SurName':
                            bin_data = sk_value.raw_data()
                            fmt_sur_name = ">" + str(len(bin_data)) + "s"
                            sur_name = struct.unpack_from(fmt_sur_name, bin_data[0:])[0]

                        elif sk_value.name() == 'InternetUserName':
                            bin_data = sk_value.raw_data()
                            fmt_internet_name = ">" + str(len(bin_data)) + "s"
                            internet_name = struct.unpack_from(fmt_internet_name, bin_data[0:])[0]

                        elif sk_value.name() == 'UserPasswordHint':
                            bin_data = sk_value.raw_data()
                            fmt_pw_hint = ">" + str(len(bin_data)) + "s"
                            pw_hint_temp = struct.unpack_from(fmt_pw_hint, bin_data[0:])[0]
                            pw_hint = pw_hint_temp.decode("utf-16")

                    temp_list = (user_name_decoded, full_name, comment, user_sid, user_name_decoded, user_name_create_dttm,
                                 last_login_date, pwd_reset_date, acct_exp_date, pwd_fail_date, user_rid,
                                 user_acb_flags, user_failed_count, user_login_count, given_name,
                                 sur_name, internet_name, pw_hint, security_question_1, security_answer_1, security_question_2, security_answer_2,
                                 security_question_3, security_answer_3)
                    data_list.append(temp_list)

            num_entries = len(data_list)
            if num_entries > 0:
                report = ArtifactHtmlReport('SAM Information')
                report.start_artifact_report(report_folder, 'SAM Information')
                report.add_script()
                data_headers = ('user_name', 'full_name', 'comment', 'user_sid', 'user_name_decoded', 'user_name_create_dttm',
                                'last_login_date', 'pwd_reset_date', 'acct_exp_date', 'pwd_fail_date', 'user_rid',
                                'user_acb_flags', 'user_failed_count', 'user_login_count', 'given_name',
                                'sur_name', 'internet_name', 'pw_hint', 'question 1', 'answer 1', 'question 2', 'answer 2', 'question 3', 'answer 3')

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'SAM Information'
                tsv(report_folder, data_headers, data_list, tsvname)

                tlactivity = f'SAM Information'
                timeline(report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No SAM Information data available')
        elif file_found.lower().endswith('software'):
            data_list = []
            # Find an existing key.
            try:
                hive = Registry.Registry(file_found)
                key = hive.open("Microsoft\\Windows NT\\CurrentVersion\\ProfileList")
            except:
                continue

            # Print information about its subkeys.
            for sk in key.subkeys():
                if sk.values_number() > 0:
                    # print (sk.name())
                    user_sid = sk.name()
                    sk_values = sk.values()
                    for sk_value in sk_values:
                        # print (sk_value.name())
                        if sk_value.name() == 'ProfileImagePath':
                            (head, tail) = os.path.split(sk_value.value())
                            temp_list = []
                            win_parms.add_user_sid(user_sid, tail)
                            temp_list.append(user_sid)
                            temp_list.append(tail)
                            data_list.append(temp_list)

            num_entries = len(data_list)
            if num_entries > 0:
                report = ArtifactHtmlReport('Profile List')
                report.start_artifact_report(report_folder, 'Profile List')
                report.add_script()
                data_headers = ('sid', 'user name')

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'Profile List'
                tsv(report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Profile List'
                timeline(report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Profile List data available')
    for sid in known_sids.keys():
        win_parms.add_user_sid(sid, known_sids[sid])
