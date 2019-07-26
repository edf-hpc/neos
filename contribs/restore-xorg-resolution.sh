#!/bin/sh
#
# This script is used to restore Xorg default resolution during Slurm slurmd
# prolog. A user can change the resolution of Xorg using xrandr during a job
# graphical session (using a NEOS scenario or not). This script make sure the
# resolution is back to its default value before a new job starts on the node.
#
# This script is run as root by slurmd daemon on first job or job step
# initiation on that node.

# Restart Xorg servers to renew graphical sessions if no other job exists 

if [ -z "$(find "/sys/fs/cgroup/cpuset" -name "job_*" -type d)" ]; then
       logger "Restarting Xorg@0 ans Xorg@1 servers"       
       systemctl restart xorg@0.service 2>/dev/null
       systemctl restart xorg@1.service 2>/dev/null
fi

logger "Restoring Xorg default resolution for display :0 :1"
xrandr -d :0 --fb 1024x768 2>/dev/null
xrandr -d :1 --fb 1024x768 2>/dev/null
