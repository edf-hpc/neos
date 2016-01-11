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

package Neos;

# Be good
use strict;

our $VERSION = '0.3';
my $mdp;

                                       # Dependencies (Debian packages)
                                       # ==============================
use File::Path qw(make_path);          # perl-modules
use File::chmod;                       # libfile-chmod-perl
use Config::General qw(ParseConfig);   # libconfig-general-perl
use Slurm;                             # libslurm-perl
use Crypt::GeneratePassword qw(chars); # libcrypt-generatepassword-perl
use Storable qw(freeze thaw);          # perl-modules
use File::Slurp qw(read_file write_file); # libfile-slurp-perl

use Data::Dumper;

# Load the Switch..Case construct
use Switch;

# Debug utility
sub debug {
    my ($msg) = @_;
    if ($ENV{'NEOS_DEBUG'} == 1) {
	print ("W: $msg\n");
    }
}

# Read configuration files
my $config_file = "/etc/neos.conf";
my $config_dump = "$ENV{'HOME'}/.neos/config_$ENV{'SLURM_JOB_ID'}";
our %config= ();

# Initialization
sub init {
  make_path($config{'base_dir'}, {
    verbose => 0,
    mode => 0700,
  });
}

sub get_config_job_file() {
    return $config_dump;
}

sub read_config_file {
    my ($cfg) = @_;
    debug("Reading configuration file $cfg");
    %Neos::config = ParseConfig (
	-ConfigFile => $cfg,
	-SplitPolicy => "equalsign",
	-InterPolateEnv => 1
	);
    if ($config{'base_dir'} ne "") {
	init ();
	$config_dump = "$config{'base_dir'}/config_$ENV{'SLURM_JOB_ID'}";
    }
}

sub config_file_handler {
    my ($opt_name, $opt_value) = @_;
    read_config_file($opt_value);
}

sub dump_config {
    my $file = do { @_ ? shift : get_config_job_file() };
    if (! -e $file) {
	my $yaml = freeze(\%Neos::config);
	write_file($file, { binmode => ':raw' }, $yaml);
    }
}

sub force_dump_config {
    unlink (get_config_job_file());
    dump_config (get_config_job_file());
}

sub load_config {
    my $file = do { @_ ? shift : get_config_job_file() };
    if (-e $file) {
	my $yaml = read_file($file, { binmode => ':raw' });
	%Neos::config = %{thaw($yaml)};
    } else {
	debug ("W: Can't find configuration dump: \"$file\".\n");
    }
}

if (-e $config_file) {
    read_config_file ($config_file);
} else {
    debug ("Configuration file $config_file not found!");
}

sub get_param {
    my ($param) = @_;
    return $config{$param};
}

sub get_param1 {
    my ($default) = @_;
    if (exists($config{param1}) && $config{param1} ne "") {
	return $config{param1};
    } else {
	return get_param($default);
    }
}

sub set_param {
    my ($param, $value) = @_;
    $config{$param} = $value;
}

# Resolution
sub get_default_resolution {
    return get_param('default_resolution');
}

sub get_resolution {
    my ($default) = @_;
    $default = get_default_resolution() if ($default eq "");
    my $res = get_param('resolution');
    if ($res eq "") {
        return $default;
    } else {
        return $res;
    }
}

# Scenario actions: main, srun, task, epilog
sub get_default_scenario {
    return get_param('default_scenario');
}

sub load_scenario {
    my ($scenario) = @_;
    $scenario = Neos::get_default_scenario () if $scenario eq "";
    my $mod = "Neos::Scenarios::$scenario";
    $mod=~s/-/_/g;
    eval "use $mod;";
    if ($@) {
	die("E: Unable to load scenario $scenario: $@");
    }
}

my %scenario_actions = ();

sub insert_action {
    my ($action_name, $action_sub) = @_;
    $scenario_actions{$action_name} = $action_sub;
}

sub run_action {
    my ($action_name) = @_;
    my $scenario_name = get_scenario_name ();
    if (exists $scenario_actions{$action_name}) {
	$scenario_actions{$action_name}->();
    } else {
	debug ("Action $action_name from scenario $scenario_name is not defined!");
    }
}

# Current user (note that visu.cfg uses $ENV{'USER'})
my $user = getlogin();

# Slurm informations about current job
my $slurm = Slurm::new();
my $job_infos = $slurm->load_job($ENV{'SLURM_JOB_ID'});

sub get_job_detail {
    my ($detail) = @_;
    return @{@$job_infos{job_array}}[0]->{$detail};
}

