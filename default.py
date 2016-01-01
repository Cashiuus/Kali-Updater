#!/usr/bin/env python
#
# default.py
#
# If you make changes to this file, rename it to "settings.py"
# --------------------------------------------------------------

import os
DO_DEBUG = False
# Delay script for network latency
tdelay = 2

BACKUP_PATH = os.path.join(os.path.expanduser('~'), 'Backups')
USER_PATH = os.path.expanduser('~')

# Want to fix portmapper issue at boot?
fixportmapper   = False
# Backup user-specified files to an archive file
DO_BACKUPS      = True
# Setup system for Google Chrome; if installed it will update
DO_CHROME       = False
# Update all known Git repositories with 'git pull'
DO_GIT_REPOS    = True
# Update the Veil Framework using its own script
UPDATE_VEIL     = True

# List here folders that you are using for all git repos
# YOUR PRIMARY GIT DIRECTORY SHOULD BE FIRST. This is where
# your git_tools repositories will be cloned if they don't exist
GIT_BASE_DIRS = [
    os.path.expanduser('/opt/git'),
]

#    List your existing GIT CLONES here
#    TODO: Get existing git clones automatically; only known way is too slow
GIT_APPS_LIST = {
    # These projects have specific directory requirements
    # Key=project_local_name
    #   Value= (nested dict)
    #       Key= install|url|script|upstream
    #           Value= path|url|script_basename|upstream_url
    'artillery':
        {
        'url': 'https://github.com/trustedsec/artillery',
        },
    'creds.py': 
        {
        'url': 'https://github.com/DanMcInerney/creds.py',
        },
    'ftpmap': 
        {
        'url': 'https://github.com/Hypsurus/ftpmap',
        'command': './configure && make && make install',
        },
    'lair': 
        {
        'url': 'https://github.com/fishnetsecurity/Lair',
        },
    'mainframed' :
        {
        'url': 'https://github.com/mainframed/Mainframed',
        },
    'powersploit': 
        {
        'url': 'https://github.com/mattifestation/PowerSploit',
        },
    'pupy': 
        {
        'url': 'https://github.com/n1nj4sec/pupy',
        }
    'Responder': 
        {
        'url': 'https://github.com/SpiderLabs/Responder',
        },
    'seclists': 
        {
        'url': 'https://github.com/danielmiessler/SecLists',
        },
    'vfeed': 
        {
        'url': 'https://github.com/toolswatch/vFeed',
        },
    'smbexec':
        {
        # Don't install smbexec in '/opt' or installer defauls will fail
        'install': GIT_BASE_DIRS[0],
        'url': 'https://github.com/pentestgeek/smbexec',
        'script': 'install.sh',
        },
    'veil-framework':
        {
        'url': 'https://github.com/Veil-Framework/Veil',
        'command': './Install.sh -c',
        },
    'phishing-frenzy':
        {
        'install': '/var/www',
        'url': 'https://github.com/pentestgeek/phishing-frenzy',
        },
    }

BACKUP_FILES = [
    USER_PATH + '/.local/',
    USER_PATH + '/.msf4/',
    ]

# Dotfiles are backed up, so these are exclusions
# This list can also include any files that may exist in
# folders you specify in the BACKUP_FILES section you wish to skip
EXCLUDE_FILES = [
    '.ICEauthority',
    '.pulse-cookie',
    '.rnd',
    '.rvmrc',
    '.xsession-errors',
    '.xsession-errors.old',
    '.zlogin',
    '.zshrc',
    ]
