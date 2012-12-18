#!/usr/bin/env python
"""
top-level wrapper for FSL quality assurance project

"""

import numpy as N
import nibabel as nib
import sys,os
import argparse

def parse_arguments(testing=False):
    # parse command line arguments
    # setting testing flag to true will turn off required flags
    # to allow manually running without command line flags

    required=not testing
    parser = argparse.ArgumentParser(description='fsl-qa')

    parser.add_argument('-d', dest='featdir',
        required=required,help='feat dir for analysis')

    return parser.parse_args()


class featdir:
    # this is the main class for the project
    # defines class and methods for working with feat directories
    # this one should define a generic feat directory class that
    # extends to both .feat and .gfeat directories
    # we can then create separate derived classes for each

    def load(self,dir):
        # specify a feat directory and check to make sure it's valid
        if not os.path.exists(dir):
            print '%s does not exist'%dir
            return None
        if not os.path.exists(os.path.join(dir,'design.fsf')):
            print '%s does not appear to be a valid feat dir ('%dir
            return None





def main():
    args=parse_arguments(testing=True)

if __name__ == '__main__':
    main()
