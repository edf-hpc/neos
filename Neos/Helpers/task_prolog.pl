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

use strict;
use Sys::Hostname;
use Neos;

Neos::load_config();

my $job_partition = Neos::get_partition ();

if (Neos::is_good_partition($job_partition)) {
    Neos::init ();

    if (Neos::get_job_detail('shared') eq 0) {
        my $cmd = sprintf("xrandr -d :0 --fb %s", Neos::get_resolution());
        system($cmd);
    }

    Neos::load_scenario(Neos::get_scenario_name ());
    Neos::run_action('task');
}
