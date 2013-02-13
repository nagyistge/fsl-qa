#!/usr/bin/env python
"""
top-level wrapper for FSL quality assurance project

"""

# IN THE END, BREAK OUT INTO A MODULE
# for now we can leave it as a mixed script/class def

# some general notes from code review:
# make thigns as immutable as possible - use frozen sets

import numpy
import nibabel
import sys,os
import argparse
# read_fsl_design is badly named as it reads an fsf file
import mvpa2.misc.fsl.base
import fnmatch, string
from featdir import Featdir


def parse_arguments():
    # parse command line arguments
    # setting testing flag to true will turn off required flags
    # to allow manually running without command line flags

    parser = argparse.ArgumentParser(description='fsl-qa')

    parser.add_argument('-d', dest='featdir',
        required=True,help='feat dir for analysis')
    parser.add_argument('-v',dest='verbose',action='store_true',
        default=False,help='verbose output')
    return parser.parse_args()


def load_dir(directory_name):
    """
    specify a directory and return its file listing
    Throws IOError if directory doesn't exist
    """
    if not os.path.exists(directory_name):
        raise IOError('%s does not exist'%directory_name)

    directory_list=os.listdir(directory_name)
    file_list=frozenset([i for i in directory_list if os.path.isfile(os.path.join(directory_name,i))])
    dir_list=frozenset([i for i in directory_list if os.path.isdir(os.path.join(directory_name,i))])

    return file_list,dir_list


            
def main():
    args=parse_arguments()
    #fdir="/home1/02105/msandan/data/task001_run001.feat"
    #fdir='/corral-repl/utexas/poldracklab/openfmri/shared2/ds006A/sub001/model/model001/task001_run001.feat'
    #fdir='/Users/poldrack/data/fmriqa_data/task001_run001.feat'

    featdir=Featdir(args.featdir,args.verbose)

    featdir.run_all_checks()
    
    print ''
    
    if len(featdir.warnings)>0:
        print "Warnings:"
        for w in featdir.warnings:
            print w
    else:
        print "Successfully completed - No warnings"
  
if __name__ == '__main__':
    main()
