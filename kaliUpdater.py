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

# ----------------------------- #
#    Set configurable settings  #
# ----------------------------- #
tdelay 			= 2				# Delay script for network latency
fixportmapper 	= False			# Want to fix portmapper issue at boot?
gitcolorize		= True			# This Enables git config option for 'color.ui'

#    List your existing GIT CLONES here
#    TODO: Get existing git clones automatically; only known way is too slow
#			If I can find them in background during core update, would be ideal
listTools = [
	'/usr/share/veil',			# Veil evasion framework
	'/usr/share/creds',			# Easy Creds tool
	'/usr/share/Responder',		# Responder NTLM credential monitor
	'/opt/smbexec',				# https://github.com/pentestgeek/smbexec
	'/opt/geany'				# Simple IDE interface
]


# ----------------------------- #
#              BEGIN            #
# ----------------------------- #
# Check if user is root
def root_check():
	if not (os.geteuid() == 0):
		print("[-] Not currently root user. Please fix.")
		exit(1)
	return


#    Update Kali core distro using Aptitude   #
def core_update():
	addrepo = raw_input("\n[*] Would you like to add the Kali Bleeding Edge Repo? [y,n]: ")
	if (addrepo == 'y'):
		os.system("echo deb http://repo.kali.org/kali kali-bleeding-edge main >> /etc/apt/sources.list")
	print("[+] Now updating Kali and Packages...")
	try:
		os.system("apt-get -qq update && apt-get -y dist-upgrade && apt-get -y autoclean")
		os.system("updatedb")
		print("[+] Successfully updated Kali...moving along...")
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

# TODO: Catch exceptions when Git fails update because local file was modified
def update_extras():
	for i in listTools:
		print("\nChecking Repository:", i,"\t", sep='')
		try:
			os.chdir(i)
			time.sleep(tdelay)
			subprocess.call('git pull', shell=True)
			time.sleep(tdelay)
		except Exception as e:
			print("[-] This path does not exist:\n\t", e)
	return

def maint_tasks():
	if gitcolorize == True:
		os.system("git config --global color.ui auto")
	if fixportmapper == True:
		os.system("update-rc.d rpcbind defaults")
		time.sleep(tdelay)
		os.system("update-rc.d rpcbind enable")
	return

def main():
	maint_tasks()
	core_update()
	print("[+] Kali core update is complete. Listing support versions below:")
	get_versions()
	print("[+] Now updating Github cloned repositories...")
	repoCount = update_extras()
	print("\n[+] Kali Updater is now complete. Goodbye!")
	return

if __name__ == '__main__':
	main()

