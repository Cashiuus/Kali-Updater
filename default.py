#!/usr/bin/env python
#
#
# default.py
#
# If you make changes to this file, rename it to "settings.py"

import os


BACKUP_PATH = os.path.join(os.path.expanduser('~'), 'Backups')
usr = os.path.expanduser('~')

dotfiles_ignore = [
    '.ICEauthority',
    '.rnd',
    '.rvmrc',
    '.xsession-errors',
    '.xsession-errors.old',
    '.zlogin',
    '.zshrc',
    ]



BACKUP_FILES = [
    ]
