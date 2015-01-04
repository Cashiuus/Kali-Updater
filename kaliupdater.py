#!/usr/bin/env python
#
#   Target Release:     Python 2.x
#   Version:            1.5
#   Updated:            01/04/2015
#   Created by:         cashiuus@gmail.com
#
# Functionality:
#   1. Add Bleeding Edge Repository
#   2. Update & Upgrade all Kali apps using 'apt-get'
#   3. Update defined list of Git Clones; if nonexistant you can add them
# ====================================================================

from __future__ import print_function
import os
import shutil
import subprocess
import sys
import tarfile
import time

# TODO: There is a better way to import external variables
try:
    # Customized version of the "default.py" file
    from settings import *
except:
    # If "settings.py" doesn't exist, import default instead
    from default import *

# ----------------------------- #
#    Set configurable settings  #
# ----------------------------- #
tdelay = 2                  # Delay script for network latency
G  = '\033[32;1m'           # green
R  = '\033[31m'             # red
O  = '\033[33m'             # orange
W  = '\033[0m'              # white (normal)

#    List your existing GIT CLONES here
#    TODO: Get existing git clones automatically; only known way is too slow
#           If I can find them in background during core update, would be ideal
normal_git_tools = {
    'artillery': 'https://github.com/trustedsec/artillery',
    'creds': 'https://github.com/DanMcInerney/creds.py',
    'lair': 'https://github.com/fishnetsecurity/Lair',
    'powersploit': 'https://github.com/mattifestation/PowerSploit',
    'seclists': 'https://github.com/danielmiessler/SecLists',
    'vfeed': 'https://github.com/toolswatch/vFeed',
}

special_git_tools = {
    # These projects have specific directory requirements
    # Key=project_local_name
    #   Value= (nested dict)
    #       Key= install|url|script
    #           Value= path|url|script_basename
    'smbexec':
    {
        'install': '/opt',
        'url': 'https://github.com/pentestgeek/smbexec',
        'script': 'install.sh',
    },
    'veil':
    {
        'install': GIT_BASE_DIRS[0],
        'url': 'https://github.com/Veil-Framework/Veil',
        'script': 'update.sh',
    },
}

# Setup Python 2 & 3 'raw_input' compatibility
#
try:
    input = raw_input
except NameError:
    pass


# ----------------------------- #
#      UTILITY FUNCTIONS        #
# ----------------------------- #
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


# ----------------------------- #
#              BEGIN            #
# ----------------------------- #
#    Update Kali core distro using Aptitude
def core_update():
    print("[*] Now updating Kali and Packages...")
    try:
        subprocess.call("apt-get -qq update && apt-get -qq -y dist-upgrade && apt-get -y autoclean", shell=True)
        subprocess.call("updatedb", shell=False)
        print("[*] Successfully updated Kali...moving along...")
    except:
        printer("[-] Error attempting to update Kali. Please try again later.", color=R)

    time.sleep(tdelay)
    return


# -----------------------------
# Checking APT Repository List file
#
def bleeding_repo_check():
    bleeding = 'deb http://repo.kali.org/kali kali-bleeding-edge main'
    repofile = open('/etc/apt/sources.list', 'r')

    for line in repofile.readlines():
        if bleeding == line.rstrip():
            check = 1
            break
        else:
            check = 0
    repofile.close()

    if check == 0:
        addrepo = input("\n[+] Would you like to add the Kali Bleeding Edge Repo? [y,N]: ")
        if (addrepo == 'y'):
            repofile = '/etc/apt/sources.list'
    return


# TODO: Add code to compare current versions with those found to indicate update available
# Get installed version of supporting programming applications with dpkg
def get_versions():
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


def git_new(app_path, install_path, url, app_script=None):
    # App does not exist, we can set it up right now
    print("[-] This path does not exist: {}".format(app_path))
    answer = input("Setup this Git Clone now? [y,N]: ")
    if(answer == 'y'):
        make_dirs(app_path)
        # Change dir to the install_path, not app_path, so that clone creates dir in the right place
        os.chdir(install_path)

        # Clone the app into a new folder called $app
        subprocess.call('git clone ' + str(url) + '.git ' + str(app), shell=True)

        # Now process all special git apps, which require additional installation
        if app_script:
            run_helper_script(os.path.join(app_path, app_script))
    return


