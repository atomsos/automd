#!/bin/bash


CURDIR="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
if [ "$(uname)" == "Darwin" ]; then
        CURDIR="$(dirname -- "${BASH_SOURCE[0]}")"
        if [ "$CURDIR" == "." ]; then
                CURDIR="$(dirname -- "${PWD}/${BASH_SOURCE[0]}")"
        fi
fi


CURDIR=$(cd $CURDIR; pwd)
echo $CURDIR


export PYTHONPATH=$CURDIR:$PYTHONPATH
export PATH=$CURDIR/bin:$PATH
