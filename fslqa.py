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


# class methods should be lower_lower
#

class Featdir:
    """
    this is the main class for the project
    defines class and methods for working with feat directories
    this one should define a generic feat directory class that
    extends to both .feat and .gfeat directories
    we can then create separate derived classes for each
    """

    # CLASS VARIABLE DEFINITIONS

    dir = '' # main feat directory
    fsf = [] # dict containing fsf info
    desmtx = [] # design matrix
    featfiles=[] # set of files in feat dir
    featdir_subdirs=[] # subdirs in feat dir
    has_statsdir=False
    has_regdir=False
    has_regstddir=False
    statsfiles=[] # set of files in stats dir
    regfiles=[] # set of files in reg dir
    regstdfiles=[] # set of files in reg_standard dir
    warnings=[] # list of warnings that appear after running program
    VIF=[]
    evs={}
    contrasts={}
    nevs=[]
    ncontrasts=[]
    VIFthresh=5.0
    maskvox=[]
    verbose=False
    
    def __init__(self,dir,verbose):
        # INIT SHOULD CALL LOADFEAT
        self.verbose=verbose
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
            self.get_evs()
            self.get_contrasts()
        else:
            self.analysisLevel=self.fsf['fmri(level)']


    # set up some methods related to loading and checking directories

    def is_valid_featdir(self):
        """
        check wither self.dir is a valid feat dir by looking for design.fsf
        """
        if not os.path.exists(os.path.join(self.dir,'design.fsf')):
            return False
        else:
            if self.verbose:
                print 'design.fsf is valid'
            return True

    def load_fsf(self):
        """
        load the design.fsf file
        """
        fsffile=os.path.join(self.dir,'design.fsf')
        if os.path.exists(fsffile):
            # load design.fsf into a dict
            self.fsf=mvpa2.misc.fsl.base.read_fsl_design(fsffile)
            if self.verbose:
                print 'loaded design.fsf file successfully'
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
            if self.verbose:
                print 'loaded design.mat file successfully'
        else:
            raise IOError('problem reading design.mat')


    def get_evs(self):
        """
        get all of teh evs
        TBD: figure out which are confounds
        """
        self.nevs=self.fsf['fmri(evs_orig)']
        for ev in range(1,self.nevs+1):
            self.evs[ev]={'title':self.fsf['fmri(evtitle%d)'%ev],
                          'tempfilt':self.fsf['fmri(tempfilt_yn%d)'%ev],
                          'shape':self.fsf['fmri(shape%d)'%ev],
                          'deriv':self.fsf['fmri(deriv_yn%d)'%ev],
                          'convolve':self.fsf['fmri(convolve%d)'%ev]
                         }
        if self.verbose:
            print 'found %d evs'%len(self.evs)
            
    def get_contrasts(self):
        """ 
        get all of the contrasts
        """
        self.ncontrasts=self.fsf['fmri(ncon_orig)']
        for con in range(1,self.ncontrasts+1):
            self.contrasts[con]={'title':self.fsf['fmri(conname_orig.%d)'%con],
                                 'contrast':[],
                                 }
            for ev in range(1,self.nevs+1):
                self.contrasts[con]['contrast'].append(self.fsf['fmri(con_orig%d.%d)'%(con,ev)])
            
        if self.verbose:
            print 'found %d contrasts'%len(self.contrasts)

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
        self.check_logfiles()
        self.check_datalength()
 

    def check_deleted_volumes(self):
        """
        check whether volumes were deleted
        this is only necessary if they estimated the motion parameters
        ahead of time and are adding them manually, since delete volumes
        deletes volumes for the beginning, but if the motion parameter series
        are too long, it trims from the end.
        """
        if self.fsf['fmri(ndelete)']==0:
            if self.verbose:
                print 'no deleted volumes'
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
        warn=False
        if boldfile.find('_mcf')>0 and self.fsf['fmri(mc)']==1:
            self.warnings.append('_mcf file was used as input but mcflirt was turned on')
            warn=True
        if boldfile.find('_brain')>0 and self.fsf['fmri(bet_yn)']==1:
            self.warnings.append('_brain file was used as input but bet was turned on')
            warn=True
            
        if self.verbose and not warn:
            print 'preprocessing settings appear to match data'


    def check_model_settings(self):
        """
        - Verify that prewhitening was used
        - Verify that both data and all EVs in design matrix have been highpass filtered
        """

        # check for highpass filtering of data and EVs

        # check for prewhitening
        if self.fsf['fmri(prewhiten_yn)']==0:
            self.warnings.append('prewhitening was not turned on')
            
        elif self.verbose:
            print 'prewhitening is enabled'


    def check_design(self):
        """
        - Calculate the VIFs (Variance Inflation Factors) for the full design matrix
        to check for collinearities. This approach is nice as it will catch
        collinearities that arise from linear combinations of EVs, not just
        pairwise correlations of evs. see http://en.wikipedia.org/wiki/Variance_inflation_factor

        - Verify that the double gamma HRF was used for evs that use convolution.
        The single gamma is the default, but can lead to overestimates in activation.

        """
        # compute VIF from self.desmtx.mat by iteration
        # through all of the parameters (columns).
        # Iterate through each column of the matrix by 
        # using a boolean array index with compress.
	    # Collect each parameter's VIF in par_vif using 
        # the getVIF helper function below.
        mtx=self.desmtx.mat
    	numcol=mtx.shape[1]
        self.VIF=numpy.zeros(numcol)
        badVIF=False
        
        for par in range(numcol):
            idxcol=[i for i in range(numcol) if i != par]
            restMat=mtx[:,idxcol]
            parCol=mtx[:,par]
            self.VIF[par]=self.getVIF(restMat,parCol)
            if self.VIF[par]>self.VIFthresh:
                self.warnings.append('VIF over threshold (%f): col %d'%(self.VIF[par],par))
                badVIF=True
        if self.verbose and not badVIF:
            print 'VIF values all below threshold (max = %f, thresh = %f)'%(numpy.max(self.VIF), self.VIFthresh)
        # check for double gamma HRF
        # Gather corresponding keys, check if one-to-one.
        # Assuming evtitle and convolve go from 1-10
        conKeys=[]
        evKeys=[]
        badHRF=False
        for key in self.fsf.keys():
            if ("convolve" in key and "_" not in key):
                conKeys.append(key)
            elif "evtitle" in key:
                evKeys.append(key)
        if len(conKeys) != len(evKeys):
            self.warnings.append("The number of convolve keys does not equal the "+
				 " number of evtitle keys in fsf dictionary")

        idxMotPar=[(ev.split(")")[0][len(ev)-2:]) for ev in evKeys if "motpar" in self.fsf[ev]]
        for key in conKeys:
            ikey=key.split(")")[0][len(key)-2:]
            if ikey in idxMotPar:
                if not self.fsf[key] == 0:
                    self.warning.append("HRFwarning: %s should be set to 0 " %key)
                    badHRF=True
            else:
                if not self.fsf[key] == 3:
                    self.warning.append(" HRFwarning: %s should be set to 3 " %key)
                    badHRF=True
        if not badHRF and self.verbose:
            print 'HRF settings appear correct'
            
            
    def getVIF(self,mat,col):
        """
        Helper function to calculate VIF for given col using matrix(matrix w/o col)
        """
	
        #Initially written by Dr.Poldrack
        r1=numpy.linalg.lstsq(mat,col)
        ss_total=numpy.sum((col-numpy.mean(col))**2)
        y_pred=numpy.dot(mat,r1[0])
        ss_model=numpy.sum((y_pred - numpy.mean(y_pred))**2)
        ss_resid=numpy.sum((col - y_pred)**2)
        rsquared=1.0-(ss_resid/ss_total)
        vif=1.0 / (1.0 - rsquared)

        return vif
	

    def check_stats_files(self):
        """
        Check files in the stats directory
        - make sure that the number of stats files matches that expected from fsf
        - check each pe and zstat file to make sure it's not all zeros
        """
        
        badPE=False
        for ev in range(1,self.nevs+1):
            imgfile=os.path.join(self.dir,'stats/pe%d.nii.gz'%ev)
            try:
                img=nibabel.load(imgfile)
                data=img.get_data()
                self.evs[ev]['has_pe']=1
                self.evs[ev]['pe_min']=numpy.min(data)
                self.evs[ev]['pe_max']=numpy.max(data)
                
            except:
                self.evs[ev]['has_pe']=0
                self.warnings.append('problem loading %s'%imgfile)
                badPE=True
        if self.verbose and not badPE:
            print 'all pe images are present and loadable'
        
        badcon=False
        for con in range(1,self.ncontrasts+1):
            imgfile=os.path.join(self.dir,'stats/zstat%d.nii.gz'%con)
            try:
                img=nibabel.load(imgfile)
                data=img.get_data()
                self.contrasts[con]['has_z']=1
                self.contrasts[con]['z_min']=numpy.min(data)
                self.contrasts[con]['z_max']=numpy.max(data)
                
            except:
                self.contrasts[con]['has_z']=0
                self.warnings.append('problem loading %s'%imgfile)
                badcon=True
        if self.verbose and not badcon:
            print 'all zstats are present and loadable'
     

    def check_mask(self):
        """
        Check mask to make sure it has an appropriate number of nonzero voxels
        """
        # Mark: load the mask.nii.gz file from the featdir
        # and count the number of nonzero entries in the matrix
        
        try:
            maskimgfile=os.path.join(self.dir,'mask.nii.gz')
            img=nibabel.load(maskimgfile)
            data=img.get_data()
            self.maskvox=numpy.sum(data>0)
            if self.verbose:
                print 'mask loaded (%d in-mask voxels)'%self.maskvox
        except:
            self.warnings.append('problem loading mask')


    def check_logfiles(self):
        """
        load log file and check for any errors or warnings
        """
        logfile=os.path.join(self.dir,'report_log.html')
        try:
            f=open(logfile)
            log=[l.strip() for l in f.readlines()]
            f.close()
        except:
            self.warnings.append('problem opening logfile')
            log=[]
            
        badlog=False
        for l in log:
            if l.lower().find('error')>-1 or l.lower().find('warning')>-1 or l.lower().find('exception')>-1:
                self.warnings.append('LOG: '+l)
                badlog=True
                
        if self.verbose and not badlog:
            print 'No errors or warnings found in report_log.html'
        
    def check_datalength(self):
        """
        check length of data file and make sure it matches setting in fsf
        """
        
        datafilename=os.path.join(self.dir,'filtered_func_data.nii.gz')
        try:
            datafile=nibabel.load(datafilename)
            nvols_actual=datafile.shape[3]
        except:
            self.warnings.append('problem loading filtered_func_data')
            return
        
        if not nvols_actual == self.fsf['fmri(npts)']:
            self.warnings.append('nvols_actual (%d) does not match npts in fsf (%d)'%(nvols_actual,self.fsf['fmri(npts)']))
        elif self.verbose:
            print 'nvols_actual (%d) matches npts in fsf (%d)'%(nvols_actual,self.fsf['fmri(npts)'])
            
            
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
