#!/usr/bin/perl
# Copyright © 2013 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: Mehdi Dogguy <mehdi.dogguy@edf.fr>
#
# This program is free software; you can redistribute in and/or modify
# it under the terms of the GNU General Public License, version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. On Calibre
# systems, the full text of the GNU General Public License can be
# found in `/usr/share/common-licenses/GPL'.

package Neos::Scenarios;

# Be good
use strict;

use Sys::Hostname;
use Neos;;

Neos::load_config($Neos::config_dump);

# Job parameters
my $job_partition = Neos::get_partition ();
my $constraint = Neos::get_constraint ();
my $hostlist = Neos::host_list ();
my $firstnode = Neos::first_node ();

sub gnome_main {
    # Run Xvnc (with appropriate parameters)
    my $xvnc = sprintf(Neos::get_param('cmd'),
                       Neos::get_display (),
                       Neos::get_param('resolution'),
                       Neos::get_rfbport ()
                );
    my $cmd = sprintf("%s > %s 2>&1 &",
                      $xvnc,
                      Neos::get_param('x_logfile')
                );
    system ($cmd);

    # Launch graphical session
    if ($firstnode eq hostname) {
        system (sprintf("DISPLAY=:%s %s >/dev/null 2>&1 &",
                        Neos::get_display (),
                        Neos::get_param('session_manager')
               ));
    }

    # Print information about the present job (Only in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} eq "BATCH") {
        Neos::print_job_infos (Neos::get_param('password'));
    }

    # Monitor status of the Xvnc process, and exit as soon as it is
    # killed or walltime is reached.
    Neos::wait_for_process(Neos::get_param("vnc_x"));
    Neos::kill_program (Neos::get_param("vnc_x"));
    Neos::slurm_terminate_job ();
}

sub gnome_srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
        Neos::print_job_infos (Neos::get_param('password'));
    }
}

sub gnome_clean {
    my @files = (Neos::get_param('vauthfile'),
                 Neos::get_param('xauthfile'),
                 Neos::get_param('ip_pvclient'),
                 Neos::get_param('x_logfile'),
                 sprintf ("/tmp/.X%s-lock", Neos::get_display()),
                 sprintf ("/tmp/.X11-unix/X%s", Neos::get_display())
        );

    unlink @files;

    Neos::kill_program (Neos::get_param("vnc_x"));
}

Neos::insert_action('main', \&gnome_main);
Neos::insert_action('srun', \&gnome_srun);
Neos::insert_action('epilog', \&gnome_clean);

1;
