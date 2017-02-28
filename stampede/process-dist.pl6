#!/usr/bin/env perl6

subset File of Str where *.IO.f;

sub MAIN (
    File :$dist-file!,
    Str :$out-dir=$*CWD.Str,
    Str :$alias-file=""
) {
    my %alias;
    if $alias-file && $alias-file.IO.f {
        my $fh = open $alias-file;
        my @hdr = $fh.get.split(/\t/);
        %alias = $fh.lines.map(*.split(/\t/)).flat.pairup;;
    }

    my $basename = $dist-file.IO.basename;
    my $in       = open $dist-file, :r;
    my $out-file = $*SPEC.catfile(
                   $out-dir || $dist-file.IO.dirname, $basename ~ '.fixed');
    my $out = open $out-file, :w;

    for 1..* Z $in.lines -> ($i, $line) {
        my @flds = $line.split(/\t/);

        if $i == 1 {
            my $query = @flds.shift;
            $query   ~~ s/^ '#'//;
            my @files = @flds.map(&remove_suffix).map({%alias{$_} || $_});
            @flds     = ($query, @files).flat;
        }
        else {
            my $file = remove_suffix(@flds.shift);
            next if all(@flds) == 1;
            @flds[0] = %alias{ $file } || $file;
        }

        $out.put(@flds.join("\t"));
    }

    $in.close;
    $out.close;

    put "Done, see '$out-file'";
}

sub remove_suffix($file) {
    my $basename = $file.IO.basename;
    $basename   ~~ s/\.msh $//;
    $basename   ~~ s/\.gz $//;
    #$basename   ~~ s/\.fa(st[aq])? $//;
    $basename;
}
