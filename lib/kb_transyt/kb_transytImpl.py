# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
import transyt_wrapper as tw
from installed_clients.KBaseReportClient import KBaseReport
import uuid
import shutil

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

        transyt_process = tw.transyt_wrapper(token=ctx['token'], params=params, config=self.config,
                                             callbackURL=self.callback_url, shared_folder=self.shared_folder)
        transyt_process.run_transyt()
        #output = transyt_process.process_output()
        #output = transyt_process.get_report()

        report = KBaseReport(self.callback_url)
        objects_created = []
        model_fix_path = self.shared_folder + '/transporters_sbml.xml'

        transyt_process.fix_transyt_model("/kb/module/conf/transyt.xml", model_fix_path)
        shutil.copyfile("/kb/module/conf/report_template.html", self.shared_folder + '/report.html')

        report_params = {
            'direct_html_link_index': 0,
            'workspace_name': transyt_process.get_workspace_name(),
            'report_object_name': 'run_transyt_' + uuid.uuid4().hex,
            'objects_created': [],
            'html_links': [
                {'name': 'report', 'description': 'Report', 'path': self.shared_folder + '/report.html'}
            ],
            'file_links': [
                {'name': params['model_id'] + ".xml", 'description': 'desc', 'path': model_fix_path}
            ]
        }

        print(report_params)

        report_info = report.create_extended_report(report_params)

        #report_info = report.create(
        #    {
        #        'report': {
        #            'objects_created': objects_created,
        #            'text_message': "SOME TEXT MESSAGE HERE"
        #        },
        #        'workspace_name': transyt_process.get_workspace_name()
        #    })

        # report_info = report.create(report_params)

        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
            'fbamodel_id': params['model_id']
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
