<%inherit file="${context['main_template'].uri}" />
<%namespace file="/base/utils.mako" import="company_list_badges"/>
<%namespace file="/base/searchformlayout.mako" import="searchform"/>

<%block name='actionmenucontent'>
<div class='main_toolbar action_tools'>
    <div class='layout flex main_actions'>
        <div role='group'></div>
        <div role='group'>
            <a class='btn' href='${export_xls_url}' title="Export au format Excel (xlsx)" aria-label="Export au format Excel (xlsx)">
                ${api.icon('file-excel')} Excel
            </a>
            <a class='btn' href='${export_ods_url}' title="Export au format Open Document (ods)" aria-label="Export au format Open Document (ods)">
                ${api.icon('file-spreadsheet')} ODS
            </a>
        </div>
    </div>
</div>
</%block>

<%block name='content'>

<div class='search_filters'>
    ${form|n}
</div>

<div>
    <div class="table_container scroll_hor">
        <button class="fullscreen_toggle small" title="Afficher le tableau en plein écran" aria-label="Afficher le tableau en plein écran" onclick="toggleTableFullscreen(this);return false;">
            ${api.icon('expand')}
            ${api.icon('compress')}
            <span>Plein écran</span>
        </button>
        <table class="hover_table">
            <thead>
                <tr>
                    <th scope="col" class="col_date">Date</th>
                    <th scope="col" class="col_text">Validateur</th>
                    <th scope="col" class="col_text">Enseigne</th>
                    <th scope="col" class="col_text">Type</th>
                    <th scope="col" class="col_text">Nom</th>
                    <th scope="col" class="col_text">Résultat</th>
                </tr>
                <tr class="row_recap">
                    <th class="col_text min10" colspan=6>${records.count()} validations</th>
                </tr>
            </thead>
            <tbody>
                % for data in records:
                    <tr>
                        <td class="col_date">${api.format_date(data.datetime)}</td>
                        <td class="col_text">${data.user.lastname} ${data.user.firstname}</td>
                        <td class="col_text">${data.node.company.name}</td>
                        <td class="col_text">${data.node.type_label}</td>
                        <td class="col_text">
                            <a href="${api.node_url(data.node)}">
                                ${api.node_label(data.node, with_details=True)|n}
                            </a>
                        <td class="col_text">
                            % if data.status == "valid":
                                <span class="icon status valid">${api.icon("check-circle")}</span> Validé
                            % else:
                                <span class="icon status invalid">${api.icon("times-circle")}</span> Invalidé
                            % endif
                        </td>
                    </tr>
                % endfor
            </tbody>
        </table>
    </div>
</div>

</%block>
