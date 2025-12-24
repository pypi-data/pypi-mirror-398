## ###
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
##
# ReOxide manager GUI frontend
# @category: ReOxide
# @runtime PyGhidra
import sys
from subprocess import Popen

if len(sys.argv) > 1:
    from reoxide.manage.gui import run_gui
    exit(run_gui())
else:
    Popen([sys.executable, __file__, '1'])