# TODO: Catch exceptions when Git fails update because local file was modified
def do_git_apps(path_list, tools_dict, special_tools):
    """
    Usage: do_git_apps(list(base_install_dir), dict(appname_github_url))
    Will process a dictionary of tools
    If dict value is a dict, it will process post-clone installation
    """
    fnull = open(os.devnull, 'w')

    def git_update(git_path):
        if os.path.isdir(git_path):
            os.chdir(git_path)
            try:
                subprocess.call('git pull', shell=True)
                time.sleep(tdelay)
            except:
                printer("[-] Error updating Git Repo: {}".format(git_path))
                # TODO: Maybe in future ask if we want to reset this broken repo, not yet
            return True
        else:
            return False

    # Pre-processing of existing GIT repositories
    my_apps = []
    for item in path_list:
        # if we have a folder that also has a .git folder inside it, we want to update it
        # list - full paths to app
        # TODO: Maybe a better approach is to find them and ask to update the repo list with existing ones
        my_apps.extend([os.path.join(item, x) for x in os.listdir(item) if os.path.isdir(os.path.join(item, x, '.git'))])

    for app, details in tools_dict.iteritems():
        printer("\n[*] Checking Repository: {}".format(app), color=G)

        # Normal git, so just standardize the variable being used
        url = details
        # New repo clones are always installed in first directory path
        install_path = path_list[0]
        app_path = os.path.join(install_path, app)
        print("[*] Application Path: {}".format(app_path))

        # Avoid redundancy, remove apps from list if we're checking it already
        if app_path in my_apps:
            my_apps.remove(app_path)
            
        if not git_update(app_path):
            git_new(app_path, install_path, url, app_script=app_script)

    for app, details in special_tools.iteritems():
        app_script = False      # Initialize toggle for function to work
        # What type of mapping are we dealing with
        # Check if the dict value is a dict, indicating special tools
        printer("Special Tools Mapping: {}".format(app))
        install_path = special_tools[app]['install']
        url = special_tools[app]['url']
        app_script = special_tools[app]['script']
        app_path = os.path.join(install_path, app)
        print("[*] Application Path: {}".format(app_path))
        
        # Avoid redundancy, remove apps from list if we're checking it already
        if app_path in my_apps:
            my_apps.remove(app_path)
            
        if not git_update(app_path):
            git_new(app_path, install_path, url, app_script=app_script)
    # Now update my existing git repoos
    for i in my_apps:
        printer("\n[*] Updating Repository: {}".format(i.split('/')[-1]), color=G)
        git_update(i)


def run_helper_script(script_path):
    """
    This function aids installs and updates by running developers'
    locally crafted scripts. No sense in redoing their hard efforts.
    However, this also introduces a security concern if said script is malicious
    """
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
    # Credit to: http://www.blackmoreops.com/2013/12/01/install-google-chrome-kali-linux-part-2/
    chrome_repo = 'deb http://dl.google.com/linux/chrome/deb/ stable main'

    # Google Chrome creates its own sources file, let's check for it first
    if os.path.isfile('/etc/apt/sources.list.d/google-chrome.list'):
        found = True
    else:
        f = open('/etc/apt/sources.list', 'r')
        found = False
        for line in f.readlines():
            if line.startswith("#"):
                continue
            if line.strip() == chrome_repo:
                found = True
        f.close()
    if not found:
        try:
            f = open('/etc/apt/sources.list', 'a')
            f.write(chrome_repo)
            f.close()
        except OSError:
            printer("[-] Error trying to write to sources.list file. Installation aborted.", color=R)
            return

    # Check if Chrome is already installed in its default location
    if not os.path.isfile('/opt/google/chrome/google-chrome'):
        subprocess.call('apt-get install -qq -y google-chrome-stable', shell=True)

    # Check Chrome's config file and fix if it is broken for root use
    inputfile = open('/opt/google/chrome/google-chrome', 'r')
    contents = inputfile.readlines()
    inputfile.close()
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
            run_helper_script('/opt/google/chrome/google-chrome')
        except Exception as e:
            printer("Error moving Google chrome config file: {}".format(e))
            pass
    else:
        print("[*] Google chrome config file appears to be fine, moving along")
    return


def maint_tasks():
    if gitcolorize is True:
        subprocess.check_output(['git', 'config', '--global', 'color.ui', 'auto'])
    if fixportmapper is True:
        subprocess.call("update-rc.d rpcbind defaults", shell=True)
        time.sleep(tdelay)
        subprocess.call("update-rc.d rpcbind enable", shell=True)
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
        response = input("[-] The backup destination file already exists, overwrite? [y, N]: ")
        if response != 'y':
            return False
    z = tarfile.open(zname, mode='w:gz')

    # ------ dotfiles -----------
    for f in os.listdir(usr):
        fpath = os.path.join(usr, f)
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
    maint_tasks()
    if DO_CHROME:
        # Do chrome first, this way we can run update just once
        setup_chrome()
    core_update()
    print("[*] Kali core update is complete. Listing utility bundle versions below:")
    get_versions()
    if DO_GIT_REPOS:
        print("[*] Now updating Github cloned repositories...")
        do_git_apps(GIT_BASE_DIRS, normal_git_tools, special_git_tools)

    if DO_BACKUPS:
        if backup_files(BACKUP_FILES, BACKUP_PATH) is True:
            print("[*] Backups successfully saved to: {}".format(BACKUP_PATH))
        else:
            printer("[-] Backups failed to complete", color=R)

    printer("\n[*] Kali Updater is now complete. Goodbye!\n", color=G)
    return


if __name__ == '__main__':
    main()
