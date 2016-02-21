#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==============================================================================
# File:         kali-updater.py
# Depends:
# Compat:       2.7+
# Created:      09/21/2015  -   Revised: 02/20/2016
# Author:       Cashiuus - Cashiuus@gmail.com
#
# Purpose:      Update kali, git repositories, and other helpers all at once.
#
# ==============================================================================
#
# Functionality:
#   1. Update & Upgrade all Kali apps using 'apt-get'
#   2. Update defined list of Git Clones; if nonexistant you can add them
#   3. Create a backup archive of specified files--See default.py
# ====================================================================
from __future__ import absolute_import
from __future__ import print_function
__version__ = 0.8
__author__ = 'Cashiuus'
# ===[ Python 2/3 Compatibilities ]=== #
try: input = raw_input
except NameError: pass
## =======[ IMPORT & CONSTANTS ]========= ##
import fnmatch
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import time
# ==========================[           ]========================== #
# TODO: There is (maybe?) a better way to import external variables
try:
    # Customized version of the "default.py" file
    from settings import *
except:
    # If "settings.py" doesn't exist, import default instead
    from default import *

## ========[ TEXT COLORS ]=============== ##
GREEN = '\033[32;1m'    # Green
YELLOW = '\033[01;33m'  # Warnings/Information
RED = '\033[31m'        # Red/Error
ORANGE = '\033[33m'     # Orange/Debug
RESET = '\033[00m'      # Normal/White
# ========================[  CORE UTILITY FUNCTIONS  ]======================== #
def printer(msg, color=ORANGE):
    if color == ORANGE and DO_DEBUG:
        print("{}[DEBUG] {!s}{}".format(color, msg, RESET))
    elif color != ORANGE:
        print("{}{!s}{}".format(color, msg, RESET))
    return


# Check - Root user
# TODO: If not root, run with sudo
def root_check():
    if not (os.geteuid() == 0):
        printer("[-] Not currently root user. Please fix.", color=RED)
        exit(1)
    return


def make_dirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return
# ==========================[  BEGIN APPLICATION  ]========================== #
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
        #text = raw_input(prompt)
        text = input(prompt)
        signal.alarm(0)
        return text
    except AlarmException:
        return choice
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    return ''


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
        subprocess.call(
            "apt-get -qq update && apt-get -y dist-upgrade && apt-get -y autoclean", shell=True)
        print("[*] Successfully updated Kali...moving along...")
    except:
        printer("[-] Error attempting to update Kali. Please try again later.", color=RED)
    time.sleep(tdelay)
    return


# -------------------------------
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
                print("{}----[-]{} Error trying to write to sources.list file. Installation aborted.".format(RED, RESET))
    return


def git_new(app, app_path, install_path, url, app_script=None, cmd=None, upstream=None):
    '''
    Clone Git Repositories not already present on system.
    Also, runs any specific installer file required by the project
    '''
    printer("[*] Installing New Repo: {}".format(app), color=GREEN)

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
        print("{0}[*]{1} Updating Git Repo: {2}\t[{0}Path:{1} {3}{0}]{1}".format(GREEN, RESET, os.path.split(git_path)[1], git_path))
        try:
            print("{0}[*]{1} Git Owner: {2}".format(GREEN, RESET, git_owner(git_path)))
        except IndexError:
            # There is no owner string listed in this repository's git config file, so ignore
            pass

        try:
            os.chdir(git_path)
            subprocess.call('git pull', shell=True)
            time.sleep(tdelay)
        except:
            print("{}----[-]{} Error updating Git Repo: {}".format(RED, RESET, git_path))
    return


