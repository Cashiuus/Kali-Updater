#!/usr/bin/env python
#
# default.py
#
# If you make changes to this file, rename it to "settings.py"

import os
# DEBUGGING
DO_DEBUG = True
BACKUP_PATH = os.path.join(os.path.expanduser('~'), 'Backups')
usr = os.path.expanduser('~')

# Want to fix portmapper issue at boot?
fixportmapper   = False
# This Enables git config option for 'color.ui'
gitcolorize     = True
# Backup user-specified files to an archive file
DO_BACKUPS      = True
# Setup system for Google Chrome; if installed it will update
DO_CHROME       = True
# Update all known Git repositories with 'git pull'
DO_GIT_REPOS    = False
# Update the Veil Framework using its own script
UPDATE_VEIL     = True

# List here folders that you are using for all git repos
# YOUR PRIMARY GIT DIRECTORY SHOULD BE FIRST. This is where
# your git_tools repositories will be cloned if they don't exist
GIT_BASE_DIRS = [
    os.path.expanduser('~/git'),
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


BACKUP_FILES = [
    usr + '/.local/',
    ]
