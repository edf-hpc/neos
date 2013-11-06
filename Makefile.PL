use ExtUtils::MakeMaker;
use Config;

WriteMakefile(
	'NAME'		=> 'Neos',
	'VERSION_FROM'	=> 'Neos.pm',
	'EXE_FILES'     => [ 'neos' ],
	'PMLIBDIRS'     => [ 'Neos' ],
);
