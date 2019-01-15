#BEGIN_HEADER
import os
from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.WorkspaceClient import Workspace
#END_HEADER
#BEGIN_CLASS_HEADER
#END_CLASS_HEADER
#BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
#END_CONSTRUCTOR
#BEGIN run_transyt
        print(params)

        ws_client = Workspace(self.callback_url, token=ctx['token'])
        #get genome
        def get_object(wclient, oid, ws):
            res = wclient.get_objects2({"objects" : [{"name" : oid, "workspace" : ws}]})
            return res["data"][0]["data"]

        genome = get_object(ws_client, params['genome_id'], params['workspace_name'])
        print(genome.keys())

        #make FAA

        def to_faa(kgenome):
                faa_features = []
                for feature in kgenome['features']:
                        faa_features.append('>' + feature['id'] + '\n' + feature['protein_translation'])
                        #print(feature)
                        #break
                
                return '\n'.join(faa_features)

        faa = to_faa(genome)
        with open('/kb/module/data/transyt/genome/genome.faa', 'w') as f:
                f.write(faa)
                f.close()

        #detect taxa

        #ref_data = kbase.get_object_info_from_ref(kgenome['taxon_ref'])
        #ktaxon = kbase.get_object(ref_data['infos'][0][1], ref_data['infos'][0][7])
        #scientific_lineage = ktaxon['scientific_lineage']
        #taxa_id = ktaxon['taxonomy_id']
        


        #get model (if exists)
        #/opt/jdk/jdk-11.0.1/bin/java -jar transytTest.jar 
        # 511145 
        # ./../genome/GCF_000005845.2_ASM584v2_protein.faa 
        # ./../genome/simGCF_000005845.2.new_template.xml
        #cobrakbase make sbml
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
