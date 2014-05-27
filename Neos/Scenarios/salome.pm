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
my $jobid = $ENV{'SLURM_JOB_ID'};
my $display_number = Neos::get_display ();

sub print_salome_job_infos() {
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
        <salome_server>
                <node>$firstnode</node>
                <ipaddress>$iprin</ipaddress>
                <port>$display_number</port>
        </salome_server>
        <enddatetime>$daylimit</enddatetime>
        <pid>$jobid</pid>
</$job_partition>
MESSAGE
}

sub salome_main {
    if ($ENV{'ENVIRONMENT'} eq "BATCH") {
	print_salome_job_infos ();
    }

    # Run Salome RunSession command
    my $xvnc = sprintf(Neos::get_param('salome_x'),
                       Neos::get_display (),
                       Neos::get_vncres(),
                       Neos::get_rfbport ()
                );
    my $cmdx = sprintf("%s >> %s 2>&1 &",
                      $xvnc,
                      Neos::get_param('x_logfile')
                );
    system ($cmdx);

    my $runSession = sprintf("%s/runSession", Neos::get_param1('salome_path'));
    my $cmd = sprintf("%s mpirun -x DISPLAY=:%s -x LIBGL_ALWAYS_INDIRECT=y pvserver -rc -ch=%s >>%s 2>&1 &",
                      $runSession,
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
}

sub salome_srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
	print_salome_job_infos ();
    }
}

sub salome_clean {
    my @files = (Neos::get_param('x_logfile')
        );

    unlink @files;

    Neos::kill_program ("pvserver");
}

Neos::insert_action('main', \&salome_main);
Neos::insert_action('srun', \&salome_srun);
Neos::insert_action('epilog', \&salome_clean);

1;
