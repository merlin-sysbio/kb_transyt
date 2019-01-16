# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
from installed_clients.WorkspaceClient import Workspace
from installed_clients.KBaseReportClient import KBaseReport
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

        print(os.environ)
        print(self.config)
        ws_client = Workspace(self.config['workspace-url'], token=ctx['token'])
        def get_object(wclient, oid, ws):
            res = wclient.get_objects2({"objects" : [{"name" : oid, "workspace" : ws}]})
            return res["data"][0]["data"]

        genome = get_object(ws_client, params['genome_id'], params['workspace_name'])

        report = KBaseReport(self.callback_url)
        report_info = report.create({'report': {'objects_created':[],
                                                'text_message': params['genome_id'] + ", " +genome['id']},
                                                'workspace_name': params['workspace_name']})

        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
        }
        print('returning:', output)
        #END run_transyt

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
