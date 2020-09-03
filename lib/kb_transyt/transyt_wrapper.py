import cobrakbase
import subprocess
import os
import cobra
from cobra_to_kbase_patched import convert_to_kbase_reaction, get_compounds_references, \
    get_compartmets_references, build_model_compound, build_model_compartment
import kb_transyt_report
import shutil
import re

class transyt_wrapper:

    def __init__(self, token=None, params=None, config=None, deploy_database=True, callbackURL=None, dev=False,
                 shared_folder=None):

        self.params = params
        self.config = config
        self.callback_url = callbackURL
        #self.inputs_path = '/Users/davidelagoa/Desktop/test/processingDir/'
        self.inputs_path = '/workdir/processingDir/'
        self.results_path = ''
        #self.results_path = '/Users/davidelagoa/Desktop/test/resultsDir/'
        self.java = '/opt/jdk/jdk-11.0.1/bin/java'
        self.transyt_jar = '/opt/transyt/transyt.jar'
        self.ref_database = 'ModelSEED'     #check if it only supports modelseed
        self.kbase_model = None
        self.shared_folder = shared_folder
        self.report_template_html = "/kb/module/conf/report_template.html"

        self.ws = None
        self.taxonomy_id = None
        self.genome_id = None
        self.scientific_lineage = None
        self.kbase = None

        if dev:
            self.kbase = cobrakbase.KBaseAPI(token=token, dev=True)
        else:
            self.kbase = cobrakbase.KBaseAPI(token, config=self.config)

        if deploy_database:
            transyt_wrapper.deploy_neo4j_database()

    def get_workspace_name(self):
        return self.ws

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

        if self.taxonomy_id is None:
            return -3

        #if not os.path.exists(self.results_path):
        #    os.makedirs(self.results_path)

        transyt_subprocess = subprocess.Popen([self.java, "-jar", "--add-exports",
                                               "java.base/jdk.internal.misc=ALL-UNNAMED",
                                               "-Dio.netty.tryReflectionSetAccessible=true", "-Dworkdir=/workdir",
                                               "-Dlogback.configurationFile=/kb/module/conf/logback.xml",
                                               "-Xmx4096m", self.transyt_jar, "3", self.inputs_path])

        exit_code = transyt_subprocess.wait()

        self.results_path = self.inputs_path + "results"

        print(os.system("ls " + self.inputs_path))
        print(os.system("ls " + self.results_path))

        print("jar process finished! exit code: " + str(exit_code))

        return exit_code

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
        model_compounds = None

        if self.params['cpmds_filter'] == 1 and 'model_id' in self.params and self.params['model_id'] is not None:
            self.kbase_model = self.kbase.get_object(self.params['model_id'], self.ws)
            model_compounds = self.kbase_model['modelcompounds']

        return genome, model_compounds

    def inputs_preprocessing(self, genome, model_compounds):

        # detect taxa
        if 'taxon_ref' in genome:
            ref_data = self.kbase.get_object_info_from_ref(genome['taxon_ref'])
            ktaxon = self.kbase.get_object(ref_data.id, ref_data.workspace_id)
            self.scientific_lineage = ktaxon['scientific_lineage']
            self.taxonomy_id = ktaxon['taxonomy_id']
        elif self.params["tax_id"] != "":
            self.taxonomy_id = self.params["tax_id"]

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

        with open(self.inputs_path + 'protein.faa', 'w') as f:
            f.write('\n'.join(faa_features))
            f.close()

    def params_to_file(self):

        with open(self.inputs_path + 'params.txt', 'w') as f:

            for key in self.params:
                value = self.params[key]

                if key == "score_threshold" and self.params['ignore_m2'] == 1:
                    value = 1

                f.write(key + "\t" + str(value) + "\n")

            f.write('taxID' + "\t" + str(self.taxonomy_id) + "\n")
            f.write('reference_database' + "\t" + self.ref_database)
            f.close()

        print('taxID' + "\t" + str(self.taxonomy_id))

    def process_output(self):

        # only used for tests
        if self.shared_folder is None:
            self.shared_folder = ""

        out_sbml_path = self.results_path + "/transyt.xml"
        model_fix_path = self.shared_folder + '/transporters_sbml.xml'


        if self.ws is None:  # delete when tests are complete
            self.ws = "davide:narrative_1585772431721"
            #self.params["genome_id"] = "Escherichia_coli_K-12_MG1655"
            self.kbase_model = self.kbase.get_object(self.params['model_id'], self.ws)
            self.results_path = "/Users/davidelagoa/Downloads/results"
            self.shared_folder = "/Users/davidelagoa/Downloads/results"
            out_sbml_path = self.results_path + "/transyt.xml"
            model_fix_path = self.results_path + "/transporters_sbml.xml"
            self.report_template_html = "/Users/davidelagoa/PycharmProjects/kb_transyt/conf/report_template.html"


        if os.path.exists(out_sbml_path):

            # fix this in TranSyT, then delete this step
            self.fix_transyt_model(out_sbml_path, model_fix_path)

            return self.merge_or_replace_model_reactions(model_fix_path)
        return None

    def merge_or_replace_model_reactions(self, transyt_model_fix_path):

        cobra_model = cobra.io.read_sbml_model(transyt_model_fix_path)

        report_new_compartments = {}
        report_new_reactions_added = {}
        report_reactions_gpr_modified = {}
        report_reactions_removed = {}
        report_reactions_not_saved_not_accept_transyt_id = {}

        option = self.params["rule"]
        references = self.read_references_file()

        transporters_in_model = {}
        compounds_in_model = []
        compartments_in_model = []

        kbase_cobra_model = cobrakbase.convert_kmodel(self.kbase_model) #facilitates building the report

        for reaction in self.kbase_model["modelreactions"]:
            compartments = []

            for compound in reaction["modelReactionReagents"]:
                compartment = compound["modelcompound_ref"].split("_")[1]
                compound_ref = compound["modelcompound_ref"].split("/")[-1]

                if compound_ref not in compounds_in_model:
                    compounds_in_model.append(compound_ref)
                if compartment not in compartments_in_model:
                    compartments_in_model.append(compartment)

                if compartment not in compartments:
                    compartments.append(compartment)

            if len(compartments) > 1 and option == "replace_all":
                self.kbase_model["modelreactions"].remove(reaction)
                report_reactions_removed[reaction["id"]] = kbase_cobra_model.reactions.get_by_id(reaction["id"])
            elif len(compartments) > 1 and "merge_" in option:
                transporters_in_model[reaction["id"].split("_")[0]] = reaction

        compartments_to_refs = get_compartmets_references(cobra_model)
        compounds_to_refs = get_compounds_references(cobra_model)
        compounds_names = transyt_wrapper.get_compounds_names(self.kbase_model)

        for reaction in cobra_model.reactions:

            original_id = reaction.id
            reaction_id = reaction.id

            if reaction_id in references:
                reaction_id = references[reaction_id]
                reaction.id = reaction_id

            save = False
            model_reaction = convert_to_kbase_reaction(reaction, compounds_to_refs)

            if option == "replace_all":
                save = True
            elif reaction_id in transporters_in_model:
                if option == "merge_reactions_only":
                    continue

                elif option == "merge_reactions_and_gpr":
                    original_gpr = self.build_str_gpr(transporters_in_model[reaction_id]["modelReactionProteins"])

                    transporters_in_model[reaction_id]["modelReactionProteins"] = self.merge_gpr(
                        transporters_in_model[reaction_id]["modelReactionProteins"],
                        model_reaction["modelReactionProteins"])

                    new_gpr = self.build_str_gpr(transporters_in_model[reaction_id]["modelReactionProteins"])
                    report_reactions_gpr_modified[original_id] = (original_gpr, new_gpr)

                elif option == "merge_reactions_replace_gpr":
                    original_gpr = self.build_str_gpr(transporters_in_model[reaction_id]["modelReactionProteins"])
                    new_gpr = self.build_str_gpr(model_reaction["modelReactionProteins"])
                    transporters_in_model[reaction_id]["modelReactionProteins"] = model_reaction["modelReactionProteins"]
                    report_reactions_gpr_modified[original_id] = (original_gpr, new_gpr)

            else:   #for reaction that is not already in model
                save = True

            if save and self.params["accept_transyt_ids"] == 1:

                for metabolite in reaction.metabolites:
                    comp_id = metabolite.compartment + "0"
                    if comp_id not in compartments_in_model:
                        model_compartment = build_model_compartment(comp_id,
                                                                    compartments_to_refs[metabolite.compartment],
                                                                    cobra_model.compartments[metabolite.compartment] + "_0")
                        self.kbase_model["modelcompartments"].append(model_compartment)
                        compounds_in_model.append(comp_id)
                        report_new_compartments[comp_id] = cobra_model.compartments[metabolite.compartment]

                    if metabolite.id not in compounds_in_model:
                        model_compound = build_model_compound(metabolite, compartments_to_refs)
                        self.kbase_model["modelcompounds"].append(model_compound)
                        compounds_names = transyt_wrapper.save_compound_name(model_compound, compounds_names)

                self.kbase_model["modelreactions"].append(model_reaction)
                report_new_reactions_added[original_id] = reaction
            elif self.params["accept_transyt_ids"] == 0:
                report_reactions_not_saved_not_accept_transyt_id[original_id] = reaction

        object_id = self.params['model_id']
        description = "object new version created"

        if self.params["output_model"]:
            object_id = self.params["output_model"]
            description = "new object created"

        # this steps saves the object in the workspace
        self.kbase.save_object(object_id, self.ws, 'KBaseFBA.FBAModel', self.kbase_model)

        new_transyt_zip_path = self.shared_folder + "/results.zip"
        shutil.copyfile(self.inputs_path + "/results.zip", new_transyt_zip_path)
        shutil.copyfile("/kb/module/conf/search.png", self.shared_folder + "/search.png")
        report_path = self.shared_folder + "/report.html"

        report_elements = {
            "New reactions": report_new_reactions_added,
            "Reactions GPR modified": report_reactions_gpr_modified,
            "Reactions removed": report_reactions_removed,
            "Reactions not saved (ModelSEED ID not found)": report_reactions_not_saved_not_accept_transyt_id
        }

        objects_created = [{'ref': f"{self.ws}/{object_id}",
                            'description': description}]

        report_info = kb_transyt_report.generate_report(report_path, report_elements, references, objects_created,
                                                        self.callback_url, self.ws, self.params['model_id'],
                                                        transyt_model_fix_path, new_transyt_zip_path,
                                                        report_new_compartments, self.report_template_html, compounds_names)
        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref'],
        }

        return output

    def merge_gpr(self, kbase_model_gpr, transyt_model_gpr):

        kbase_gpr = self.build_str_subunits(kbase_model_gpr)

        for model_protein in transyt_model_gpr:

            protein = []
            for model_subunit in model_protein["modelReactionProteinSubunits"]:
                for gene_ref in model_subunit["feature_refs"]:
                    subunit = gene_ref.split("/")[-1].strip()
                    protein.append(subunit)
            protein.sort()

            if " and ".join(protein) not in kbase_gpr:
                kbase_model_gpr.append(model_protein)

        return kbase_model_gpr

    def build_str_gpr(self, kbase_gpr):

        return " or ".join(self.build_str_subunits(kbase_gpr))

    def build_str_subunits(self, kbase_gpr):

        gpr = []

        for model_protein in kbase_gpr:

            protein = []
            for model_subunit in model_protein["modelReactionProteinSubunits"]:
                for gene_ref in model_subunit["feature_refs"]:
                    subunit = gene_ref.split("/")[-1].strip()
                    if subunit: #some subunit are empty and passed here as a subunit with a blank ID
                        protein.append(subunit)

            if len(protein) > 0:
                protein.sort()
                gpr.append(" and ".join(protein))

        return gpr

    def read_references_file(self):

        dic = {}

        with open(self.results_path + '/reactions_references.txt', 'r') as f:
            for line in f:
                split_line = line.split("\t")
                dic[split_line[0].strip()] = split_line[1].strip().replace("[", "").replace("]", "").split("; ")[0] #not sure if more than 1 is possible

        return dic

    def fix_transyt_model(self, sbml_path, sbml_fix_path):

        sbml_tag = '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" fbc:required="false" groups:required="false" level="3" sboTerm="SBO:0000624" version="1" xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2" xmlns:groups="http://www.sbml.org/sbml/level3/version1/groups/version1">'
        model_tag = '<model extentUnits="substance" fbc:strict="true" id="transyt" metaid="transyt" name="transyt" substanceUnits="substance" timeUnits="time">'
        xml_data = None
        xml_fix = ""
        with open(sbml_path, 'r') as f:
            xml_data = f.readlines()
        for l in xml_data:
            if l.strip().startswith('<sbml'):
                xml_fix += sbml_tag
            elif l.strip().startswith('<model'):
                xml_fix += model_tag
            else:
                xml_fix += l

        if xml_data is not None:
            with open(sbml_fix_path, 'w') as f:
                f.writelines(xml_fix)

    @staticmethod
    def get_compounds_names(kbase_model):

        compounds = {}

        for model_compound in kbase_model["modelcompounds"]:
            compounds = transyt_wrapper.save_compound_name(model_compound, compounds)

        return compounds

    @staticmethod
    def save_compound_name(model_compound, compounds):
        m_seed_id = model_compound["id"]
        # replace compartment
        m_seed_name = re.sub("_(?:.(?!_))+$", "_", model_compound["name"])
        # guarantee always same in different compartments (might be different when source of compound is different)
        m_seed_id_aux = model_compound["id"].split("_")[0] + "_"

        if m_seed_id_aux in compounds:
            if m_seed_id == compounds[m_seed_id_aux]:
                compounds[m_seed_id_aux] = m_seed_name
        else:
            compounds[m_seed_id_aux] = m_seed_name

        return compounds

    @staticmethod
    def deploy_neo4j_database():

        subprocess.Popen(["/opt/neo4j/neo4j-community-4.0.2/bin/neo4j", "start"])
