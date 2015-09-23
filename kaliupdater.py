#!/usr/bin/env python
#
#   Target Release:     Python 2.x
#   Version:            0.5
#   Updated:            09/21/2015
#   Created by:         cashiuus@gmail.com
#
# Functionality:
#   1. Update & Upgrade all Kali apps using 'apt-get'
#   2. Update defined list of Git Clones; if nonexistant you can add them
#   3. Create a backup archive of specified files--See default.py
# ====================================================================

from __future__ import print_function
import fnmatch
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import time

# TODO: There is (maybe?) a better way to import external variables
try:
    # Customized version of the "default.py" file
    from settings import *
except:
    # If "settings.py" doesn't exist, import default instead
    from default import *

# Setup Python 2 & 3 'raw_input' compatibility
try:
    input = raw_input
except NameError:
    pass


# ----------------------------- #
#      UTILITY FUNCTIONS        #
# ----------------------------- #
G  = '\033[32;1m'           # green text coloring
R  = '\033[31m'             # red text coloring
O  = '\033[33m'             # orange text coloring
W  = '\033[0m'              # white (normal) text coloring
def printer(msg, color=O):
    if color == O and DO_DEBUG:
        print("{}[DEBUG] {!s}{}".format(color, msg, W))
    elif color != O:
        print("{}{!s}{}".format(color, msg, W))
    return


# Check - Root user
# TODO: If not root, run with sudo
def root_check():
    if not (os.geteuid() == 0):
        printer("[-] Not currently root user. Please fix.", color=R)
        exit(1)
    return


def make_dirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return

def locate(pattern, root='/'):
    '''
    Local all Git repositories in the filesystem,
    creating a list in order to update them all.
    '''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(dirs, pattern):
            yield os.path.join(path, filename)


class AlarmException(Exception):
    pass

def alarm_handler(signum, frame):
    raise AlarmException

def input_with_timeout(prompt='', choice=None, timeout=20):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    try:
        text = raw_input(prompt)
        signal.alarm(0)
        return text
    except AlarmException:
        return choice
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    return ''


# ----------------------------- #
#              BEGIN            #
# ----------------------------- #

def maint_tasks():
    # Git color config setting
    subprocess.check_output(['git', 'config', '--global', 'color.ui', 'auto'])
    if fixportmapper is True:
        subprocess.call("update-rc.d rpcbind defaults", shell=True)
        time.sleep(tdelay)
        subprocess.call("update-rc.d rpcbind enable", shell=True)
    return

#    Update Kali core distro using Aptitude
def core_update():
    print("[*] Now updating Kali and Packages...")
    try:
        subprocess.call("apt-get -qq update && apt-get -y dist-upgrade && apt-get -y autoclean", shell=True)
        print("[*] Successfully updated Kali...moving along...")
    except:
        printer("[-] Error attempting to update Kali. Please try again later.", color=R)
    time.sleep(tdelay)
    return


# -----------------------------
# APT Repository Changes
# -------------------------------
def apt_repo_change(repo_string, sources_file=None):
    ''' Accept a repo string and/or file name to determine
    if the desired repository is already present for apt-get.
    If it is not, it will create the string or file.
    
    Usage: apt_repo_change(<string>, <filename>)
    '''
    # If a sources file is known, check existance first
    if (sources_file) and (os.path.isfile(sources_file)):
        found = True
    else:
        with open('/etc/apt/sources.list', 'r') as repofile:
            for line in repofile.readlines():
                if line.startswith("#"):
                    continue
                if repo_string == line.strip():
                    found = True
    if not found:
        if sources_file:
            # Create the intended sources file for the future
            with open(sources_file, 'w'):
                f.write(repo_string)
        else:
            try:
                with open('/etc/apt/sources.list', 'a') as f:
                    f.write(repo_string)
            except OSError:
                printer("[-] Error trying to write to sources.list file. Installation aborted.", color=R)
    return


def git_new(app, app_path, install_path, url, app_script=None, cmd=None, upstream=None):
    '''
    Clone Git Repositories not already present on system.
    Also, runs any specific installer file required by the project
    '''
    printer("[*] Installing New Repo: {}".format(app), color=G)

    make_dirs(app_path)
    # Change dir to the install_path, not app_path, so that clone creates dir in the right place
    os.chdir(install_path)

    # Clone the app into a new folder called $app
    subprocess.call('git clone ' + str(url) + '.git ' + str(app), shell=True)
    time.sleep(tdelay)
    # Now process all special git apps, which require additional installation
    if app_script:
        run_helper_script(os.path.join(app_path, app_script))
    if cmd and not cmd.startswith('rm'):
        subprocess.call(cmd, shell=True)
    return


