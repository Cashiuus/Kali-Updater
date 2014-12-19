#!/usr/bin/env python
#
#	Target Release:		Python 2.x
#	Version:			1.3
#	Updated:			12/04/2014
#	Created by: 		cashiuus@gmail.com
#
# Functionality:
#   1. Add Bleeding Edge Repository
#   2. Update & Upgrade all Kali apps using 'apt-get'
#   3. Update defined list of Git Clones; if nonexistant you can add them
# ====================================================================

from __future__ import print_function
import os
import platform
import subprocess
import sys
import time

# ----------------------------- #
#    Set configurable settings  #
# ----------------------------- #
tdelay 			= 2				# Delay script for network latency
fixportmapper 	= False			# Want to fix portmapper issue at boot?
gitcolorize		= True			# This Enables git config option for 'color.ui'
DO_CHROME		= False			# Setup system for Google Chrome
UPDATE_VEIL		= True			# Update the Veil framework using its own script
GIT_BASE_DIR	= os.path.expanduser('~/git')

#    List your existing GIT CLONES here
#    TODO: Get existing git clones automatically; only known way is too slow
#			If I can find them in background during core update, would be ideal
normal_git_tools = {
	'artillery':'https://github.com/trustedsec/artillery',
	'creds':'https://github.com/DanMcInerney/creds.py',
	'kaliupdater':'https://github.com/Cashiuus/kaliUpdater',
	'lair':'https://github.com/fishnetsecurity/Lair',
	'powersploit':'https://github.com/mattifestation/PowerSploit',
	'seclists':'https://github.com/danielmiessler/SecLists',
	'veil':'https://github.com/Veil-Framework/Veil',
	'vfeed':'https://github.com/toolswatch/vFeed',
}
special_git_tools = {
	# These projects prefer to be placed in the "/opt" directory instead
	# local_name, Dict value=(Tuple: git_url, installer_file)
	'smbexec':('https://github.com/pentestgeek/smbexec','install.sh'),
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
		os.system("apt-get -qq update && apt-get -qq -y dist-upgrade && apt-get -y autoclean")
		os.system("updatedb")
		print("[+] Successfully updated Kali...moving along...")
	except:
		print("[-] Error attempting to update Kali. Please try again later.")

	time.sleep(tdelay)
	return


# -----------------------------
# Checking APT Repository List file
#
def bleedingRepoCheck():
	bleeding = 'deb http://repo.kali.org/kali kali-bleeding-edge main'
	repoFile = open('/etc/apt/sources.list', 'r')

	for line in repoFile.readlines():
		if bleeding == line.rstrip():
			check = 1
			break
		else:
			check = 0
	if check == 0:
		addrepo = input("\n[*] Would you like to add the Kali Bleeding Edge Repo? [y,N]: ")
		if (addrepo == 'y'):
			os.system("echo deb http://repo.kali.org/kali kali-bleeding-edge main >> /etc/apt/sources.list")
	return



# TODO: Add code to compare current versions with those found present
# Get installed version of supporting programming applications with dpkg
def get_versions():
	pVersion = str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + str(sys.version_info[2])
	print("\t[*] Python Version:\t{}".format(pVersion))

	try:
		out_bytes = subprocess.check_output(['ruby', '-v'])
		out_text = out_bytes.decode('UTF-8')
		out_text = out_text.split(' ')
		rVersion = out_text[1]
		print("\t[*] Ruby Version:\t", rVersion, sep='')
	except:
		print("\t[*] Ruby Version:\t Not Installed", sep='')

	try:
		out_bytes = subprocess.check_output(['gem', '-v'])
		gVersion = out_bytes.decode('UTF-8')
		gVersion = gVersion.rstrip()
		print("\t[*] Gem Version:\t", gVersion, sep='')
	except:
		print("\t[*] Gem Version:\t Not Installed", sep='')

	try:
		out_bytes = subprocess.check_output(['bundle', '-v'])
		out_text = out_bytes.decode('UTF-8')
		out_text = out_text.split(' ')
		bVersion = out_text[2]
		print("\t[*] Bundle Version:\t", bVersion, sep='')
	except:
		print("\t[*] Bundle Version:\t Not Installed", sep='')
	return

# TODO: Catch exceptions when Git fails update because local file was modified
def do_git_apps(install_path, tools_dict):
	"""
	Usage: do_git_apps(base_install_dir, dict_appname_github_url)
	Will process a dictionary of tools
	If dict value is a tuple, it will process post-clone installation
	"""
	for app, url in tools_dict.iteritems():
		install_script = False	# Need to initialize for function to work
		print("\n[*] Checking Repository: {}".format(app))
		app_path = os.path.join(install_path, app)
		# If the app already exists, just update it
		if os.path.isdir(app_path):
			os.chdir(app_path)
			try:
				subprocess.call('git pull', shell=True)
				time.sleep(tdelay)
			except:
				print("[-] Error updating Git Repo: {}".format(app))
		else:
			# App does not exist, we can set it up right now
			print("[-] This path does not exist: {}".format(app_path))
			createMe = input("Setup this Git Clone now? [y,N]: ")
			if(createMe == 'y'):
				make_dirs(app_path)
				os.chdir(install_path)
				# Check if the dict value is a tuple, indicating special tools
				if type(tools_dict[app]) is tuple:
					url2, install_script = url
				else:
					# Normal git, so just standardize the variable being used
					url2 = url
				subprocess.call('git clone ' + str(url2) + '.git ' + str(app), shell=True)

				# Now process all special git apps, which require additional installation
				if install_script:
					run_helper_script(os.path.join(app_path, install_script))
		# Check and update the Veil framework
		if app == 'veil':
			if UPDATE_VEIL:
				run_helper_script(os.path.join(app_path, 'update.sh'))
	return

def run_helper_script(script_path):
	"""
	This function aids installs and updates by running developers'
	locally crafted scripts. No sense in redoing their hard efforts.
	However, this also introduces a security concern if said script is malicious
	"""
	if not os.path.isfile(script_path):
		print("[-] Script path is invalid, skipping script execution")
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
	if os.path.isfile('etc/apt/sources.list.d/google-chrome.list'):
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
			f = open('/etc/apt/sources.list', 'wa')
			f.write(chrome_repo)
			f.close()
		except OSError:
			print("[-] Error trying to write to sources.list file. Installation aborted.")
			return
	#os.system('echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list')

	subprocess.call('apt-get -qq update', shell=True)
	subprocess.call('apt-get install -y google-chrome-stable', shell=True)

	inputfile = open('/opt/google/chrome/google-chrome', 'r')
	outputfile = open('/tmp/google-chrome', 'w')
	# TODO: This part not done
	return


def maint_tasks():
	if gitcolorize == True:
		os.system("git config --global color.ui auto")
	if fixportmapper == True:
		os.system("update-rc.d rpcbind defaults")
		time.sleep(tdelay)
		os.system("update-rc.d rpcbind enable")
	return

def do_app_updates():
	print("[*] Custom App Updates")
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

	do_app_updates()
	print("\n[+] Kali Updater is now complete. Goodbye!")
	return

if __name__ == '__main__':
	main()

