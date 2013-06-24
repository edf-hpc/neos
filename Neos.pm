#!/usr/bin/perl
# Copyright © 2013 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: Mehdi Dogguy <mehdi.dogguy@edf.fr>
#          Antonio Russo <antonio-externe.russo@edf.fr>
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

package Neos;

# Be good
use strict;

my $VERSION = '0.1';

                                       # Dependencies (Debian packages)
                                       # ==============================
use File::Path qw(make_path);          # perl-modules
use File::chmod;                       # libfile-chmod-perl
use Config::General qw(ParseConfig);   # libconfig-general-perl
use Slurm;                             # libslurm-perl
use Crypt::GeneratePassword qw(chars); # libcrypt-generatepassword-perl

# Load the Switch..Case construct
use Switch;

# Read configuration files
my %config = ParseConfig (
    -ConfigFile => "/etc/neos.conf",
    -SplitPolicy => "equalsign",
    -InterPolateEnv => 1
    );

sub get_param {
    my ($param) = @_;
    return $config{$param};
}

sub set_param {
    my ($param, $value) = @_;
    $config{$param} = $value;
}

# Current user (note that visu.cfg uses $ENV{'USER'})
my $user = getlogin();

# Slurm informations about current job
my $slurm = Slurm::new();
my $job_infos = $slurm->load_job($ENV{'SLURM_JOB_ID'});

# Initialization
sub init {
  make_path($config{'base_dir'}, {
    verbose => 0,
    mode => 0700,
  });
}

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
    }
    if ($partition ~~ @partitions_conf) {
	return 1;
    } else {
	return 0;
    }
}

sub get_constraint {
    my @constval = ("vncres", "pvserver");
    my ($feature, $level) = split(/:/, get_job_detail ('features'), 2);
    if ($feature ~~ @constval) {
        return $feature;
    } else {
        return $constval[0];
    }
}

sub get_vncres {
    my ($feature, $level) = split(/:/, get_job_detail ('features'), 2);
    switch ($level) {
        case 1 { return "1280x1024" }
        case 2 { return "1680x1050" }
        case 3 { return "1920x1200" }
        else   { return "1024x768"  }
    }
}

sub gen_password {
    my $password = chars(8, 8, ["a".."z", "A".."Z", 0..9]);
    open (VNCPASS, sprintf("> %s", $config{'vauthfile'}));
    my $encrypted_text = `echo "$password" | $config{'vnc_passwd'}`;
    print VNCPASS $encrypted_text;
    close (VNCPASS);
    chmod(0600, $config{'vauthfile'});
    return $password;
}

sub store_ip_pvclient {
    open (IPPVCLIENT, sprintf("> %s", $config{'ip_pvclient'}));
    my @ssh_params = split /\s+/, $ENV{'SSH_CONNECTION'};
    print IPPVCLIENT $ssh_params[0];
    close (IPPVCLIENT);
    chmod(0600, $config{'ip_pvclient'});
}

my $magic_number = 59530;

sub get_rfbport {
    return ($ENV{'SLURM_JOB_ID'} % $magic_number + $magic_number);
}

sub get_display {
    return ($ENV{'SLURM_JOB_ID'} % $magic_number + 1);
}

sub get_x_pid {
    my $pid_cmd = sprintf("ps aux | egrep \"Xvnc :%s\" | grep -v grep | awk '{print \$2}'", get_display ());
    my $x_pid = `$pid_cmd`;
    chomp($x_pid);
    return $x_pid;
}

sub kill_x_vnc {
    my $x_pid = get_x_pid ();
    if ($x_pid != "") {
        kill 9, $x_pid;
    }
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

    print <<MESSAGE;

<$job_partition>
        <nodes> 
                <node>$hostlist</node>
        </nodes>
        <vncserver>
                <node>$firstnode</node>
                <ipaddress>$iprin</ipaddress>
                <session>$rfbport</session>
                <password>$password</password>
        </vncserver>
        <enddatetime>$daylimit</enddatetime>"
        <pid>$jobid</pid>"
</$job_partition>
MESSAGE
}
1;
