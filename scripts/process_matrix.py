#!/usr/bin/env python3
"""process Mash distance matrix"""

# Author: Ken Youens-Clark <kyclark@email.arizona.edu>

import argparse
import csv
import json
import os
import sqlite3

# --------------------------------------------------
def get_args():
    """argparser"""
    parser = argparse.ArgumentParser(description='Fix Mash matrix')
    parser.add_argument('-m', '--matrix', help='Mash matrix', type=str,
                        metavar='FILE', required=True)
    parser.add_argument('-p', '--precision', type=int, metavar='NUM',
                        default=4, help='Number of significant digits')
    parser.add_argument('-o', '--out_dir', help='Output directory',
                        type=str, metavar='DIR', default='')
    parser.add_argument('-a', '--alias', help='Alias file',
                        type=str, metavar='FILE', default='')
    parser.add_argument('-d', '--annot_db', help='Annotation database',
                        type=str, metavar='DB',
                        default='/work/05066/imicrobe/iplantc.org/data/imicrobe-annotdb/annots.db')
    return parser.parse_args()

# --------------------------------------------------
def main():
    """main"""
    args = get_args()
    matrix = args.matrix
    out_dir = args.out_dir
    precision = args.precision
    alias = args.alias
    annot_db = args.annot_db

    if not os.path.isfile(matrix):
        print('--matrix "{}" is not valid'.format(matrix))
        exit(1)

    if len(out_dir) == 0:
        out_dir = os.path.dirname(os.path.abspath(matrix))

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    if not 1 <= precision <= 10:
        print('--precision "{}" should be between 1-10'.format(matrix))
        exit(1)

    if not os.path.isfile(annot_db):
        print('--annot_db "{}" is not valid'.format(annot_db))
        exit(1)

    aliases = dict()
    if len(alias) > 0:
        if os.path.isfile(alias):
            with open(alias) as csvfile:
                reader = csv.DictReader(csvfile, delimiter='\t')
                for row in reader:
                    if set(('name', 'alias')) <= set(row):
                        aliases[row['name']] = row['alias']
                    else:
                        print('--alias file should contain name/alias')
                        exit(1)
        else:
            print('--alias "{}" is not valid'.format(alias))
            exit(1)

    def good_name(file):
        """get a better name for the sample"""
        base = os.path.basename(file)
        return aliases[base] if base in aliases else base

    near_fh = open(os.path.join(out_dir, 'nearness.tab'), 'w')
    dist_fh = open(os.path.join(out_dir, 'distance.tab'), 'w')
    matrix_fh = open(matrix, 'r')
    db = sqlite3.connect(annot_db)
    sql = 'select annots from annot where sample_id=?'
    annots = []
    fld_names = set()

    for line_num, line in enumerate(matrix_fh):
        line = line.rstrip()
        flds = line.split('\t')
        first = flds.pop(0)

        # header line, replace the first ("#query") with empty string
        if line_num == 0:
            out = '\t'.join([''] + list(map(good_name, flds)))
            near_fh.write(out + '\n')
            dist_fh.write(out + '\n')
        else:
            if not all([v == '1' for v in flds]):
                sample_id = os.path.basename(os.path.dirname(first))
                dist_fh.write('\t'.join([sample_id] + flds) + '\n')
                inverted = list(map(lambda n: str(1 - float(n)), flds))
                near_fh.write('\t'.join([sample_id] + inverted) + '\n')

                for row in db.execute(sql, (sample_id,)):
                    annot = json.loads(row[0])
                    annots.append(annot)
                    for key in annot.keys():
                        fld_names.add(key)
    #
    # Print headers for output
    #
    fld_names.remove('sample_id')
    cols = ['sample_id'] + sorted(fld_names)
    annot_file = os.path.join(out_dir, 'annotations.tab')
    annot_fh = open(annot_file, 'wt')
    annot_fh.write('\t'.join(cols) + '\n')
    for annot in annots:
        vals = []
        for col in cols:
            val = annot.get(col)
            if val is None:
                val = ''
            vals.append(val)

        annot_fh.write('\t'.join(vals) + '\n')

    annot_fh.close()

    print('Done, see nearness/distance/annotations in "{}"'.format(out_dir))

# --------------------------------------------------
if __name__ == '__main__':
    main()
