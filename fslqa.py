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



def parse_arguments(testing=False):
    # parse command line arguments
    # setting testing flag to true will turn off required flags
    # to allow manually running without command line flags

    required=not testing
    parser = argparse.ArgumentParser(description='fsl-qa')

    parser.add_argument('-d', dest='featdir',
        required=required,help='feat dir for analysis')

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


# class methods should be lower_lower
#

class Featdir:
    """
    this is the main class for the project
    defines class and methods for working with feat directories
    this one should define a generic feat directory class that
    extends to both .feat and .gfeat directories
    we can then create separate derived classes for each

    DESCRIBE METHODS AND USAGE
    """

    # CLASS VARIABLE DEFINITIONS

    dir = ''        # main feat directory
    fsf = []        # dict containing fsf info
    desmtx = []     # design matrix
    featfiles=[]    # set of files in feat dir
    featdir_subdirs=[]    # subdirs in feat dir
    has_statsdir=False
    has_regdir=False
    has_regstddir=False
    statsfiles=[]   # set of files in stats dir
    regfiles=[]     # set of files in reg dir
    regstdfiles=[]     # set of files in reg_standard dir
    warnings=[]         # list of warnings

    def __init__(self,dir):
        # INIT SHOULD CALL LOADFEAT
        if not os.path.exists(dir):
            raise IOError('%s does not exist'%dir)
        self.dir=dir
        if not self.is_valid_featdir():
            raise IOError('%s is not a valid featdir'%dir)

        #create frozen sets to prevent later modification

        self.featfiles,self.featdir_subdirs=load_dir(dir)

        if os.path.exists(os.path.join(dir,'stats')):
            self.has_statsdir=True
            self.statsfiles=frozenset(load_dir(os.path.join(dir,'stats')))

        if os.path.exists(os.path.join(dir,'reg')):
            self.has_regdir=True
            self.regfiles=frozenset(load_dir(os.path.join(dir,'reg')))

        if os.path.exists(os.path.join(dir,'reg_standard')):
            self.has_regstddir=True
            self.regstdfiles=frozenset(load_dir(os.path.join(dir,'reg_standard')))


        self.load_fsf()
        if self.fsf['fmri(level)']==1:
            self.analysisLevel=1
            self.load_desmtx()
        else:
            self.analysisLevel=2


    # set up some methods related to loading and checking directories

    def is_valid_featdir(self):
        """
        check wither self.dir is a valid feat dir by looking for design.fsf
        """
        if not os.path.exists(os.path.join(self.dir,'design.fsf')):
            return False
        else:
            return True

    def load_fsf(self):
        """
        load the design.fsf file
        """
        fsffile=os.path.join(self.dir,'design.fsf')
        if os.path.exists(fsffile):
            # load design.fsf into a dict
            self.fsf=mvpa2.misc.fsl.base.read_fsl_design(fsffile)
        else:
            raise IOError('problem reading design.fsf')

    def load_desmtx(self):
        """
        load the design.mat file
        """
        desmatfile=os.path.join(self.dir,'design.mat')
        if os.path.exists(desmatfile):
            # load design.mat into a design matrix object (matrix is in self.desmtx.mat)
            self.desmtx=mvpa2.misc.fsl.base.FslGLMDesign(desmatfile)
        else:
            raise IOError('problem reading design.mat')


    # check lots of different analysis features
    # whenever a problem is found, append a warning message to
    # self.warnings

    def run_all_checks(self):
        self.check_deleted_volumes()
        self.check_preproc_settings()
        self.check_model_settings()
        self.check_design()
        self.check_stats_files()
        self.check_mask()

    def check_deleted_volumes(self):
        """
        check whether volumes were deleted
        this is only necessary if they estimated the motion parameters
        ahead of time and are adding them manually, since delete volumes
        deletes volumes for the beginning, but if the motion parameter series
        are too long, it trims from the end.

        """
        if featdir.fsf['fmri(ndelete)']==0:
            return False
        else:
            self.warnings.append('ndelete is >0: if you added motion params manually, check their length')
            return True

    def check_preproc_settings(self):
        """
        If input data include _brain and or _mcf_brain extensions,
        double check that the user turned off mcflirt and bet in the GUI.
        """
        boldfile=os.path.basename(self.fsf['feat_files'])
        if boldfile.find('_mcf')>0 and self.fsf['fmri(mc)']==1:
            self.warnings.append('_mcf file was used as input but mcflirt was turned on')
        if boldfile.find('_brain')>0 and self.fsf['fmri(bet_yn)']==1:
            self.warnings.append('_brain file was used as input but bet was turned on')

    def check_model_settings(self):
        """
        - Verify that prewhitening was used
        - Verify that both data and all EVs in design matrix have been highpass filtered
        """

        # check for highpass filtering of data and EVs

        # Mark - please write

        # check for prewhitening
        if self.fsf['fmri(prewhiten_yn)']==0:
            self.warnings.append('prewhitening was not turned on')

    def check_design(self):
        """
        - Calculate the VIFs (Variance Inflation Factors)  for the full design matrix
        to check for collinearities.  This approach is nice as it will catch
        collinearities that arise from linear combinations of EVs, not just
        pairwise correlations of evs. see http://en.wikipedia.org/wiki/Variance_inflation_factor

        - Verify that the double gamma HRF was used for evs that use convolution.
        The single gamma is the default, but can lead to overestimates in activation.

        """
        return
        # compute VIF from self.desmtx.mat

        # Mark - please write

        # check for double gamma HRF

        # Mark - please write

    def check_stats_files(self):
        """
        Check files in the stats directory
        - make sure that the number of stats files matches that expected from fsf
        - check each nii.gz file to make sure it's not all zeros
        """
        return

    def check_mask(self):
        """
        Check mask to make sure it has an appropriate number of nonzero voxels
        """
        return

#def main():
#    args=parse_arguments(testing=True)
fdir='/Users/poldrack/Dropbox/data/fmriqa_data/task001_run001.feat/'
featdir=Featdir(fdir)
featdir.run_all_checks()

#if __name__ == '__main__':
#    main()
