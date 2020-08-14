import cobrakbase
import subprocess
import os
import cobra
from installed_clients.KBaseReportClient import KBaseReport
from cobra_to_kbase_patched import convert_to_kbase,convert_to_kbase_reaction, get_compounds_references, \
    get_compartmets_references, build_model_compound, build_model_compartment
import generate_report

class transyt_wrapper:

    def __init__(self, token=None, params=None, config=None, deploy_database=True, callbackURL=None, dev=False):

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
        self.kbase_model = None

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
        '''
        transyt_subprocess = subprocess.Popen([self.java, "-jar", "--add-exports",
                                               "java.base/jdk.internal.misc=ALL-UNNAMED",
                                               "-Dio.netty.tryReflectionSetAccessible=true", "-Dworkdir=/workdir",
                                               "-Dlogback.configurationFile=/kb/module/conf/logback.xml",
                                               "-Xmx4096m", self.transyt_jar, "3", self.inputs_path])

        exit_code = transyt_subprocess.wait()
        '''
        exit_code = 0

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
        model_compounds = None

        if self.params['cpmds_filter'] == 1 and 'model_id' in self.params and self.params['model_id'] is not None:
            self.kbase_model = self.kbase.get_object(self.params['model_id'], self.ws)
            model_compounds = self.kbase_model['modelcompounds']

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

        with open(self.inputs_path + 'protein.faa', 'w') as f:
            f.write('\n'.join(faa_features))
            f.close()


    def params_to_file(self):

        with open(self.inputs_path + 'params.txt', 'w') as f:

            for key in self.params:
                f.write(key + "\t" + str(self.params[key]) + "\n")

            f.write('taxID' + "\t" + str(self.taxonomy_id) + "\n")
            f.write('reference_database' + "\t" + self.ref_database)
            f.close()

        print('taxID' + "\t" + str(self.taxonomy_id))

    def process_output(self):

        out_sbml_path = self.results_path + "/results/transyt.xml"

        if self.ws is None:  # delete when tests are complete
            self.ws = "davide:narrative_1585772431721"
            #self.params["genome_id"] = "Escherichia_coli_K-12_MG1655"
            self.kbase_model = self.kbase.get_object(self.params['model_id'], self.ws)
            self.results_path = "/Users/davidelagoa/Desktop/ecoli/ecoli_iML1515_new/results/results"
            out_sbml_path = self.results_path + "/transyt.xml"

        model_fix_path = self.results_path + '/transporters_sbml.xml'
        if os.path.exists(out_sbml_path):

            self.fix_transyt_model(out_sbml_path, model_fix_path) #fix this in TranSyT, then delete this step
            self.merge_or_replace_model_reactions(model_fix_path)

            self.kbase.save_object(self.params['model_id'], self.ws, 'KBaseFBA.FBAModel', self.kbase_model)

    def merge_or_replace_model_reactions(self, transyt_model_fix_path):

        cobra_model = cobra.io.read_sbml_model(transyt_model_fix_path)

        option = self.params["rule"]
        references = self.read_references_file()

        transporters_in_model = {}
        compounds_in_model = []
        compartments_in_model = []

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
            elif len(compartments) > 1 and "merge_" in option:
                transporters_in_model[reaction["id"].split("_")[0]] = reaction

        compartments_to_refs = get_compartmets_references(cobra_model)
        compounds_to_refs = get_compounds_references(cobra_model)

        for reaction in cobra_model.reactions:

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
                    for gpr in model_reaction["modelReactionProteins"]:
                        transporters_in_model[reaction_id]["modelReactionProteins"].append(gpr)    #this only works because kbase object is ignoring complexes
                elif option == "merge_reactions_replace_gpr":
                    #print(reaction_id)
                    transporters_in_model[reaction_id]["modelReactionProteins"] = model_reaction["modelReactionProteins"]
            else:   #for merge and reaction is not already in model
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

                    if metabolite.id not in compounds_in_model:
                        model_compound = build_model_compound(metabolite, compartments_to_refs)
                        self.kbase_model["modelcompounds"].append(model_compound)

                self.kbase_model["modelreactions"].append(model_reaction)

        #generate_report._generate_report(self.kbase_model, self.params, self.results_path)

    def get_report(self):
        report_params = {
            # message is an optional field.
            # A string that appears in the summary section of the result page
            'message': "this is a transyt message",

            # A list of strings that can be used to alert the user
            'warnings': ["a warning should be here", "and another one here"],

            # The workspace name or ID is included in every report
            'workspace_name': self.ws,

            # HTML files that appear in “Links”
            #   section. A list of paths or shock node
            #   IDs pointing to a single flat html file
            #   or to the top-level directory of a
            #   website. The report widget can render
            #   one html view directly. Set one of the
            #   following fields to decide which view to
            #   render:
            #     direct_html - A string with simple
            #       html text that will be rendered
            #       within the report widget:
            #     direct_html_link_index - Integer to
            #       specify the index of the page in
            #       html_links to view directly in the
            #       report widget
            # See a working example here:
            # https://github.com/kbaseapps/kb_deseq/blob/586714d/lib/kb_deseq/Utils/DESeqUtil.py#L86-L194
            # 'html_links': html_files_in_app,
            # 'direct_html_link_index': 0,
            'direct_html': '<!DOCTYPE html><html><head><style>body {font-family: "Lato", sans-serif;}/* Style the tab */div.tab {    overflow: hidden;    border: 1px solid #ccc;    background-color: #f1f1f1;}/* Style the buttons inside the tab */div.tab button {    background-color: inherit;    float: left;    border: none;    outline: none;    cursor: pointer;    padding: 14px 16px;    transition: 0.3s;    font-size: 17px;}/* Change background color of buttons on hover */div.tab button:hover {    background-color: #ddd;}/* Create an active/current tablink class */div.tab button.active {    background-color: #ccc;}/* Style the tab content */.tabcontent {    display: none;    padding: 6px 12px;    border: 1px solid #ccc;    -webkit-animation: fadeEffect 1s;    animation: fadeEffect 1s;    border-top: none;}/* Fade in tabs */@-webkit-keyframes fadeEffect {    from {opacity: 0;}    to {opacity: 1;}}@keyframes fadeEffect {    from {opacity: 0;}    to {opacity: 1;}}table {    font-family: arial, sans-serif;    border-collapse: collapse;    width: 100%;}td, th {    border: 1px solid #dddddd;    text-align: left;    padding: 8px;}tr:nth-child(odd) {    background-color: #dddddd;}div.gallery {    margin: 5px;    border: 1px solid #ccc;    float: left;    width: 180px;}div.gallery:hover {    border: 1px solid #777;}div.gallery img {    width: 100%;    height: auto;}div.desc {    padding: 15px;    text-align: center;}.tg  {border-collapse:collapse;border-spacing:0;}.tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;  overflow:hidden;padding:10px 5px;word-break:normal;}.tg th{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;  font-weight:normal;overflow:hidden;padding:10px 5px;word-break:normal;}.tg .tg-baqh{text-align:center;vertical-align:top}.tg .tg-i1re{background-color:#9b9b9b;color:#ffffff;font-weight:bold;text-align:center;vertical-align:top}.tg .tg-0lax{text-align:left;vertical-align:top}</style></head><body><p></p><div class="tab">  <button class="tablinks" onclick="openTab(event, "Overview")" id="defaultOpen">Overview</button>  <button class="tablinks" onclick="openTab(event, "Visualization")">Visualization</button></div><div id="Overview" class="tabcontent">    <p>Overview_Content</p></div><div id="Visualization" class="tabcontent">  <p>Visualization_Content</p></div><script>function openTab(evt, tabName) {    var i, tabcontent, tablinks;    tabcontent = document.getElementsByClassName("tabcontent");    for (i = 0; i < tabcontent.length; i++) {        tabcontent[i].style.display = "none";    }    tablinks = document.getElementsByClassName("tablinks");    for (i = 0; i < tablinks.length; i++) {        tablinks[i].className = tablinks[i].className.replace(" active", "");    }    document.getElementById(tabName).style.display = "block";    evt.currentTarget.className += " active";}// Get the element with id="defaultOpen" and click on itdocument.getElementById("defaultOpen").click();</script></body></html>',

            # html_window_height : Window height - This sets the height
            # of the HTML window displayed under the “Reports” section.
            # The width is fixed.
            'html_window_height': 333,
        }  # end of report_params

        # Make the client, generate the report

        kbase_report_client = KBaseReport(self.callback_url)
        report_output = kbase_report_client.create_extended_report(report_params)

        # Return references which will allow inline display of
        # the report in the Narrative
        output = {'report_name': report_output['name'],
                         'report_ref': report_output['ref']}

        return output

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

    def get_workspace_name(self):
        return self.ws

    def deploy_neo4j_database(self):

        subprocess.Popen(["/opt/neo4j/neo4j-community-4.0.2/bin/neo4j", "start"])
