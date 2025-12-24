TEMPLATE = \
r"""#!/usr/bin/env bash

set -e

################################################################################

VENV_NAME=$(basename "$0")
VENV_DIR=__venv__

GREEN="\e[42m"
NORMAL="\e[0m"

################################################################################

function box()
{
   echo -e "${GREEN}################################################################################${NORMAL}"
   echo -e "${GREEN}# $@${NORMAL}"
   echo -e "${GREEN}################################################################################${NORMAL}"
}

################################################################################

box "Creating & activating $VENV_NAME virtual environment"

python3 -m venv $VENV_DIR

source $VENV_DIR/bin/activate

if [[ -f requirements.txt ]]
then
   box "Installing/Upgrading packages"

   python3 -m pip install -r requirements.txt
fi

if [[ -f ${VENV_NAME} ]]
then
    box "Running ${VENV_NAME} script"

    python3 ./${VENV_NAME}.py "$@"

    deactivate
fi
"""

