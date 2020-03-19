import cobrakbase
import subprocess
import os
import cobra

class transyt_wrapper:

    def __init__(self, token=None, params=None, config=None, deploy_database=True):

        self.params = params
        self.config = config
        self.inputs_path = '/Users/davidelagoa/Desktop/test/'
        #self.inputs_path = '/workdir/processingDir/'
        self.results_path = '/workdir/results/'
        self.java = '/opt/jdk/jdk-11.0.1/bin/java'
        self.transyt_jar = '/opt/transyt/transyt.jar'
        self.ref_database = 'ModelSEED'     #check if it only supports modelseed

        self.kbase = cobrakbase.KBaseAPI(token, config=self.config)

        if deploy_database:
            self.deploy_neo4j_database()


    def run_transyt(self, model_obj_name = None, genome_obj_name = None, narrative_id = None):

        genome = None
        compounds = None

        if narrative_id is None:
            genome, compounds = self.retrieve_params_data()
        else:
            genome, compounds = self.retrieve_test_data(model_obj_name, genome_obj_name, narrative_id)

        self.inputs_preprocessing(genome, compounds)

        transyt_subprocess = subprocess.Popen([self.java, "-jar", "--add-exports",
                                               "java.base/jdk.internal.misc=ALL-UNNAMED",
                                               "-Dio.netty.tryReflectionSetAccessible=true", "-Dworkdir=/workdir",
                                               "-Xmx4096m", self.transyt_jar, "3", "/kb/module/data/testData/",
                                               self.results_path])

        working_dir = "/opt/transyt/jar"

        subprocess.check_call(transyt_subprocess, cwd=working_dir)

        if not os.path.exists(self.results_path):
            os.makedirs(self.results_path)


    def retrieve_test_data(self, model_obj_name, genome_obj_name, narrative_id):

        genome = self.kbase.get_object(genome_obj_name, narrative_id)
        model_compounds = self.kbase.get_object(model_obj_name, narrative_id)['modelcompounds']

        return genome, model_compounds


    def retrieve_params_data(self):

        ws = self.params['workspace_name']

        genome = self.kbase.get_object(self.params['genome_id'], ws)

        if 'model_id' in self.params and len(self.params['model_id'].strip()) > 0:
            kbase_model = self.kbase.get_object(self.params['model_id'], ws)
            model_compounds = kbase_model['modelcompounds']

        return genome, model_compounds


    def inputs_preprocessing(self, genome, model_compounds):

        # detect taxa
        ref_data = self.kbase.get_object_info_from_ref(genome['taxon_ref'])
        ktaxon = self.kbase.get_object(ref_data.id, ref_data.workspace_id)
        scientific_lineage = ktaxon['scientific_lineage']
        taxonomy_id = ktaxon['taxonomy_id']

        print(taxonomy_id)

        self.compounds_to_txt(model_compounds)
        self.genome_to_faa(genome)
        self.params_to_file(taxonomy_id, self.ref_database, False)


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


    def params_to_file(self, taxonomy_id, ref_database, override_common_ontology_filter):

        with open(self.inputs_path + 'params.txt', 'w') as f:
            f.write(str(taxonomy_id) + "\n" + ref_database + "\n" + str(override_common_ontology_filter))
            f.close()

    def deploy_neo4j_database(self):

        subprocess.Popen(["/opt/neo4j/neo4j-community-4.0.1/bin/neo4j", "start"])

wp = transyt_wrapper(token="NSRBLCNEOIC3RJZWFC66FGOLLWOQ24MI", deploy_database=False)