def git_owner(ap):
    ''' Get the owner for existing cloned Git repos
    the .git/config file has a line that startswith url that contains remote url
    Unfortunately, there doesn't appear to be any way to get master owner for forks :(
    '''
    with open(os.path.join(ap, '.git', 'config'), 'r') as fgit:
        #for line in fgit.readlines():
        #    if line.strip().startswith('url'):
        #        owner_string = line.strip().split(' ')[2]
        owner_string = [x.strip().split(' ')[2] for x in fgit.readlines() if x.strip().startswith('url')]
    return owner_string[0]


def git_update(git_path):
    ''' 
    Update existing Git Cloned Repositories
    '''
    if os.path.isdir(os.path.join(git_path, '.git')):
        printer("[*] Updating Git Repo: {}".format(os.path.split(git_path)[1]), color=G)
        printer("[*] Git Owner: {}".format(git_owner(git_path)), color=G)
        try:
            os.chdir(git_path)
            subprocess.call('git pull', shell=True)
            time.sleep(tdelay)
        except:
            printer("[-] Error updating Git Repo: {}".format(git_path), color=R)
    return


def do_git_apps(path_list, git_tools):
    """
    Will process a dictionary of tools
    If dict value is a dict, it will process post-clone installation
    
    Usage: do_git_apps(list(base_install_dir), dict(git_tools))
    """
    
    fnull = open(os.devnull, 'w')
        
    # Find all Repositories on the system and update them all?
    printer("[*] Searching Filesystem for all Git Clones...", color=W)
    my_apps = []
    
    ## -- Update Existing Repos
    for i in locate('.git'):
        # For each found Git Repo, add to my_apps list and call update
        dir_repo, tail = os.path.split(i)
        if '/.cache/' not in dir_repo:
            my_apps.append(dir_repo)
            git_update(dir_repo)
    for i in my_apps:
        printer("<Existing List> : {}".format(i), color=O)

    # -- Process Git Projects
    for app, details in git_tools.iteritems():
        # Get all possible key/values, behavior based on which exist
        url = details.get('url')
        app_script = details.get('script')
        upstream = details.get('upstream')
        install_path = details.get('install')
        command = details.get('command')
        if not install_path:
            # New repo clones are always installed in first directory path
            install_path = path_list[0]
        
        app_path = os.path.join(install_path, app)
        printer("Application Path: {}".format(app_path), color=O)
        # Avoid redundancy, remove apps from list if we're checking it already
        if app_path in my_apps:
            printer("App is already in existing apps list!", color=O)
            continue
        printer("\n[*] Installing Repository: {}".format(app), color=G)
        # If new, install it
        git_new(app, app_path, install_path, url, app_script=app_script, 
            cmd=command, upstream=upstream)
    return



def run_helper_script(script_path):
    '''
    This function aids installs and updates by running developers'
    locally crafted scripts. No sense in redoing their hard efforts.
    However, this also introduces a security concern if said script is malicious...
    '''
    if not os.path.isfile(script_path):
        printer("[-] Script path is invalid, skipping script execution", color=R)
        return False
    if not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)
        except:
            printer("[-] Unable to modify permissions on script file, aborting", color=R)
            return False
    os.system('clear')
    subprocess.call(script_path, shell=True)
    return True


def setup_chrome():
    """
    Google Chrome has an odd setup path within Kali and hates running as root
    """
    chrome_repo = 'deb http://dl.google.com/linux/chrome/deb/ stable main'
    apt_repo_change(chrome_repo, '/etc/apt/sources.list.d/google-chrome.list')

    # Check if Chrome is already installed in its default location
    if not os.path.isfile('/opt/google/chrome/google-chrome'):
        subprocess.call('apt-get install -qq -y google-chrome-stable', shell=True)

    # Check Chrome's config file and fix if it is broken for root use
    with open('/opt/google/chrome/google-chrome', 'r') as inputfile:
        contents = inputfile.readlines()

    if contents[-1].strip() == '"$@"':
        # The default config file is back and we must replace it
        outputfile = open('/tmp/google-chrome', 'w')
        for line in contents[:-2]:
            outputfile.write(line)
        chromefix = 'exec -a "$0" "$HERE/chrome" "$@" --user-data-dir "$PROFILE_DIRECTORY_FLAG"\n'
        outputfile.write(chromefix)
        outputfile.close()
        # Move the new file to overwrite the old
        try:
            shutil.move('/tmp/google-chrome', '/opt/google/chrome/google-chrome')
            #run_helper_script('/opt/google/chrome/google-chrome')
        except Exception as e:
            printer("Error moving Google chrome config file: {}".format(e))
            pass
    else:
        print("[*] Google chrome config file appears to be fine, moving along")
    return


