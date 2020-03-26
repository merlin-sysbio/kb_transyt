# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
from installed_clients.WorkspaceClient import Workspace
from installed_clients.KBaseReportClient import KBaseReport
import cobra
import cobrakbase
import cobrakbase.core.cobra_to_kbase
import uuid
import transyt_wrapper as tw

#END_HEADER


class kb_transyt:
    '''
    Module Name:
    kb_transyt

    Module Description:
    A KBase module: kb_transyt
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "git@github.com:merlin-sysbio/kb_transyt.git"
    GIT_COMMIT_HASH = "a64636d6d2a3fd30fa6dfd2d7aa11b93352431dd"

    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        
        # Any configuration parameters that are important should be parsed and
        # saved in the constructor.
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        self.config = config

        #END_CONSTRUCTOR
        pass


    def run_transyt(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_transyt

        print(params)

        transyt_process = tw.transyt_wrapper(token=ctx['token'], params=params, config=self.config)
        transyt_process.run_transyt()
        output = transyt_process.process_output()

        output = {
            'report_name': "report_name_here",
            'report_ref': "report_info_here",
            'fbamodel_id': "id_here"
        }

        # END run_transyt

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_transyt return value ' +
                             'output is not type dict as required.')
        # return the results

        return [output]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
