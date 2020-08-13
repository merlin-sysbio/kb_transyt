import time
import json
import os
import uuid
import errno
import subprocess
import zipfile
import shutil
import csv
import numpy
import fileinput
import re
import itertools

from installed_clients.WorkspaceClient import Workspace as Workspace
from installed_clients.KBaseReportClient import KBaseReport

def _generate_html_report(result_directory, diff_expression_obj_ref,
                          params):
    """
    _generate_html_report: generate html summary report
    """

    html_report = list()

    #output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
    #self._mkdir_p(output_directory)
    result_file_path = os.path.join(result_directory, 'report.html')

    result_dirs = os.listdir(result_directory)
    visualization_content = ''
    for result_dir in result_dirs:
        dispersion_plots_name = result_dir + '_dispersion_plots.png'
        dispersion_plots_display_name = '{} {} dispersion plot'.format(result_dir.split('_')[0],
                                                                       result_dir.split('_')[1])

        #shutil.copy2(os.path.join(result_directory, result_dir, 'deseq2_MAplot.png'),
        #             os.path.join(result_directory, dispersion_plots_name))
        visualization_content += '<div class="gallery">'
        visualization_content += '<a target="_blank" href="{}">'.format(dispersion_plots_name)
        visualization_content += '<img src="{}" '.format(dispersion_plots_name)
        visualization_content += 'alt="{}" width="600" height="400">'.format(dispersion_plots_display_name)
        visualization_content += '</a><div class="desc">{}</div></div>'.format(dispersion_plots_display_name)


    #diff_expr_set_data = self.ws.get_objects2({'objects':
     #                                              [{'ref':
     #                                                    diff_expression_obj_ref}]})['data'][0]['data']
    #diff_expr_set_data = None

    #items = diff_expr_set_data['items']

    # expression_ref = self.expression_set_data['items'][0]['ref']
    # expression_object = self.ws.get_objects2({'objects':
    #                                          [{'ref': expression_ref}]})['data'][0]
    # expression_data = expression_object['data']
    # genome_ref = expression_data['genome_id']
    # genome_name = self.ws.get_object_info([{"ref": genome_ref}], includeMetadata=None)[0][1]

    # feature_num = self.gsu.search({'ref': genome_ref})['num_found']
    # genome_features = self.gsu.search({'ref': genome_ref,
    #                                    'limit': feature_num,
    #                                    'sort_by': [['feature_id', True]]})['features']
    # feature_ids = []
    # for genome_feature in genome_features:
    #     if not re.match('.*\.\d*', genome_feature.get('feature_id')):
    #         feature_ids.append(genome_feature.get('feature_id'))
    # total_feature_num = len(feature_ids)
    '''
    overview_content = ''
    overview_content += '<br/><table><tr><th>Generated DifferentialExpressionMatrixSet'
    overview_content += ' Object</th></tr>'
    overview_content += '<tr><td>{} ({})'.format(params.get('diff_expression_obj_name'),
                                                 diff_expression_obj_ref)
    overview_content += '</td></tr></table>'

    overview_content += '<p><br/></p>'

    overview_content += '<br/><table><tr><th>Generated DifferentialExpressionMatrix'
    overview_content += ' Object</th><th></th><th></th><th></th></tr>'
    overview_content += '<tr><th>Differential Expression Matrix Name</th>'
    # overview_content += '<th>Reference Genome</th>'
    # overview_content += '<th>Reference Genome Feature Count</th>'
    overview_content += '<th>Feature Count</th>'
    overview_content += '</tr>'
    
    for item in items:
        diff_expr_ref = item['ref']
        #diff_expr_object = self.ws.get_objects2({'objects':
        #                                             [{'ref': diff_expr_ref}]})['data'][0]
        diff_expr_object = None

        diff_expr_data = diff_expr_object['data']
        diff_expr_info = diff_expr_object['info']
        diff_expr_name = diff_expr_info[1]
        number_features = len(diff_expr_data['data']['row_ids'])

        overview_content += '<tr><td>{} ({})</td>'.format(diff_expr_name, diff_expr_ref)
        # overview_content += '<td>{} ({})</td>'.format(genome_name, genome_ref)
        # overview_content += '<td>{}</td>'.format(total_feature_num)
        overview_content += '<td>{}</td></tr>'.format(number_features)
    overview_content += '</table>'
    '''
    overview_content = '<table class="tg">\
    <thead>\
      <tr>\
        <th class="tg-i1re">TranSyT ID</th>\
        <th class="tg-i1re">ModelSEED ID</th>\
        <th class="tg-i1re">previous GPR</th>\
        <th class="tg-i1re">current GPR</th>\
      </tr>\
    </thead>\
    <tbody>\
      <tr>\
        <td class="tg-baqh">TR0000032</td>\
        <td class="tg-baqh">rnx00002</td>\
        <td class="tg-0lax">b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001<br> b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001 b0001</td>\
        <td class="tg-0lax">b0002</td>\
      </tr>\
      <tr>\
        <td class="tg-baqh">TI0000064</td>\
        <td class="tg-baqh">rxn00001</td>\
        <td class="tg-0lax"></td>\
        <td class="tg-0lax">b0003</td>\
      </tr>\
    </tbody>\
    </table>'

    with open(result_file_path, 'w') as result_file:
        with open(os.path.join(os.path.dirname(__file__), 'report_template.html'),
                  'r') as report_template_file:
            report_template = report_template_file.read()
            report_template = report_template.replace('<p>Overview_Content</p>',
                                                      overview_content)
            report_template = report_template.replace('<p>Visualization_Content</p>',
                                                      visualization_content)
            result_file.write(report_template)

    #report_shock_id = dfu.file_to_shock({'file_path': result_directory,
    #                                          'pack': 'zip'})['shock_id']
    report_shock_id = None

    html_report.append({'shock_id': report_shock_id,
                        'name': os.path.basename(result_file_path),
                        'label': os.path.basename(result_file_path),
                        'description': 'TranSyT HTML report'})
    return html_report