# TODO: Add code to compare current versions with those found to indicate update available
# Get installed version of supporting programming applications with dpkg
def get_specs():
    
    print("\t{}[*] Active Shell:{}\t{!s}".format(G, W, os.environ['SHELL'])
    
    pversion = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
    print("\t{}[*] Python Version:{}\t{}".format(G, W, pversion))

    try:
        out_bytes = subprocess.check_output(['ruby', '-v'])
        out_text = out_bytes.decode('UTF-8')
        rversion = out_text.split(' ')[1]
        print("\t{}[*] Ruby Version:{}\t{!s}".format(G, W, rversion))
    except:
        printer("\t[*] Ruby Version:\t Not Installed", color=R)

    try:
        out_bytes = subprocess.check_output(['gem', '-v'])
        gversion = out_bytes.decode('UTF-8')
        gversion = gversion.rstrip()
        print("\t{}[*] Gem Version:{}\t{!s}".format(G, W, gversion))
    except:
        printer("\t[*] Gem Version:\t Not Installed", color=R)

    try:
        out_bytes = subprocess.check_output(['bundle', '-v'])
        out_text = out_bytes.decode('UTF-8')
        bversion = out_text.split(' ')[2]
        print("\t{}[*] Bundle Version:{}\t{!s}".format(G, W, bversion))
    except:
        printer("\t[-] Bundle Version:\t Not Installed", color=R)
    return


def file_filter(f):
    if f in EXCLUDE_FILES:
        return True
    else:
        return False


def backup_files(files, dest):
    if not os.path.isdir(BACKUP_PATH):
        try:
            os.makedirs(BACKUP_PATH, mode=0o711)
        except:
            printer("[-] Error creating backup folders", color=R)
            return False

    # Create the compressed archive the files will be sent to
    zname = BACKUP_PATH + os.sep + 'daily-' + time.strftime('%Y%m%d') + '.tar.gz'
    if os.path.exists(zname):
        #response = input("[-] The backup destination file already exists, overwrite? [y, N]: ")
        response = input_with_timeout(prompt='[-] The backup destination file already exists, overwrite? [y,N]: ', choice='N', timeout=10)
        print('\n')
        if response != 'y':
            return False
    
    z = tarfile.open(zname, mode='w:gz')

    # ------ dotfiles -----------
    for f in os.listdir(USER_PATH):
        fpath = os.path.join(USER_PATH, f)
        if f.startswith('.') and not os.path.isdir(fpath):
            if f not in EXCLUDE_FILES:
                # Add to archive if it is not in the excluded files list
                z.add(fpath)

    # --------- backup files ----------
    for fpath in BACKUP_FILES:
        try:
            # Add files unless they are listed in the exclude settings
            z.add(fpath, filter=lambda x: None if x.name in EXCLUDE_FILES else x)
        except Exception as e:
            printer("Error adding backup file: {}".format(e), color=R)
    # Close archive file
    z.close()
    return True


# ------------------------
#          MAIN
# ------------------------
def main():
    printer('================================================================', color=G)
    printer('                          Kali Updater                          ', color=W)
    printer('================================================================', color=G)
    print('\n')
    maint_tasks()
    if DO_CHROME:
        # Do chrome first, this way we can run update just once
        setup_chrome()
    core_update()
    print("[*] Kali core update is complete.")

    if DO_GIT_REPOS:
        printer("[*] Now updating Github cloned repositories...", color=G)
        do_git_apps(GIT_BASE_DIRS, GIT_APPS_LIST)

    if DO_BACKUPS:
        if backup_files(BACKUP_FILES, BACKUP_PATH) is True:
            printer("[*] Backups successfully saved to: {}".format(BACKUP_PATH), color=G)
        else:
            printer("[-] Backups failed to complete", color=R)

    # Update RVM, if present on system
    if os.system('which rvm') == 0:
        subprocess.call('rvm get stable', shell=True)
    
    subprocess.call('updatedb', shell=True)
    printer("\n[*] Kali Updater is now complete. Listing vital stats below:\n", color=G)
    get_specs()

    return


if __name__ == '__main__':
    main()
