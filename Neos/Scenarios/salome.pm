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
my $hostlist = Neos::host_list ();
my $firstnode = Neos::first_node ();

sub salome_main {
    return unless ($firstnode eq hostname);

    if ($ENV{'ENVIRONMENT'} eq "BATCH") {
	Neos::print_job_infos ();
    }

    my $display = Neos::get_display ();
    my $vglrun = "vglrun -display :0";
    if (Neos::get_job_detail('shared') eq 0) {
       $display = "0";
       $vglrun = "";
    }

    # Run pvserver command
    my $runSession = sprintf("%s/runSession", Neos::get_param1('salome_path'));
    my $cmd = sprintf("%s mpirun -x DISPLAY=:%s %s %s/bin/pvserver --connect-id=%s -rc -ch=%s >>%s 2>&1 &",
                      $runSession,
                      $display,
                      $vglrun,
                      Neos::get_param('salome_path'),
                      $display,
                      Neos::get_ip_pvclient (),
                      Neos::get_param('x_logfile')
	);


    system ($cmd);

    # Monitor status of the paraview process, and exit as soon as it is
    # killed or walltime is reached. Same as for Xvnc...
    Neos::wait_for_process("pvserver");
    Neos::kill_program ("pvserver");
    Neos::slurm_terminate_job ();
}

sub salome_srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
	Neos::print_job_infos ();
    }
}

sub salome_clean {
    Neos::kill_program ("pvserver");
}

Neos::insert_action('main', \&salome_main);
Neos::insert_action('srun', \&salome_srun);
Neos::insert_action('epilog', \&salome_clean);

1;
