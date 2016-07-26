#!/bin/sh
#
# This script is used to restore Xorg default resolution during Slurm slurmd
# prolog. A user can change the resolution of Xorg using xrandr during a job
# graphical session (using a NEOS scenario or not). This script make sure the
# resolution is back to its default value before a new job starts on the node.
#
# This script is run as root by slurmd daemon on first job or job step
# initiation on that node.

xrandr -d :0 --fb 1024x768
