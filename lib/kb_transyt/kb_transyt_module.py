import os
import cobra
import subprocess

def copy_sbml():
    1

def make_report():
    1

class Transyt:

    def __init__(self):
        self.java_home = ""
        self.working_dir = "/kb/module/data/transyt/jar"

    def run(self, genome_path, model_path, taxa_id, output_model_path):
        java = "/opt/jdk/jdk-11.0.1/bin/java"
        transyt_jar = "newTransytTest.jar"
        
        #genome_path = "../genome/GCF_000005845.2_ASM584v2_protein.faa"
        
        transyt_subprocess = [java, "-jar", transyt_jar, str(taxa_id), genome_path, model_path]

        subprocess.check_call(transyt_subprocess, cwd=self.working_dir)

        out_sbml_path = '/kb/module/data/transyt/genome/sbmlResult_qCov_0.8_eValThresh_1.0E-50.xml'

        if os.path.exists(out_sbml_path):
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
                with open(output_model_path, 'w') as f:
                    f.writelines(xml_fix)

        tmodel = cobra.io.read_sbml_model(output_model_path)
        return tmodel
        

