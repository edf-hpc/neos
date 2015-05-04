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

Neos::load_config($Neos::config_dump);

# Job parameters
my $job_partition = Neos::get_partition ();
my $constraint = Neos::get_constraint ();
my $hostlist = Neos::host_list ();
my $firstnode = Neos::first_node ();

sub xfce4_main {
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
        system (sprintf("%s --display=:%s >/dev/null 2>&1 &",
                        Neos::get_param('xfce4_session_manager'),
                        Neos::get_display ()
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

sub xfce4_srun {
    # Print information about the present job (When not in "BATCH" mode)
    if ($ENV{'ENVIRONMENT'} ne "BATCH") {
        Neos::print_job_infos (Neos::get_param('password'));
    }
}

sub xfce4_clean {
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

Neos::insert_action('main', \&xfce4_main);
Neos::insert_action('srun', \&xfce4_srun);
Neos::insert_action('epilog', \&xfce4_clean);

1;
