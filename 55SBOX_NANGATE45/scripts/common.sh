#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PROJECT_ROOT/config.sh"

if [ -n "$CADENCE_SETUP" ] && [ -f "$CADENCE_SETUP" ]; then
    source "$CADENCE_SETUP"
elif [ -n "$CADENCE_SETUP" ]; then
    echo "ERROR: Cadence setup script not found:"
    echo "  $CADENCE_SETUP"
    exit 2
fi

if [ -z "$LIB_FILE" ]; then
    echo "ERROR: LIB_FILE is not set."
    echo "Set it to the Nangate45 Liberty file before running the flow."
    exit 2
fi

if [ ! -f "$LIB_FILE" ]; then
    echo "ERROR: Liberty file not found:"
    echo "  $LIB_FILE"
    exit 2
fi

export PROJECT_ROOT
export LIB_FILE
