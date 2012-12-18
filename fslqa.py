#!/usr/bin/env python
"""
top-level wrapper for FSL quality assurance project

"""

import numpy as N
import nibabel as nib
import sys,os
import argparse
from mvpa2.misc.fsl.base import read_fsl_design,FslEV3,FslGLMDesign

## {{{ http://code.activestate.com/recipes/52664/ (r2)
def Walk( root, recurse=0, pattern='*', return_folders=0 ):
    """
    walk through a directory tree
    """
    import fnmatch, os, string

    # initialize
    result = []

    # must have at least root folder
    try:
        names = os.listdir(root)
    except os.error:
        return result

    # expand pattern
    pattern = pattern or '*'
    pat_list = string.splitfields( pattern , ';' )

    # check each file
    for name in names:
        fullname = os.path.normpath(os.path.join(root, name))

        # grab if it matches our pattern and entry type
        for pat in pat_list:
            if fnmatch.fnmatch(name, pat):
                if os.path.isfile(fullname) or (return_folders and os.path.isdir(fullname)):
                    result.append(fullname)
                continue

        # recursively scan other folders, appending results
        if recurse:
            if os.path.isdir(fullname) and not os.path.islink(fullname):
                result = result + Walk( fullname, recurse, pattern, return_folders )

    # modified from example to remove root from results
    result_stripped=[i.replace(root,'') for i in result]
    return result_stripped

## end of http://code.activestate.com/recipes/52664/ }}}

def parse_arguments(testing=False):
    # parse command line arguments
    # setting testing flag to true will turn off required flags
    # to allow manually running without command line flags

    required=not testing
    parser = argparse.ArgumentParser(description='fsl-qa')

    parser.add_argument('-d', dest='featdir',
        required=required,help='feat dir for analysis')

    return parser.parse_args()


class featdirClass:
    # this is the main class for the project
    # defines class and methods for working with feat directories
    # this one should define a generic feat directory class that
    # extends to both .feat and .gfeat directories
    # we can then create separate derived classes for each

    def __init__(self,dir):
        self.dir = dir
        self.fsf = []
        self.featfiles=[]
        self.featfiles_dict={}
        self.has_statsdir=False
        self.has_regdir=False
        self.statsfiles=[]
        self.regfiles=[]

    def loadFeatDir(self):
        """
        specify a feat directory and get its file listing
        """
        if not os.path.exists(self.dir):
            print '%s does not exist'%self.dir
            return None
        if not os.path.exists(os.path.join(self.dir,'design.fsf')):
            print '%s does not appear to be a valid feat dir :'%self.dir
            return None

        self.featfiles=Walk(self.dir)

    def loadFeatRegDir(self):
        """
        specify a feat directory and get its file listing
        """
        regdir=os.path.join(self.dir,'reg')
        if not os.path.exists(regdir):
            print 'reg dir %s does not exist'%regdir
            return None
        self.has_regdir=True
        self.regfiles=[i.replace('/','') for i in Walk(regdir)]

    def loadFeatStatsDir(self):
        """
        specify a feat directory and get its file listing
        """
        statsdir=os.path.join(self.dir,'stats')
        if not os.path.exists(statsdir):
            print 'stats dir %s does not exist'%statsdir
            return None
        self.has_statsdir=True
        self.statsfiles=[i.replace('/','') for i in Walk(statsdir)]

    def parseFeatDir(self):
        """
        parse the featfiles and identify what's there
        """
        # create a dictionary of all the files
        for f in self.featfiles:
            self.featfiles_dict[f]=1



    def loadFSF(self):
        """
        load the design.fsf file
        """
        fsffile=os.path.join(self.dir,'design.fsf')
        if os.path.exists(fsffile):
            self.fsf=read_fsl_design(fsffile)
        else:
            print 'problem reading design.fsf'


#def main():
#    args=parse_arguments(testing=True)
fdir='/Users/poldrack/Dropbox/data/hiddencity/ER_run1_mcf.feat/'
featdir=featdirClass(fdir)
featdir.loadFeatDir()
featdir.loadFeatStatsDir()
featdir.loadFeatRegDir()

featdir.loadFSF()
featdir.parseFeatDir()


#if __name__ == '__main__':
#    main()
