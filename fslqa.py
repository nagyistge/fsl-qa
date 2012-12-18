"""
top-level wrapper for FSL quality assurance project

"""

# some general notes from code review:
# make thigns as immutable as possible - use frozen sets

import numpy
import nibabel
import sys,os
import argparse
# read_fsl_design is badly named as it reads an fsf file
import mvpa2.misc.fsl.base
import fnmatch, string



def parse_arguments(testing=False):
    # parse command line arguments
    # setting testing flag to true will turn off required flags
    # to allow manually running without command line flags

    required=not testing
    parser = argparse.ArgumentParser(description='fsl-qa')

    parser.add_argument('-d', dest='featdir',
        required=required,help='feat dir for analysis')

    return parser.parse_args()

# IN THE END, BREAK OUT INTO A MODULE
# for now we can leave it as a mixed script/class def

# class methods should be lower_lower
#

def load_dir(directory_name):
    """
    specify a directory and return its file listing

    Throws IOError if directory doesn't exist

    """
    if not os.path.exists(directory_name):
        raise IOError('%s does not exist'%directory_name)

    directory_list=os.listdir(directory_name)
    good_list=[i for i in directory_list if os.path.isfile(os.path.join(directory_name,i))]
    return good_list


class Featdir:
    """
    this is the main class for the project
    defines class and methods for working with feat directories
    this one should define a generic feat directory class that
    extends to both .feat and .gfeat directories
    we can then create separate derived classes for each

    DESCRIBE METHODS AND USAGE
    """

    # MOVE VARIABLES DEFINITIONS TO HERE
    # REMOVE SELF
    dir = ''
    fsf = []
    featfiles=[]
    featfiles_dict={}
    has_statsdir=False
    has_regdir=False
    statsfiles=[]
    regfiles=[]

    def __init__(self,dir):
        # INIT SHOULD CALL LOADFEAT
        if not os.path.exists(dir):
            raise IOError('%s does not exist'%dir)
        self.dir=dir
        if not self.is_valid_featdir():
            raise IOError('%s is not a valid featdir'%dir)

        self.featfiles=load_dir(dir)

        if os.path.exists(os.path.join(dir,'stats')):
            self.has_statsdir=True
            self.statsfiles=load_dir(os.path.join(dir,'stats'))

        if os.path.exists(os.path.join(dir,'reg')):
            self.has_regdir=True
            self.regfiles=load_dir(os.path.join(dir,'reg'))


    # get rid of these specific loaders in favor of a single more powerful loader
    # also replace Walk with os.listdir() since we don't need recursive
    # check with os.path.isfile()

    def is_valid_featdir(self):
        """
        check wither self.dir is a valid feat dir by looking for design.fsf
        """
        if not os.path.exists(os.path.join(self.dir,'design.fsf')):
            return False
        else:
            return True

    def parseFeatDir(self):
        """
        parse the featfiles and identify what's there
        """
        # create a dictionary of all the files
        for f in self.featfiles:
            self.featfiles_dict[f]=1
        # create featfiles as an frozen set
        # instead use if ... in set(list) to find things in featfiles



    def loadFSF(self):
        """
        load the design.fsf file
        """
        fsffile=os.path.join(self.dir,'design.fsf')
        if os.path.exists(fsffile):
            # load design.fsf into a dict
            self.fsf=read_fsl_design(fsffile)
        else:
            # raise...
            print 'problem reading design.fsf'


#def main():
#    args=parse_arguments(testing=True)
fdir='/Users/poldrack/Dropbox/data/hiddencity/ER_run1_mcf.feat/'
featdir=Featdir(fdir)

#if __name__ == '__main__':
#    main()
