#BEGIN_HEADER
import os
from installed_clients.KBaseReportClient import KBaseReport
#END_HEADER
#BEGIN_CLASS_HEADER
#END_CLASS_HEADER
#BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
#END_CONSTRUCTOR
#BEGIN run_transyt
        print(params)
        report = KBaseReport(self.callback_url)
        report_info = report.create({'report': {'objects_created':[],
                                                'text_message': params['genome_id']},
                                                'workspace_name': params['workspace_name']})
        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
        }
#END run_transyt
#BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
#END_STATUS
