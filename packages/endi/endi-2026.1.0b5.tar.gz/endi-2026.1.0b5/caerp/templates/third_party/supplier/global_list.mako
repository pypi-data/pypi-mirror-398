<%inherit file="${context['main_template'].uri}" />
<%namespace file="/base/pager.mako" import="pager"/>
<%namespace file="/base/pager.mako" import="sortable"/>
<%namespace file="/base/searchformlayout.mako" import="searchform"/>

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
                    <th scope="col" class="col_text">${sortable("SIREN", "siren")}</th>
                    <th scope="col" class="col_text">${sortable("Nom du fournisseur", "company_name")}</th>
                    <th scope="col" class="col_text">${sortable("Dernière mise à jour", "last_update")}</th>
                    <th scope="col" class="col_text">${sortable("Nombre d'enseignes associées", "nb_companies")}</th>
                    <th scope="col" class="col_text">${sortable("Enseigne(s) associées", "company_name")}</th>
                    <th scope="col" class="col_actions" title="Actions"><span class="screen-reader-text">Actions</span></th>
                </tr>
            </thead>
            <tbody>
        % else:
        <table>
            <tbody>
				<tr>
					<td class="col_text">
						<em>Aucun fournisseur commun n’est référencé</em>
					</td>
				</tr>
       % endif
            % for row in records:
                <tr class='tableelement'>                    
                    <% tooltip_title = "Voir le fournisseur commun « " + row['name'] + " »" %>
                    <td class="col_text" title="${tooltip_title}">
                        % if row['siren']:
                            ${row['siren']}
                        % else:
                            <em>Non renseigné</em>
                        % endif
                    </td>
                    <td class="col_text">                 
                        <a href="${get_item_url(row)}" title="${tooltip_title}" aria-label="${tooltip_title}">${row['name']}</a>
                    </td>
                    <td class="col_text" title="${tooltip_title}">
                        ${row['api_last_update']}
                    </td>
                    <td class="col_text" title="${tooltip_title}">
                        ${row['nb_companies']}                 
                    </td>
                    <td class="col_text">
                        % if row['nb_companies'] == 1:
                        ${row['company_name']}
                        % else:
                        ${row['nb_companies']} enseignes associées
                        % endif
                    </td>
                    
                    ${request.layout_manager.render_panel('action_buttons_td', links=stream_actions(row))}
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
