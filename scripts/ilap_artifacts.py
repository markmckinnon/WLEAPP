# To add a new artifact module, import it here as shown below:
#     from scripts.artifacts.fruitninja import get_fruitninja
# Also add the grep search for that module using the same name
# to the 'tosearch' data structure.

import traceback

from scripts.artifacts.betterDiscord import get_betterDiscord
from scripts.artifacts.prefetch import get_prefetch
from scripts.artifacts.users import get_users
from scripts.artifacts.bam import get_bam
from scripts.artifacts.control_sets import get_control_sets
from scripts.artifacts.network_interfaces import get_network_interfaces
from scripts.artifacts.sru_application import get_sru_application
from scripts.artifacts.services import get_services

from scripts.ilapfuncs import *

# GREP searches for each module
# Format is Key='modulename', Value=Tuple('Module Pretty Name', 'regex_term')
#   regex_term can be a string or a list/tuple of strings
# Here modulename must match the get_xxxxxx function name for that module. 
# For example: If modulename='profit', function name must be get_profit(..)
# Don't forget to import the module above!!!!

tosearch = {
    'control_sets': ('Control Sets', ('*/Windows/System32/config/SYSTEM')),
    'network_interfaces': ('Network Interfaces', ('*/Windows/System32/config/SOFTWARE')),
    'users':('User Information', ('*/Windows/System32/config/SAM', '*/Windows/System32/config/SOFTWARE')),
    'betterDiscord':('Better Discord', ('*/AppData/Roaming/BetterDiscord/plugins/MessageLoggerV2Data.config.json')),
 # Program Execution
    'prefetch':('Program Execution', ('*/Windows/Prefetch/*.pf')),
    'bam':('Program Execution', ('*/Windows/System32/config/SYSTEM')),
    'sru_application': ('Program Execution', ('*/Windows/System32/sru/SRUDB.dat')),
    'services': ('Program Execution', ('*/Windows/System32/config/SYSTEM')),
}
slash = '\\' if is_platform_windows() else '/'

def process_artifact(files_found, artifact_func, artifact_name, seeker, report_folder_base, wrap_text, win_parms):
    ''' Perform the common setup for each artifact, ie, 
        1. Create the report folder for it
        2. Fetch the method (function) and call it
        3. Wrap processing function in a try..except block

        Args:
            files_found: list of files that matched regex

            artifact_func: method to call

            artifact_name: Pretty name of artifact

            seeker: FileSeeker object to pass to method
            
            wrap_text: whether the text data will be wrapped or not using textwrap.  Useful for tools that want to parse the data.

            win_parms: Windows parmameters what can be passed around to different artifacts (ie: username/sid)
    '''
    logfunc('{} [{}] artifact executing'.format(artifact_name, artifact_func))
    report_folder = os.path.join(report_folder_base, artifact_name) + slash
    try:
        if os.path.isdir(report_folder):
            pass
        else:
            os.makedirs(report_folder)
    except Exception as ex:
        logfunc('Error creating {} report directory at path {}'.format(artifact_name, report_folder))
        logfunc('Reading {} artifact failed!'.format(artifact_name))
        logfunc('Error was {}'.format(str(ex)))
        return
    try:
        method = globals()['get_' + artifact_func]
        method(files_found, report_folder, seeker, wrap_text, win_parms)
    except Exception as ex:
        logfunc('Reading {} artifact had errors!'.format(artifact_name))
        logfunc('Error was {}'.format(str(ex)))
        logfunc('Exception Traceback: {}'.format(traceback.format_exc()))
        return

    logfunc('{} [{}] artifact completed'.format(artifact_name, artifact_func))
    