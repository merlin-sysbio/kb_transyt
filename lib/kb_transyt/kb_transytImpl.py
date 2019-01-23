# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
from installed_clients.WorkspaceClient import Workspace
from installed_clients.KBaseReportClient import KBaseReport
import cobra
import cobrakbase
import cobrakbase.core.cobra_to_kbase
import kb_transyt_module
import uuid
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
        output_model_id = "test_model"
        kbase = cobrakbase.KBaseAPI(ctx['token'], config=self.config)

        #print(os.environ)
        #print(self.config)
        #ws_client = Workspace(self.config['workspace-url'], token=ctx['token'])
        #def get_object(wclient, oid, ws):
        #    res = wclient.get_objects2({"objects" : [{"name" : oid, "workspace" : ws}]})
        #    return res["data"][0]["data"]

        ws = params['workspace_name']
        genome = kbase.get_object(params['genome_id'], ws)

        def to_faa(kgenome):
            faa_features = []
            for feature in kgenome['features']:
                if 'protein_translation' in feature:
                    faa_features.append('>' + feature['id'] + '\n' + feature['protein_translation'])
            
            return '\n'.join(faa_features)

        faa = to_faa(genome)
        print('write genome FAA (bytes):', len(faa))
        with open('/kb/module/data/transyt/genome/genome.faa', 'w') as f:
            f.write(faa)
            f.close()

        #detect taxa
        ref_data = kbase.get_object_info_from_ref(genome['taxon_ref'])
        ktaxon = kbase.get_object(ref_data['infos'][0][1], ref_data['infos'][0][7])
        scientific_lineage = ktaxon['scientific_lineage']
        taxa_id = ktaxon['taxonomy_id']

        model = None
        if 'model_id' in params and len(params['model_id'].strip()) > 0:
            model = kbase.get_object(params['model_id'], ws)

        
        model_path = "../genome/simGCF_000005845.2.new_template.xml"

        if not model == None:
            print('converting model to sbml')
            cobra_model = cobrakbase.convert_kmodel(model, {})
            model_path = "/kb/module/data/transyt/genome/model.xml"
            cobra.io.write_sbml_model(cobra_model, model_path)

        import subprocess

        java = "/opt/jdk/jdk-11.0.1/bin/java"
        transyt_jar = "newTransytTest.jar"

        genome_path = "../genome/genome.faa"
        
        #genome_path = "../genome/GCF_000005845.2_ASM584v2_protein.faa"
        
        transyt_subprocess = [java, "-jar", transyt_jar, str(taxa_id), genome_path, model_path]

        working_dir= "/kb/module/data/transyt/jar"

        subprocess.check_call(transyt_subprocess, cwd=working_dir)

        out_sbml_path = '/kb/module/data/transyt/genome/sbmlResult_qCov_0.8_eValThresh_1.0E-50.xml'
        objects_created = []

        #check of genome file exists 
        model_fix_path = self.shared_folder + '/transporters_sbml.xml'
        if os.path.exists(out_sbml_path):
            #fix sbml header for cobra
            
            sbml_tag = '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" fbc:required="false" groups:required="false" level="3" sboTerm="SBO:0000624" version="1" xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2" xmlns:groups="http://www.sbml.org/sbml/level3/version1/groups/version1">'
            model_tag = '<model extentUnits="substance" fbc:strict="true" id="transyt" metaid="transyt" name="transyt" substanceUnits="substance" timeUnits="time">'
            xml_data = None
            xml_fix = ""
            with open(out_sbml_path, 'r') as f:
                xml_data = f.readlines()
            for l in xml_data:
                if l.strip().startswith('<sbml'):
                    xml_fix += sbml_tag
                elif l.strip().startswith('<model'):
                    xml_fix += model_tag
                else:
                    xml_fix += l
            if not xml_data == None:
                with open(model_fix_path, 'w') as f:
                    f.writelines(xml_fix)
            #fix otherthing
            tmodel = cobra.io.read_sbml_model(model_fix_path)
            out_model = cobrakbase.core.cobra_to_kbase.convert_to_kbase(tmodel.id, tmodel)
            out_model['genome_ref'] = ws + '/' + params['genome_id']
            kbase.save_object(output_model_id, ws, 'KBaseFBA.FBAModel', out_model)
            objects_created.append(output_model_id)

        #/kb/module/data/transyt/genome/sbmlResult_qCov_0.8_eValThresh_1.0E-50.xml

        text_message = "{} {} {} {}".format(params['genome_id'], genome['id'], scientific_lineage, taxa_id)
        with open(self.shared_folder + '/report.html', 'w') as f:
            f.write('<p>' + text_message + '</p>')

        report = KBaseReport(self.callback_url)

        report_params = {
            'direct_html_link_index' : 0,
            'workspace_name' : ws,
            'report_object_name' : 'runMemote_' + uuid.uuid4().hex,
            'objects_created' : [],
            'html_links' : [
                {'name' : 'report', 'description' : 'Report', 'path' : self.shared_folder + '/report.html' }
            ],
            'file_links' : [
                {'name' : params['model_id'] + ".xml", 'description' : 'desc', 'path' : model_fix_path + "/model.xml"}
            ]
        }

        print(report_params)

        
        report_info = report.create(
            {
                'report': {
                    'objects_created': objects_created,
                    'text_message': text_message
                    },
                'workspace_name': ws
            })
 
        #report_info = report.create(report_params)

        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
            'fbamodel_id' : output_model_id
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
