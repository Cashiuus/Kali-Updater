#!/usr/bin/env python
#
#	Target Release:		3.x
#	Version:			1.0
#	Created by: 		cashiuus@gmail.com
#
# This script will update core Kali, update known Git clones,
# and other trivial maintenance tasks

from __future__ import print_function
import os
import subprocess
import sys
import time

#    Set configurable settings  #
# ------------------------------#
tdelay 			= 2				# Delay script for network latency
fixportmapper 	= FALSE			# Want to fix portmapper issue at boot?

#    List your GIT CLONES here
listTools = [
	'/usr/share/veil',			# Veil evasion framework
	'/opt/geany'				# Simple IDE interface
]


# ----------------------------#
#             BEGIN           #
# ----------------------------#
# Check if user is root
if not (os.geteuid() == 0):
	useSudo = input("[-] Not running as root. Continue using sudo? [y or n]")
	if (useSudo == 'y'):
		useSudo = 'sudo'
		pass
	else:
		exit(1)


#    Update Kali distro using Aptitude   #
def core_update():
	print("[+] Now updating Kali and Packages...")
	try:
		os.system("apt-get -qq update && apt-get -y dist-upgrade && apt-get -y autoclean")
		print("[+] Successfully updated Kali")
	except:
		print("[-] Error attempting to update Kali. Please try again later.")

	time.sleep(tdelay)
	return


# TODO: Add code to compare current versions with those found present
# Get installed version of supporting programming applications
def get_versions():
	pVersion = sys.version_info[0]	# major version
	pVersion2 = sys.version_info[1]	# minor version
	print("\t[*] Python Version:\t", str(pVersion), ".", str(pVersion2), ".x", sep='')

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


def update_extras():
	for i in listTools:
		print("Repository:",i,"\t", sep='')
		os.chdir(i)
		time.sleep(tdelay)
		subprocess.call('git pull', shell=True)
		time.sleep(tdelay)
	return len(listTools)

def maint_tasks():
	if fixportmapper == TRUE:
		os.system("update-rc.d rpcbind defaults")
		time.sleep(tdelay)
		os.system("update-rc.d rpcbind enable")
	return

def main():
	core_update()
	print("[+] Kali core update is complete. Listing support versions below:")
	get_versions()
	print("[+] Now updating Github cloned repositories...")
	repoCount = update_extras()
	print("\n[+] Repo updates complete. Updated:",str(repoCount),"repositories.")
	maint_tasks()
	return

if __name__ == '__main__':
	main()

