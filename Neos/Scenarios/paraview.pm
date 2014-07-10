#!/usr/bin/perl
# Copyright © 2014 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: Gregory Hernandez <gregory-externe.hernandez@edf.fr>
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

Neos::load_config();

# Job parameters
my $job_partition = Neos::get_partition ();
my $constraint = Neos::get_constraint ();
my $hostlist = Neos::host_list ();
my $firstnode = Neos::first_node ();
my $display_number = Neos::get_display ();

sub print_job_infos() {
    my $daylimit = Neos::get_job_daylimit ();

    my $iprin;
    chomp($iprin = `grep rin$firstnode /etc/hosts | awk '{print \$1}'`);
    if ($iprin eq '') {
        $iprin = `grep -w $firstnode /etc/hosts | grep -v 127.0.1.1 | awk '{print \$1}'`;
        chomp($iprin);
    }

    my $nodes = "";
    my $hl = Neos::nodes_list();
    while(my $host = $hl->shift()) {
	$nodes .= "                <node>$host</node>\n";
    }
    chomp($nodes);
    print <<MESSAGE;
<$job_partition>
        <nodes>
$nodes
        </nodes>
        <pvserver>
                <node>$firstnode</node>
                <ipaddress>$iprin</ipaddress>
                <port>$display_number</port>
        </pvserver>
        <enddatetime>$daylimit</enddatetime>
        <pid>$Neos::jobid</pid>
</$job_partition>
MESSAGE
}

sub paraview_main {
    if ($ENV{'ENVIRONMENT'} eq "BATCH") {
	print_job_infos ();
    }

    # Run pvserver command
    my $cmd = sprintf("mpirun -x DISPLAY=:0.0 vglrun -d :0.0 pvserver --connect-id=%s -rc -ch=%s >>%s 2>&1 &",
                      Neos::get_display (),
		      Neos::get_ip_pvclient (),
                      Neos::get_param('x_logfile')
	);

    if ($firstnode eq hostname) {
	system ($cmd);
    } else {
	sleep(1);
    }

    # Monitor status of the paraview process, and exit as soon as it is
    # killed or walltime is reached. Same as for Xvnc...
    Neos::wait_for_process("pvserver");
    Neos::kill_program ("pvserver");
    Neos::slurm_terminate_job ();
}

sub paraview_srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
	print_salome_job_infos ();
    }
}

sub paraview_clean {
    my @files = (Neos::get_param('vauthfile'),
                 Neos::get_param('xauthfile'),
                 Neos::get_param('ip_pvclient'),
                 Neos::get_param('x_logfile'),
                 sprintf ("/tmp/.X%s-lock", Neos::get_display()),
                 sprintf ("/tmp/.X11-unix/X%s", Neos::get_display())
        );

    unlink @files;

    Neos::kill_program ("pvserver");
    Neos::slurm_terminate_job ();
}

Neos::insert_action('main', \&paraview_main);
Neos::insert_action('srun', \&paraview_srun);
Neos::insert_action('epilog', \&paraview_clean);

1;