def _generate_output_file_list(self, result_directory):
    """
    _generate_output_file_list: zip result files and generate file_links for report
    """

    output_files = list()

    output_directory = os.path.join(self.scratch, str(uuid.uuid4()))
    self._mkdir_p(output_directory)
    result_file = os.path.join(output_directory, 'DESeq2_result.zip')
    plot_file = os.path.join(output_directory, 'DESeq2_plot.zip')

    with zipfile.ZipFile(result_file, 'w',
                         zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zip_file:
        for root, dirs, files in os.walk(result_directory):
            for file in files:
                if not (file.endswith('.zip') or
                        file.endswith('.png') or
                        file.endswith('.DS_Store')):
                    zip_file.write(os.path.join(root, file),
                                   os.path.join(os.path.basename(root), file))

    output_files.append({'path': result_file,
                         'name': os.path.basename(result_file),
                         'label': os.path.basename(result_file),
                         'description': 'File(s) generated by DESeq2 App'})

    with zipfile.ZipFile(plot_file, 'w',
                         zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zip_file:
        for root, dirs, files in os.walk(result_directory):
            for file in files:
                if file.endswith('.png'):
                    zip_file.write(os.path.join(root, file),
                                   os.path.join(os.path.basename(root), file))

    output_files.append({'path': plot_file,
                         'name': os.path.basename(plot_file),
                         'label': os.path.basename(plot_file),
                         'description': 'Visualization plots by DESeq2 App'})

    return output_files

def _generate_report(self, model_object, params, result_directory):
    """
    _generate_report: generate summary report
    """

    #output_files = self._generate_output_file_list(result_directory)

    #dfu = DataFileUtil(self.callback_url)

    output_html_files = _generate_html_report(result_directory,
                                                   model_object,
                                                   params)

    #diff_expr_set_data = self.ws.get_objects2({'objects':
    #                                               [{'ref':
    #                                                     diff_expression_obj_ref}]})['data'][0]['data']

    #items = diff_expr_set_data['items']

    description_set = 'DifferentialExpressionMatrixSet generated by DESeq2'
    description_object = 'DifferentialExpressionMatrix generated by DESeq2'
    objects_created = []
    #objects_created.append({'ref': diff_expression_obj_ref,
    #                        'description': description_set})

    #for item in items:
    #    diff_expr_ref = item['ref']
    #    objects_created.append({'ref': diff_expr_ref,
    #                            'description': description_object})

    report_params = {'message': '',
                     'workspace_name': params.get('workspace_name'),
                     #'file_links': output_files,
                     'html_links': output_html_files,
                     'direct_html_link_index': 0,
                     'html_window_height': 333,
                     'report_object_name': 'kb_transyt_report_' + str(uuid.uuid4())}

    kbase_report_client = KBaseReport(self.callback_url)
    output = kbase_report_client.create_extended_report(report_params)

    report_output = {'report_name': output['name'], 'report_ref': output['ref']}

    return report_output

