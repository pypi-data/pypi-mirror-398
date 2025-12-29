<%inherit file="${context['main_template'].uri}" />
<%namespace file="/base/utils.mako" import="dropdown_item"/>
<%namespace file="/base/pager.mako" import="pager"/>
<%namespace file="/base/pager.mako" import="sortable"/>
<%namespace file="/base/searchformlayout.mako" import="searchform"/>

<%block name='actionmenucontent'>
<div class='main_toolbar action_tools'>
	<div class='layout flex main_actions'>
    	${request.layout_manager.render_panel('action_buttons', links=stream_main_actions())}
    	${request.layout_manager.render_panel('action_buttons', links=stream_more_actions())}
    </div>
</div>
</%block>

<%block name='content'>

${searchform()}

<div>
    <div>
        ${records.item_count} Résultat(s)
    </div>
    <div class='table_container'>
        % if records:
        <table class="hover_table">
            <thead>
                <tr>
                    <th scope="col" class="col_date">${sortable("Créé le", "created_at")}</th>
                    % if is_global:
                        <th scope="col" class="col_text">Enseigne</th>
                    % endif
                    <th scope="col" class="col_text">${sortable("Nom du fournisseur", "label")}</th>
                    <th scope="col" class="col_text">N<span class='screen-reader-text'>umér</span><sup>o</sup> d'identification</th>
                    <th scope="col" class="col_text">Nom du contact principal</th>
                    <th scope="col" class="col_actions" title="Actions"><span class="screen-reader-text">Actions</span></th>
                </tr>
            </thead>
            <tbody>
        % else:
        <table>
            <tbody>
				<tr>
					<td class="col_text">
						<em>Aucun fournisseur n’a été référencé</em>
					</td>
				</tr>
       % endif
            % for supplier in records:
                <tr class='tableelement' id="${supplier.id}">
					<% url = request.route_path("/suppliers/{id}", id=supplier.id) %>
                    <% onclick = "document.location='{url}'".format(url=url) %>
                    <% tooltip_title = "Cliquer pour voir ou modifier le fournisseur « " + supplier.label + " »" %>
                    <td class="col_date" onclick="${onclick}" title="${tooltip_title}">${api.format_date(supplier.created_at)}</td>
                    % if is_global:
                        <td class="col_text" onclick="${onclick}">
                            ${supplier.company.name}
                        </td>
                    % endif
                    <td class="col_text">
						<a href="${url}" title="${tooltip_title}" aria-label="${tooltip_title}">${supplier.label}</a>
                        % if supplier.archived:
                            <span class="icon tag neutral">${api.icon('archive')} Archivé</span>
                        % endif
						% if supplier.is_internal():
                            <span class="icon tag neutral">${api.icon('house')} Interne à la CAE</span>
						% endif
                    </td>
                    <td class="col_text" onclick="${onclick}" title="${tooltip_title}">
                        ${supplier.get_company_identification_number()}
                    </td>
                    <td class="col_text" onclick="${onclick}" title="${tooltip_title}">
                        ${supplier.get_contact_label()}
                    </td>
                    ${request.layout_manager.render_panel('action_buttons_td', links=stream_actions(supplier))}
                </tr>
            % endfor
            </tbody>
        </table>
	</div>
	${pager(records)}
</div>

</%block>

<%block name='footerjs'>
$(function(){
    $('input[name=search]').focus();
});
</%block>