sub nodes_list {
    my $hl = Slurm::Hostlist::create($ENV{'SLURM_NODELIST'});
    $hl->uniq();
    return $hl;
}

sub first_node {
    my $hl = nodes_list();
    return $hl->shift();
}

sub host_list {
    my $hl = nodes_list();
    my $result = "";
    my @list = ();
    while(my $host = $hl->shift()) {
        push (@list, $host);
    }
    return join ",", @list;
}

sub get_realname {
    my ($uid, $pass, $uid, $gid, $quota, $comment, $name, $dir, $shell, $expire) =
        getpwnam($user);
    return $name;
}

sub get_partition {
    return get_job_detail ('partition');
}

sub is_good_partition {
    my ($partition) = @_;
    my @partitions_conf = split /,/, get_param('partitions');
    foreach (@partitions_conf) {
	s/^\s+|\s+$//g;
        return 1 if ($partition eq $_);
    }
    return 0;
}

sub get_scenario_name {
    my ($scenario) = do { @_ ? shift : "" };
    if ($scenario ne "") {
	return $scenario;
    } else {
	my $constval = "scenario";
	my ($feature, $level) = split(/:/, get_job_detail ('features'), 2);
	if ($feature eq $constval) {
	    return $level;
	} else {
	    return get_default_scenario ();
	}
    }
}

sub gen_password {
    my $password = chars(8, 8, ["a".."z", "A".."Z", 0..9]);
    my $cmd = sprintf ("$config{'vnc_passwd'} -storepasswd %s %s >>%s 2>&1", $password, $config{'vauthfile'}, $config{'x_logfile'});
    system($cmd);
    $mdp = $password;
    return $mdp;
}

sub store_ip_pvclient {
    open (IPPVCLIENT, sprintf("> %s", $config{'ip_pvclient'}));
    my @ssh_params = split /\s+/, $ENV{'SSH_CONNECTION'};
    print IPPVCLIENT $ssh_params[0];
    close (IPPVCLIENT);
    chmod(0600, $config{'ip_pvclient'});
}

sub get_ip_pvclient {
    my $output = `cat $config{'ip_pvclient'}`;
    chomp($output);
    return $output;
}

my $magic_number = 59530;

sub get_rfbport {
    return ($ENV{'SLURM_JOB_ID'} % $magic_number + 1024);
}

sub get_display {
    return ($ENV{'SLURM_JOB_ID'} % $magic_number + 1);
}

sub get_job_endtime {
    return get_job_detail ('end_time');
}

sub get_job_daylimit {
    my $endtime = get_job_endtime ();
    my $res = `date --date "\@$endtime"`;
    chomp($res);
    return $res;
}

sub clean_generated_files {
    my @files = (get_param('vauthfile'),
                 get_param('xauthfile'),
                 get_param('ip_pvclient'),
                 get_param('x_logfile'),
                 get_config_job_file(),
                 sprintf ("/tmp/.X%s-lock", get_display()),
                 sprintf ("/tmp/.X11-unix/X%s", get_display())
        );

    unlink @files;
}

sub slurm_terminate_job {
    my $job_id = $ENV{'SLURM_JOB_ID'};
    if ($job_id ne "") {
        system("scancel $job_id");
    }
}

sub print_job_infos {
    my ($password) = @_;

    my $job_partition = get_partition ();
    my $firstnode = first_node ();
    my $hostlist = host_list ();
    my $daylimit = get_job_daylimit ();
    my $jobid = $ENV{'SLURM_JOB_ID'};
    my $rfbport = get_rfbport ();
    my $iprin;
    chomp($iprin = `grep rin$firstnode /etc/hosts | awk '{print \$1}'`);
    if ($iprin eq '') {
        $iprin = `grep -w $firstnode /etc/hosts | grep -v 127.0.1.1 | awk '{print \$1}'`;
        chomp($iprin);
    }

    #print Data::Dumper->Dump([$job_infos], [qw(job_infos)]);

    my $nodes = "";
    my $hl = nodes_list();
    while(my $host = $hl->shift()) {
       $nodes .= "                <node>$host</node>\n";
    }
    chomp($nodes);
    print <<MESSAGE;
<$job_partition>
        <nodes>
$nodes
        </nodes>
        <config>
                <node>$firstnode</node>
                <ipaddress>$iprin</ipaddress>
                <session>$rfbport</session>
                <password>$mdp</password>
        </config>
        <enddatetime>$daylimit</enddatetime>
        <pid>$jobid</pid>
</$job_partition>
MESSAGE
}

1;