def do_git_apps(path_list, git_tools):
    """
    Will process a dictionary of tools
    If dict value is a dict, it will process post-clone installation

    Usage: do_git_apps(list(base_install_dir), dict(git_tools))
    """

    # fnull = open(os.devnull, 'w')

    # Find all Repositories on the system and update them all?
    print("{0}----[*]{1} Searching Filesystem for all Git Clones...".format(GREEN, RESET))
    my_apps = []

    # -- Update Existing Repos
    for i in locate('.git'):
        # For each found Git Repo, add to my_apps list and call update
        dir_repo, tail = os.path.split(i)
        if '/.cache/' not in dir_repo:
            my_apps.append(dir_repo)
            git_update(dir_repo)
    for i in my_apps:
        printer("<Existing List> : {}".format(i), color=ORANGE)

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
        printer("Application Path: {}".format(app_path), color=ORANGE)
        # Avoid redundancy, remove apps from list if we're checking it already
        if app_path in my_apps:
            printer("App is already in existing apps list!", color=ORANGE)
            continue
        printer("\n[*] Installing Repository: {}".format(app), color=GREEN)
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
        printer("[-] Script path is invalid, skipping script execution", color=RED)
        return False
    if not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)
        except:
            printer("[-] Unable to modify permissions on script file, aborting", color=RED)
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
            # BROKEN: run_helper_script('/opt/google/chrome/google-chrome')
        except Exception as e:
            printer("Error moving Google chrome config file: {}".format(e))
            pass
    else:
        print("[*] Google chrome config file appears to be fine, moving along")
    return


# TODO: Add code to compare current versions with those found to indicate update available
# Get installed version of supporting programming applications with dpkg
def get_specs():
    print("{}==============================================================={}".format(GREEN, RESET))
    print("\t{}[*] Active Shell:{}\t{!s}".format(GREEN, RESET, os.environ['SHELL']))

    pversion = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
    print("\t{}[*] Python Version:{}\t{}".format(GREEN, RESET, pversion))

    try:
        out_bytes = subprocess.check_output(['ruby', '-v'])
        out_text = out_bytes.decode('UTF-8')
        rversion = out_text.split(' ')[1]
        print("\t{}[*] Ruby Version:{}\t{!s}".format(GREEN, RESET, rversion))
    except:
        printer("\t[*] Ruby Version:\t Not Installed", color=RED)

    try:
        out_bytes = subprocess.check_output(['gem', '-v'])
        gversion = out_bytes.decode('UTF-8')
        gversion = gversion.rstrip()
        print("\t{}[*] Gem Version:{}\t{!s}".format(GREEN, RESET, gversion))
    except:
        printer("\t[*] Gem Version:\t Not Installed", color=RED)

    try:
        out_bytes = subprocess.check_output(['bundle', '-v'])
        out_text = out_bytes.decode('UTF-8')
        bversion = out_text.split(' ')[2]
        print("\t{}[*] Bundle Version:{}\t{!s}".format(GREEN, RESET, bversion))
    except:
        printer("\t[-] Bundle Version:\t Not Installed", color=RED)
    print("{}==============================================================={}\n\n".format(GREEN, RESET))
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
            printer("[-] Error creating backup folders", color=RED)
            return False

    # Create the compressed archive the files will be sent to
    zname = BACKUP_PATH + os.sep + 'daily-' + time.strftime('%Y%m%d') + '.tar.gz'
    if os.path.exists(zname):
        # response = input("[-] The backup destination file already exists, overwrite? [y, N]: ")
        response = input_with_timeout(  prompt='[-] The backup destination file already exists, overwrite? [y,N]: ',
                                        choice='N', timeout=10)
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
            printer("Error adding backup file: {}".format(e), color=RED)
    # Close archive file
    z.close()
    return True


# ------------------------
#          MAIN
# ------------------------
def main():
    print('{}================================================================\n'.format(GREEN))
    print('                          Kali Updater                          \n'.format(RESET))
    print("{0}========================<{1} version: {2} {0}>========================\n{1}".format(GREEN, RESET, __version__))
    maint_tasks()
    if DO_CHROME:
        # Do chrome first, this way we can run update just once
        setup_chrome()
    core_update()
    print("[*] Kali core update is complete.")

    if DO_GIT_REPOS:
        print("{0}----[*]{1} Now updating Github cloned repositories...".format(GREEN, RESET))
        do_git_apps(GIT_BASE_DIRS, GIT_APPS_LIST)

    if DO_BACKUPS:
        if backup_files(BACKUP_FILES, BACKUP_PATH) is True:
            print("{0}----[*] Backups successfully saved to:{1} {2}".format(GREEN, RESET, BACKUP_PATH))
        else:
            printer("[-] Backups failed to complete", color=RED)

    # Update RVM, if present on system
    if os.system('which rvm') == 0:
        subprocess.call('rvm get stable', shell=True)

    subprocess.call('updatedb', shell=True)
    print("\n{}[*]{} Kali Updater is now complete. Listing vital stats below:".format(GREEN, RESET))
    get_specs()
    return


if __name__ == '__main__':
    main()
