#!/bin/bash

PYTHON_FILES="../lliurex-mirror-gui/usr/share/lliurex-mirror/lliurex-mirror.py"
UI_FILES="../lliurex-mirror-gui/usr/share/lliurex-mirror/rsrc/lliurex-mirror.ui"

mkdir -p lliurex-mirror/

xgettext $UI_FILES $PYTHON_FILES -o lliurex-mirror/lliurex-mirror.pot

