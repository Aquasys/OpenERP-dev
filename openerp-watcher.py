import time
import sys
import os
import subprocess
import shlex

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



def get_module_to_reload(path):
    """
    Returns the name of the module where a file has changed
    """
    path_directories = path.split('/')

    for index, directory in enumerate(path_directories):
        if directory == "addons":
            if path_directories[index + 1]:
                return path_directories[index + 1]

    #if we couldn't find (should not happen), don't reload any module specifically
    return None


def get_extension(path):
    """
    Return the file extension
    File starting by . are ignored
    """
    return os.path.splitext(path)[-1].lower()


def get_openerp_executable(path):
    """
    Gets the complete path to the openerp-server executable
    """
    path_directories = path.split('/')

    right_index = 0

    #Executable is in the folder 2 directories before addons/
    #Remove 1 to the index here
    for index, directory in enumerate(path_directories):
        if directory == "addons":
            if path_directories[index - 1]:
                right_index = index - 1

    #The slice removes 1 more and we have the right path
    return '/'.join(path_directories[:right_index]) + '/openerp-server'


def start_openerp(executable, module):
    """
    Starts OpenERP using the --update flag with the necessary module
    """

    #No module to update if first start
    if module:
        command = executable + ' --update=' + module
    else:
        command = executable

    args = shlex.split(command)

    print "Starting OpenERP"

    openerp = subprocess.Popen(args)

    return openerp


def stop_openerp(openerp):
    """
    Stops the openerp process
    """
    print "Stopping OpenERP"

    #Terminates the popen containing openerp
    openerp.terminate()


class UpdateHandler(FileSystemEventHandler):
    """
    Restarts openerp whenever a .py file is changed
    """
    openerp = None
    executable = None


    def __init__(self, addons_path):
        self.executable = get_openerp_executable(addons_path)
        self.openerp = start_openerp(self.executable, None)


    def on_any_event(self, event):

        if event.is_directory:
            return
        extension = get_extension(event.src_path)
        if extension == ".py" or extension == ".xml":
            module = get_module_to_reload(event.src_path)

            if self.openerp:
                stop_openerp(self.openerp)
                self.openerp = None

            #Sleep to avoid starting the server when the process is still up
            time.sleep(1)
            self.openerp = start_openerp(self.executable, module)



if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'

    event_handler = UpdateHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()