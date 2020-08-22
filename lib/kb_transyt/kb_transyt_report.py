from installed_clients.KBaseReportClient import KBaseReport
import uuid

tr_url = "https://transyt.bio.di.uminho.pt/reactions/"
search_bar_placeholder = "__SEARCHER__"

def generate_report(report_path, report_elements, references, objects_created, callback_url, ws_name, model_id,
                    sbml_path, transyt_zip, new_compartments, html_template_path, compounds_names):

    generate_html_file(report_path, report_elements, references, html_template_path, compounds_names)

    report = KBaseReport(callback_url)

    report_params = {
        'direct_html_link_index': 0,
        'workspace_name': ws_name,
        'report_object_name': 'run_transyt_' + uuid.uuid4().hex,
        'objects_created': objects_created,
        'html_links': [
            {'name': 'report', 'description': 'Report HTML', 'path': report_path}
        ],
        'file_links': [
            {'name': model_id + ".xml", 'description': 'desc', 'path': sbml_path},
            {'name': "transyt_output.zip", 'description': 'desc', 'path': transyt_zip}
        ]
    }

    if len(new_compartments) > 0:
        report_params['warnings'] = []
        for compartment in new_compartments:
            report_params['warnings'].append("New compartment \"" + compartment + "\" added to the model!")

    report_info = report.create_extended_report(report_params)

    return report_info


def generate_html_file(report_path, report_elements, references, html_template_path, compounds_names):

    onclick_bar = "<p></p><div class='tab'>\n"
    html = ""
    object_id = 1

    for title in report_elements.keys():

        if report_elements[title]:  #Empty entries are ignored from HTML file

            onclick_bar = onclick_bar + "<button class=\"tablinks\" onclick=\"openTab(event, '" + title + "')\"\
            id='defaultOpen'>" + title + "</button>\n"
            html = html + "<div id=\"" + title + "\" class=\"tabcontent\">"

            if title == "New reactions":
                html = html + "<table id='myTable" + str(object_id) + "' class='tg'><thead><tr><h3>List of new " \
                                                                      "reactions inserted in the model.</h3></tr>\n"
                html = html + search_bar_placeholder + "<tr><th class='tg-i1re'>TranSyT ID</th>\
                <th class='tg-i1re'>ModelSEED ID</th><th class='tg-i1re'>Equation</th>\
                <th class='tg-i1re'>GPR</th></tr></thead><tbody>"
                html = html + new_reactions_html(report_elements[title], references)

            elif title == "Reactions removed":
                html = html + "<table id='myTable" + str(object_id) + "' class='tg'><thead><tr><h3>Because option" \
                                                                      " \"Replace all transport reactions in " \
                              "the model\" was selected, the reactions below were removed from the model.</h3></tr>\n"
                html = html + search_bar_placeholder + "<tr><th class='tg-i1re'>ModelSEED ID</th>\
                              <th class='tg-i1re'>Equation</th><th class='tg-i1re'>GPR</th></tr></thead><tbody>\n"
                html = html + reactions_removed_html(report_elements[title], False)

            elif title == "Reactions not saved (ModelSEED ID not found)":
                html = html + "<table id='myTable" + str(object_id) + "' class='tg'><thead><tr><h3>Reactions in the" \
                                                                      " table below were rejected due to the" \
                              " absence of a cross-reference to ModelSEED identifiers. In order to integrate these" \
                              " reactions in the model, the advanced parameter \"Accept TranSyT identifiers if" \
                              " ModelSEED reference not found\" must be selected.</h3></tr>\n"
                html = html + search_bar_placeholder + "<tr><th class='tg-i1re'>TranSyT ID</th>\
                              <th class='tg-i1re'>Equation</th><th class='tg-i1re'>GPR</th></tr></thead><tbody>\n"
                html = html + reactions_removed_html(report_elements[title], True)

            elif title == "Reactions GPR modified":
                html = html + "<table id='myTable" + str(object_id) + "' class='tg'><thead><tr><h3>Reactions in this " \
                                                                      "table were already" \
                              "present in the model but had their GPR modified according to the option " \
                              "selected in the parameter \"Model result rules\".</h3></tr>\n"
                html = html + search_bar_placeholder + "<tr><th class='tg-i1re'>TranSyT ID</th><th class='tg-i1re'>ModelSEED ID</th>\
                              <th class='tg-i1re'>Original GPR</th><th class='tg-i1re'>New GPR</th></tr></thead><tbody>\n"
                html = html + reactions_gpr_modified_html(report_elements[title], references)

            search_bar = "<input type='text' id='myInput" + str(object_id) + "' onkeyup='myFunction" + str(object_id)\
                         + "()' placeholder='Type a query to search in all columns' title='Type in a name'>\n"
            html = html.replace(search_bar_placeholder, search_bar)
            html = html + "</tbody></table></div>\n\n"

            object_id += 1

    search_style = get_search_bar_style(object_id)
    search_script = get_search_bar_script(object_id)

    onclick_bar = onclick_bar + "</div>"
    html = onclick_bar + html

    for cpd_id in compounds_names.keys():
        html = html.replace(cpd_id, compounds_names[cpd_id])

    with open(report_path, 'w') as result_file:
        with open(html_template_path, 'r') as report_template_file:
            report_template = report_template_file.read()
            report_template = report_template.replace('#MY_INPUT', search_style)
            report_template = report_template.replace('#MY_SCRIPT', search_script)
            report_template = report_template.replace('<p>BODY_CONTENT</p>', html)
            result_file.write(report_template)


