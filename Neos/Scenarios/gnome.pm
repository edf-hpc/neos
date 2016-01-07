#!/usr/bin/perl
###############################################################################
#  Copyright (C) 2013-2014 EDF SA                                             #
#                                                                             #
#  This software is a computer program whose purpose is to ease execution     #
#  of defined sequence of actions on a Slurm cluster. For example, starting   #
#  a graphical environment for users, prepare and start a visualization       #
#  framework (like Paraview or Salome) for remote use.                        #
#                                                                             #
#  This software is governed by the CeCILL  license under French law and      #
#  abiding by the rules of distribution of free software.  You can  use,      #
#  modify and/ or redistribute the software under the terms of the CeCILL     #
#  license as circulated by CEA, CNRS and INRIA at the following URL          #
#  "http://www.cecill.info".                                                  #
#                                                                             #
#  As a counterpart to the access to the source code and  rights to copy,     #
#  modify and redistribute granted by the license, users are provided only    #
#  with a limited warranty  and the software's author,  the holder of the     #
#  economic rights,  and the successive licensors  have only  limited         #
#  liability.                                                                 #
#                                                                             #
#  In this respect, the user's attention is drawn to the risks associated     #
#  with loading,  using,  modifying and/or developing or reproducing the      #
#  software by the user in light of its specific status of free software,     #
#  that may mean  that it is complicated to manipulate,  and  that  also      #
#  therefore means  that it is reserved for developers  and  experienced      #
#  professionals having in-depth computer knowledge. Users are therefore      #
#  encouraged to load and test the software's suitability as regards their    #
#  requirements in conditions enabling the security of their systems and/or   #
#  data to be ensured and,  more generally, to use and operate it in the      #
#  same conditions as regards security.                                       #
#                                                                             #
#  The fact that you are presently reading this means that you have had       #
#  knowledge of the CeCILL license and that you accept its terms.             #
###############################################################################

package Neos::Scenarios;

# Be good
#use strict;

use POSIX ":sys_wait_h";
use Sys::Hostname;
use Neos;;

Neos::load_config($Neos::config_dump);

sub main {
    # Do not run anything if not run on the firstnode.
    return unless (Neos::first_node () eq hostname);

    # Find out which display to use
    my $display = Neos::get_display ();
    if (Neos::get_job_detail('shared') eq 0) {
        $display = "0";
    }

    # General parameters
    my @pids;
    my $xauth_file = Neos::get_param('xauthfile');
    my $x_logfile = Neos::get_param('x_logfile');

    # Create auth file
    my $cookie = `mcookie`;
    open HANDLE, ">>$xauth_file";
    close HANDLE;
    my $xauth_cmd = sprintf ("xauth -f %s -q add :%s MIT-MAGIC-COOKIE-1 %s >/dev/null 2>&1",
                             $xauth_file,
                             $display,
                             $cookie
        );
    system($xauth_cmd);

    # Print information about the present job (Only in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} eq "BATCH") {
        Neos::print_job_infos (Neos::get_param('password'));
    }

    open STDOUT, '>>$x_logfile';
    open STDERR, '>&STDOUT';

    # Xvfb
    my $x_cmd = sprintf ("Xvfb :%s -once -screen 0 %sx24+32 -auth %s",
                         $display,
                         Neos::get_resolution(),
                         Neos::get_param('xauthfile')
        );
    my $x_pid;
    if ($x_pid = fork) {
        push(@pids, $x_pid);
        Neos::set_param('x_pid', $x_pid);
    } else {
        exec $x_cmd unless ($display eq 0);
        do {
            sleep (1);
        } while (1 eq 1);
    }

    # Start graphical session
    my $session_cmd = "dbus-launch --exit-with-session gnome-session";
    my $session_pid;
    if ($session_pid = fork) {
        push(@pids, $session_pid);
        Neos::set_param('session_pid', $session_pid);
    } else {
        $ENV{DISPLAY} = sprintf (":%s", $display);
        $ENV{XAUTHORITY} = Neos::get_param('xauthfile');
        exec $session_cmd;
    }

    sleep(1);

    # Run x11vnc (with appropriate parameters)
    my $vnc_cmd = sprintf (Neos::get_param('cmd'),
                           Neos::get_resolution(),
                           $display,
                           Neos::get_rfbport ()
        );
    my $vnc_pid;
    if ($vnc_pid = fork) {
        push(@pids, $vnc_pid);
        Neos::set_param('vnc_pid', $vnc_pid);
    } else {
        exec $vnc_cmd;
    }

    # Force re-dump to store newly created PIDs
    Neos::force_dump_config ();

    # Monitor status of the Xvnc process, and exit as soon as it is
    # killed or walltime is reached.
    my $finished = 0;
    do {
        sleep (1);
        $finished++ if (waitpid($session_pid, WNOHANG) < 0);
        $finished++ if (waitpid($vnc_pid, WNOHANG) < 0);
        $finished++ if (waitpid($x_pid, WNOHANG) < 0);
    } while ($finished eq 0);

    kill 'TERM', @pids;
}

sub srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
        Neos::print_job_infos (Neos::get_param('password'));
    }
}

sub clean {
    use Scalar::Util qw(looks_like_number);
    my @pids = (Neos::get_param('vnc_pid'), Neos::get_param('session_pid'), Neos::get_param('x_pid'));
    foreach my $pid (@pids) {
        kill 'TERM', $pid if (looks_like_number($pid));
    }
}

Neos::insert_action('main', \&main);
Neos::insert_action('srun', \&srun);
Neos::insert_action('epilog', \&clean);

1;
