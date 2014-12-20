#!/usr/bin/env python
#
#   Target Release:     Python 2.x
#   Version:            1.3
#   Updated:            12/04/2014
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
import time

# ----------------------------- #
#    Set configurable settings  #
# ----------------------------- #
tdelay          = 2             # Delay script for network latency
fixportmapper   = False         # Want to fix portmapper issue at boot?
gitcolorize     = True          # This Enables git config option for 'color.ui'
DO_CHROME       = True         # Setup system for Google Chrome
UPDATE_VEIL     = True          # Update the Veil framework using its own script
GIT_BASE_DIR    = os.path.expanduser('~/git')

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
    # These projects prefer to be placed in the "/opt" directory instead
    # local_name, Dict value=(Tuple: git_url, installer_file)
    'smbexec':
    {
        'install': '/opt',
        'url': 'https://github.com/pentestgeek/smbexec',
        'script': 'install.sh',
    },
    'veil':
    {
        'install': GIT_BASE_DIR,
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
#              BEGIN            #
# ----------------------------- #
# Check - Root user
# TODO: If not root, run with sudo
def root_check():
    if not (os.geteuid() == 0):
        print("[-] Not currently root user. Please fix.")
        exit(1)
    return


def make_dirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return


#    Update Kali core distro using Aptitude
#
def core_update():
    print("[+] Now updating Kali and Packages...")
    try:
        subprocess.call("apt-get -qq update && apt-get -qq -y dist-upgrade && apt-get -y autoclean", shell=True)
        subprocess.call("updatedb", shell=False)
        print("[+] Successfully updated Kali...moving along...")
    except:
        print("[-] Error attempting to update Kali. Please try again later.")

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
        addrepo = input("\n[*] Would you like to add the Kali Bleeding Edge Repo? [y,N]: ")
        if (addrepo == 'y'):
            repofile = '/etc/apt/sources.list'
    return


# TODO: Add code to compare current versions with those found present
# Get installed version of supporting programming applications with dpkg
def get_versions():
    pversion = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
    print("\t[*] Python Version:\t{}".format(pversion))

    try:
        out_bytes = subprocess.check_output(['ruby', '-v'])
        out_text = out_bytes.decode('UTF-8')
        rversion = out_text.split(' ')[1]
        print("\t[*] Ruby Version:\t{}".format(rversion))
    except:
        print("\t[*] Ruby Version:\t Not Installed")

    try:
        out_bytes = subprocess.check_output(['gem', '-v'])
        gversion = out_bytes.decode('UTF-8')
        gversion = gversion.rstrip()
        print("\t[*] Gem Version:\t{}".format(gversion))
    except:
        print("\t[*] Gem Version:\t Not Installed")

    try:
        out_bytes = subprocess.check_output(['bundle', '-v'])
        out_text = out_bytes.decode('UTF-8')
        bversion = out_text.split(' ')[2]
        print("\t[*] Bundle Version:\t", bversion, sep='')
    except:
        print("\t[*] Bundle Version:\t Not Installed", sep='')
    return


# TODO: Catch exceptions when Git fails update because local file was modified
def do_git_apps(install_path, tools_dict):
    """
    Usage: do_git_apps(base_install_dir, dict_appname_github_url)
    Will process a dictionary of tools
    If dict value is a dict, it will process post-clone installation
    """
    for app, details in tools_dict.iteritems():
        app_script = False  # Initialize toggle for function to work
        print("\n[*] Checking Repository: {}".format(app))

        # What type of mapping are we dealing with
        # Check if the dict value is a dict, indicating special tools
        if type(tools_dict[app]) is dict:
            print("[DEBUG] Special Tools Mapping: {}".format(app))
            install_path = tools_dict[app]['install']
            url = tools_dict[app]['url']
            app_script = tools_dict[app]['script']
        else:
            # Normal git, so just standardize the variable being used
            url = details
        # This will make app_path correct for either type of mapping
        app_path = os.path.join(install_path, app)

        print("[DEBUG] Application Path: {}".format(app_path))

        # If the app already exists, just update it
        if os.path.isdir(app_path):
            os.chdir(app_path)
            try:
                subprocess.call('git pull', shell=True)
                time.sleep(tdelay)
            except:
                print("[-] Error updating Git Repo: {}".format(app))
                # TODO: Maybe in future ask if we want to reset this broken repo, not yet
        else:
            # App does not exist, we can set it up right now
            print("[-] This path does not exist: {}".format(app_path))
            answer = input("Setup this Git Clone now? [y,N]: ")
            if(answer == 'y'):
                make_dirs(app_path)
                os.chdir(install_path)

                # Clone the app into a new folder called $app
                subprocess.call('git clone ' + str(url) + '.git ' + str(app), shell=True)

                # Now process all special git apps, which require additional installation
                if app_script:
                    run_helper_script(os.path.join(app_path, app_script))
    return


def run_helper_script(script_path):
    """
    This function aids installs and updates by running developers'
    locally crafted scripts. No sense in redoing their hard efforts.
    However, this also introduces a security concern if said script is malicious
    """
    if not os.path.isfile(script_path):
        print("[-] Script path is invalid, skipping script execution")
        return False
    if not os.access(script_path, os.X_OK):
        try:
            os.chmod(script_path, 0o755)
        except:
            print("[-] Unable to modify permissions on script file, aborting")
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
            print("[-] Error trying to write to sources.list file. Installation aborted.")
            return

    subprocess.call('apt-get -qq update', shell=True)
    # TODO: Add in a check if it already exists first
    subprocess.call('apt-get install -y google-chrome-stable', shell=True)

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
            print("[-] Error moving Google chrome config file: {}".format(e))
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


# ------------------------
#          MAIN
# ------------------------
def main():
    maint_tasks()
    core_update()
    print("[+] Kali core update is complete. Listing utility bundle versions below:")
    get_versions()
    print("[+] Now updating Github cloned repositories...")
    do_git_apps(GIT_BASE_DIR, normal_git_tools)
    do_git_apps('/opt', special_git_tools)
    # Check for Google Chrome
    if DO_CHROME:
        setup_chrome()
    print("\n[+] Kali Updater is now complete. Goodbye!")
    return

if __name__ == '__main__':
    main()