def new_reactions_html(new_reactions, references):
    html = ""

    for identifier in new_reactions:

        reaction = new_reactions[identifier]
        identifier = identifier.replace("_c0", "")

        model_seed_id = "-"
        if identifier in references:
            model_seed_id = references[identifier]

        html = html + "<tr>"
        html = html + "<td class='tg-baqh'><a href='" + tr_url + identifier + "'>" + identifier + "</a></td>"
        html = html + "<td class='tg-baqh'>" + model_seed_id + "</td>"
        html = html + "<td class='tg-0lax'>" + reaction.reaction + "</td>"
        html = html + "<td class='tg-0lax'>>" + reaction.gene_reaction_rule.replace(")", "").replace("(", "") \
            .replace(" or ", "<br>>").strip() + "</td>"
        html = html + "</tr>\n"

    return html


def reactions_removed_html(reactions_removed, assign_transyt_ref):
    html = ""

    for identifier in reactions_removed:

        html = html + "<tr>"
        reaction = reactions_removed[identifier]
        identifier = identifier.replace("_c0", "")

        if assign_transyt_ref:
            url_ref = "<a href='" + tr_url + identifier + "'>" + identifier + "</a>"
        else:
            url_ref = identifier

        html = html + "<td class='tg-baqh'>" + url_ref + "</td>"
        html = html + "<td class='tg-0lax'>" + reaction.reaction + "</td>"

        gpr_rule = reaction.gene_reaction_rule.strip()

        if gpr_rule:
            gpr_rule = ">" + reaction.gene_reaction_rule.replace(")", "")\
                .replace("(", "").replace(" or ", "<br>>").strip()

        html = html + "<td class='tg-0lax'>" + gpr_rule.replace("> ", ">") + "</td>"
        html = html + "</tr>\n"

    return html

def reactions_gpr_modified_html(reactions_modified, references):
    html = ""

    for identifier in reactions_modified:

        original_gpr = reactions_modified[identifier][0].strip()
        new_gpr = reactions_modified[identifier][1].strip()

        identifier = identifier.replace("_c0", "")

        model_seed_id = "-"
        if identifier in references:
            model_seed_id = references[identifier]

        if original_gpr:
            original_gpr = ">" + original_gpr.replace(")", "")\
                .replace("(", "").replace(" or ", "<br>>").strip()

        html = html + "<tr>"
        html = html + "<td class='tg-baqh'><a href='" + tr_url + identifier + "'>" + identifier + "</a></td>"
        html = html + "<td class='tg-baqh'>" + model_seed_id + "</td>"
        html = html + "<td class='tg-0lax'>" + original_gpr + "</td>"
        html = html + "<td class='tg-0lax'>>" + new_gpr.replace(")", "").replace("(", "") \
            .replace(" or ", "<br>>").strip() + "</td>"
        html = html + "</tr>\n"

    return html


def get_search_bar_style(object_id):

    html = ""

    for i in range(1, object_id):
        if html:
            html = html + ", "
        html = html + "#myInput" + str(i)

    return html


def get_search_bar_script(object_id):

    html = "<script>"

    for i in range(1, object_id):
        html = html + "function myFunction" + str(i) + "() {\n var input, filter, table, tr, td, i, txtValue; " \
                                                       "input = document.getElementById(\"myInput" + str(i) + "\"); " \
                                                        "filter = input.value.toUpperCase(); " \
                                                        "table = document.getElementById(\"myTable" + str(i) + "\"); " \
                                                        "tr = table.getElementsByTagName(\"tr\"); " \
                                                        "th = table.getElementsByTagName(\"th\"); " \
                                                        "for (i = 0; i < tr.length; i++) " \
                                                        "for(j = 0; j < th.length; j++){ " \
                                                        "td = tr[i].getElementsByTagName(\"td\")[j]; " \
                                                        "if (td) { txtValue = td.textContent || td.innerText; " \
                                                        "if (txtValue.toUpperCase().indexOf(filter) > -1) {" \
                                                        "tr[i].style.display = \"\";break;}" \
                                                        "else {tr[i].style.display = \"none\";}}}}\n\n"

    return html + "</script>"
