#!/bin/bash

# Site-specific paths must be supplied by the user or the batch environment.
# CADENCE_SETUP is optional when the Cadence tools are already on PATH.
export CADENCE_SETUP="${CADENCE_SETUP:-}"
export LIB_FILE="${LIB_FILE:-}"

export GENUS_BIN="${GENUS_BIN:-genus}"
export XRUN_BIN="${XRUN_BIN:-xrun}"
