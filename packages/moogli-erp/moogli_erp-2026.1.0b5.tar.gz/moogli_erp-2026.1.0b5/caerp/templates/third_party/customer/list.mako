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
			<!-- CALCUL DES TOTAUX -->
			<% total_income = 0 %>
			<% total_topay = 0 %>
			% for customer in records:
				<% total_income += customer.get_total_income() %>
				<% total_topay += customer.get_topay() %>
			% endfor
			% if is_global:
				<% colspan=6 %>
			% else:
				<% colspan=5 %>
			% endif
			<table class="hover_table">
				<thead>
					<tr>
						<th scope="col" class="col_status" title="Type de client"><span class="screen-reader-text">Type de client</span></th>
						<th scope="col" class="col_date">${sortable("Utilisé en dernier le", "max_date")}</th>
						<th scope="col" class="col_date">${sortable("Créé le", "created_at")}</th>
						% if is_global:
							<th scope="col" class="col_text">Enseigne</th>
						% endif
						<th scope="col" class="col_text">${sortable("Nom du client", "label")}</th>
						<th scope="col" class="col_text">${sortable("Nom du contact principal", "lastname")}</th>
						<th scope="col" class="col_number">${sortable("CA HT", "turnover")}</th>
						<!--<th scope="col" class="col_number">${sortable("Restant dû", "topay")}</th>-->
						<th scope="col" class="col_number">Restant dû</th>
						<th scope="col" class="col_actions" title="Actions"><span class="screen-reader-text">Actions</span></th>
					</tr>
				</thead>
				<tbody>
        % else:
			<table>
				<tbody>
					<tr>
						<td colspan='7' class="col_text">
							<em>Aucun client n’a été référencé</em>
						</td>
					</tr>
		% endif
			<tr class='row_recap'>
				<td class="col_text" scope="row" colspan="${colspan}">Total</td>
				<td class='col_number'>${api.format_amount(total_income, precision=5)}&nbsp;€</td>
				<td class='col_number'>${api.format_amount(total_topay, precision=5)}&nbsp;€</td>
				<td>&nbsp;</td>
			</tr>
			% for customer in records:
				<tr class='tableelement' id="${customer.id}">
					<% url = request.route_path("/customers/{id}", id=customer.id) %>
					<% onclick = "document.location='{url}'".format(url=url) %>
					% if customer.is_company():
						<% user_icon = 'building' %>
						<% user_type = 'Personne morale' %>
					% elif customer.is_internal():
						<% user_icon = 'house' %>
						<% user_type = 'Enseigne interne à la CAE' %>
					% else:
						<% user_icon = 'user' %>
						<% user_type = 'Personne physique' %>
					% endif
					<% tooltip_title = "Cliquer pour voir ou modifier le client « " + customer.label + " » (" + user_type + ")" %>
					<td class="col_status" title="${tooltip_title}" aria-label="${tooltip_title}">
						<span class="icon status mode">${api.icon(user_icon)}</span>
					</td>
					<td class="col_date" onclick="${onclick}" title="${tooltip_title}">${api.format_date(stream_max_date(customer))}</td>
					<td class="col_date" onclick="${onclick}" title="${tooltip_title}">${api.format_date(customer.created_at)}</td>
                    % if is_global:
                        <td class="col_text" onclick="${onclick}">
                            ${customer.company.name}
                        </td>
                    % endif
					<td class="col_text">
						<a href="${url}" title="${tooltip_title}" aria-label="${tooltip_title}">${customer.label}</a>
						% if customer.archived:
                            <span class="icon tag neutral">${api.icon('archive')} Archivé</span>
						% endif
						% if customer.is_internal():
                            <span class="icon tag neutral">${api.icon('house')} Interne à la CAE</span>
						% endif
					</td>
					<td class="col_text" onclick="${onclick}" title="${tooltip_title}">
						% if customer.is_company():
							${customer.get_contact_label()}
						% else:
							&nbsp;
						% endif
					</td>
                    <td class='col_number'>${api.format_amount(customer.get_total_income(), precision=5)}&nbsp;€</td>
                    <td class='col_number'>${api.format_amount(customer.get_topay(), precision=5)}&nbsp;€</td>
					${request.layout_manager.render_panel('action_buttons_td', links=stream_actions(customer))}
				</tr>
			% endfor
			<tr class='row_recap'>
				<td class="col_text" scope="row" colspan="${colspan}">Total</td>
				<td class='col_number'>${api.format_amount(total_income, precision=5)}&nbsp;€</td>
				<td class='col_number'>${api.format_amount(total_topay, precision=5)}&nbsp;€</td>
				<td>&nbsp;</td>
			</tr>
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
