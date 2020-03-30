import cobrakbase
import subprocess
import os
import cobra
from installed_clients.KBaseReportClient import KBaseReport
from cobra_to_kbase_patched import convert_to_kbase

class transyt_wrapper:

    def __init__(self, token=None, params=None, config=None, deploy_database=True, callbackURL=None):

        self.params = params
        self.config = config
        self.callback_url = callbackURL
        #self.inputs_path = '/Users/davidelagoa/Desktop/test/processingDir/'
        self.inputs_path = '/workdir/processingDir/'
        self.results_path = '/workdir/resultsDir/'
        #self.results_path = '/Users/davidelagoa/Desktop/test/resultsDir/'
        self.java = '/opt/jdk/jdk-11.0.1/bin/java'
        self.transyt_jar = '/opt/transyt/transyt.jar'
        self.ref_database = 'ModelSEED'     #check if it only supports modelseed

        self.ws = None
        self.taxonomy_id = None
        self.genome_id = None
        self.scientific_lineage = None

        self.kbase = cobrakbase.KBaseAPI(token, config=self.config)

        if deploy_database:
            self.deploy_neo4j_database()


    def run_transyt(self, model_obj_name = None, genome_obj_name = None, narrative_id = None):

        genome = None
        compounds = None

        if self.ws is None:
            self.ws = narrative_id

        if narrative_id is None:
            genome, compounds = self.retrieve_params_data()
        else:
            genome, compounds = self.retrieve_test_data(model_obj_name, genome_obj_name, narrative_id)

        if not os.path.exists(self.inputs_path):
            os.makedirs(self.inputs_path)

        self.inputs_preprocessing(genome, compounds)

        if not os.path.exists(self.results_path):
            os.makedirs(self.results_path)

        transyt_subprocess = subprocess.Popen([self.java, "-jar", "--add-exports",
                                               "java.base/jdk.internal.misc=ALL-UNNAMED",
                                               "-Dio.netty.tryReflectionSetAccessible=true", "-Dworkdir=/workdir",
                                               "-Dlogback.configurationFile=/kb/module/conf/logback.xml",
                                               "-Xmx4096m", self.transyt_jar, "3", self.inputs_path,
                                               self.results_path])

        exit_code = transyt_subprocess.wait()

        print("jar process finished! exit code: " + str(exit_code))


    def retrieve_test_data(self, model_obj_name, genome_obj_name, narrative_id):

        if self.params is None:
            self.params = {'genome_id': genome_obj_name}

        genome = self.kbase.get_object(genome_obj_name, narrative_id)

        model_compounds = None

        if model_obj_name is not None:
            model_compounds = self.kbase.get_object(model_obj_name, narrative_id)['modelcompounds']

        return genome, model_compounds


    def retrieve_params_data(self):

        self.ws = self.params['workspace_name']

        genome = self.kbase.get_object(self.params['genome_id'], self.ws)

        if 'model_id' in self.params and len(self.params['model_id'].strip()) > 0:
            kbase_model = self.kbase.get_object(self.params['model_id'], self.ws)
            model_compounds = kbase_model['modelcompounds']

        return genome, model_compounds


    def inputs_preprocessing(self, genome, model_compounds):

        # detect taxa
        ref_data = self.kbase.get_object_info_from_ref(genome['taxon_ref'])
        ktaxon = self.kbase.get_object(ref_data.id, ref_data.workspace_id)
        self.scientific_lineage = ktaxon['scientific_lineage']
        self.taxonomy_id = ktaxon['taxonomy_id']

        if model_compounds is not None:
            self.compounds_to_txt(model_compounds)

        self.genome_to_faa(genome)
        self.params_to_file()


    def compounds_to_txt(self, model_compounds):

        path = self.inputs_path + 'metabolites.txt'

        compounds_list = []

        for compound in model_compounds:
            mseed_id = compound['id'].split("_")[0]

            if mseed_id not in compounds_list:
                compounds_list.append(mseed_id)

        with open(path, 'w') as f:
            f.write('\n'.join(compounds_list))
            f.close()


    def genome_to_faa(self, genome):
        faa_features = []
        for feature in genome['features']:
            if 'protein_translation' in feature and feature['protein_translation'] is not '':
                faa_features.append('>' + feature['id'] + '\n' + feature['protein_translation'])

        with open(self.inputs_path + 'genome.faa', 'w') as f:
            f.write('\n'.join(faa_features))
            f.close()


    def params_to_file(self):

        with open(self.inputs_path + 'params.txt', 'w') as f:

            for key in self.params:
                f.write(key + "\t" + str(self.params[key]) + "\n")

            f.write('taxID' + "\t" + str(self.taxonomy_id) + "\n")
            f.write('reference_database' + "\t" + self.ref_database)
            f.close()


    def process_output(self):

        output_model_id = self.params['output_name']

        if self.ws is None:         #delete when tests are complete
            self.ws = "davide:narrative_1585245719372"
            self.params = {"genome_id": "Escherichia_coli_str._K-12_substr._MG1655"}

        out_sbml_path = self.results_path + "/results/transyt.xml"

        objects_created = []

        model_fix_path = self.results_path + '/transporters_sbml.xml'
        if os.path.exists(out_sbml_path):
            # fix sbml header for cobra

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

            if xml_data is not None:
                with open(model_fix_path, 'w') as f:
                    f.writelines(xml_fix)

            tmodel = cobra.io.read_sbml_model(model_fix_path)
            out_model = convert_to_kbase(tmodel.id, tmodel)

            out_model['genome_ref'] = self.ws + '/' + self.params['genome_id']

            self.kbase.save_object(output_model_id, self.ws, 'KBaseFBA.FBAModel', out_model)

        text_message = "{} {} {} {}".format(self.params['genome_id'], self.genome_id, self.scientific_lineage,
                                            self.taxonomy_id)

        with open(self.results_path + '/report.html', 'w') as f:
            f.write('<p>' + text_message + '</p>')

        report = KBaseReport(self.callback_url)

        report_info = report.create(
            {
                'report': {
                    'objects_created': objects_created,
                    'text_message': text_message
                },
                'workspace_name': self.ws
            })

        #report_info = report.create(report_params)

        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
            'fbamodel_id': output_model_id
        }
        #print('returning:', output)

        return output


    def deploy_neo4j_database(self):

        subprocess.Popen(["/opt/neo4j/neo4j-community-4.0.2/bin/neo4j", "start"])
