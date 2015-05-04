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
        <pid>$Neos::jobid</pid>
</$job_partition>
MESSAGE
}

sub salome_main {
    if ($ENV{'ENVIRONMENT'} eq "BATCH") {
	print_salome_job_infos ();
    }

    # Run Xvnc (with appropriate parameters)
    my $xvnc = sprintf(Neos::get_param('cmd'),
                       Neos::get_display (),
                       Neos::get_param('default_resolution'),
                       Neos::get_rfbport ()
                );
    my $cmd1 = sprintf("%s > %s 2>&1 &",
                      $xvnc,
                      Neos::get_param('x_logfile')
                );

    # Run Salome RunSession command
    my $runSession = sprintf("%s/runSession", Neos::get_param1('salome_path'));
    my $cmd = sprintf("%s mpirun -x DISPLAY=:%s %s/bin/pvserver --connect-id=%s -rc -ch=%s >>%s 2>&1 &",
                      $runSession,
                      $display_number,
                      Neos::get_param1('salome_path'),
                      $display_number,
		      Neos::get_ip_pvclient (),
                      Neos::get_param('x_logfile')
	);

    if ($firstnode eq hostname) {
        system ($cmd1);
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

sub salome_srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
	print_salome_job_infos ();
    }
}

sub salome_clean {
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

Neos::insert_action('main', \&salome_main);
Neos::insert_action('srun', \&salome_srun);
Neos::insert_action('epilog', \&salome_clean);

1;
