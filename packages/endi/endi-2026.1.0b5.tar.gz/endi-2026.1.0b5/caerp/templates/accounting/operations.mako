<%inherit file="${context['main_template'].uri}" />
<%namespace file="/base/pager.mako" import="pager"/>
<%namespace file="/base/pager.mako" import="sortable"/>
<%namespace file="/base/searchformlayout.mako" import="searchform"/>

<%block name='actionmenucontent'>
<div class='main_toolbar action_tools'>
  <div class='layout flex main_actions'>
    <div class='btn-group'>
        %if request.context.is_upload_valid:
            ${request.layout_manager.render_panel('menu_dropdown', icon='file-redo', label='Regénérer', links=stream_regenerate_actions(), display_label=True, alignment='left')}
        % endif
        ${request.layout_manager.render_panel('menu_dropdown', icon='eye', label='Voir', links=stream_view_actions(), display_label=True, alignment='left')}
        ${request.layout_manager.render_panel('menu_dropdown', icon='file-export', label='Exporter', links=stream_export_actions(), display_label=True, alignment='left')}
    </div>
    <div class='btn-group'>
        ${request.layout_manager.render_panel('action_buttons', links=stream_delete_actions())}
    </div>
  </div>
</div>
</%block>

<%block name='content'>

%if not request.context.is_upload_valid:
    <div class="alert alert-danger">
        <span class='icon'>${api.icon('exclamation-triangle')}</span> <strong>Remontée comptable invalide</strong><br/><br/>
        Cette remontée comptable a rencontré un problème ou est actuellement en cours de traitement.<br/><br/>
        Les écritures correspondantes pourraient être incomplètes ou erronnées.
    </div>
% endif

<div class='alert alert-info'>
    <span class="icon">${api.icon('info-circle')}</span>
    Voici les écritures extraites du fichier <strong>${request.context.filename}</strong>.<br /><br />
    Si vous avez apporté des modifications à la configuration des indicateurs, vous pouvez regénérer les états comptables, les indicateurs issus des écritures ci-dessous seront mis à jour.<br /><br />
    Si certaines écritures n'ont pas été associées à des enseignes dans enDI, par exemple parce qu'un compte analytique n'a pas été configuré, elles sont signalées par l’icône <span class="icon status caution" title="Écritures n’ayant pas pu être associées à une enseigne" aria-label="Écritures n’ayant pas pu être associées à une enseigne">${api.icon('exclamation-triangle')}</span> et vous pouvez :
    <ol>
        <li>Supprimer cet import</li>
        <li>Modifier la configuration de l'enseigne</li>
        <li>Re-déposer le fichier d'écritures</li>
    </ol>
</div>

${searchform()}

<div>
    <div>${records.item_count} Résultat(s)</div>
    <div class='table_container'>
        <table class="top_align_table">
        % if records:
            <thead>
                <tr>
                    <th scope="col" class="col_status" title="Statut"><span class="screen-reader-text">Statut</span></th>
                    <th scope="col">${sortable("Compte analytique", "analytical_account")}</th>
                    <th scope="col">${sortable("Compte général", "general_account")}</th>
                    <th scope="col" class="col_date">${sortable('Date', 'date')}</th>
                    <th scope="col" class="col_text">Libellé</th>
                    <th scope="col" class="col_number">Débit</th>
                    <th scope="col" class="col_number">Crédit</th>
                    <th scope="col" class="col_number">Solde</th>
                </tr>
            </thead>
            <tbody>
			% for entry in records:
				<tr class='tableelement operation-associated-${bool(entry.company_id)}' id='${entry.id}'>
					<td class="col_status">
						% if entry.company_id:
							<span class="icon status valid" title="Écritures associées à une enseigne" aria-label="Écritures associées à une enseigne">
                                ${api.icon('link')}
							</span>
						% else:
							<span class="icon status caution" title="Écritures n’ayant pas pu être associées à une enseigne" aria-label="Écritures n’ayant pas pu être associées à une enseigne">
                                ${api.icon('exclamation-triangle')}
							</span>
						% endif
					</td>
					<td>${entry.analytical_account}</td>
					<td>${entry.general_account}</td>
					<td class="col_date">${api.format_date(entry.date)}</td>
					<td class="col_text">${entry.label}</td>
					<td class="col_number">${api.format_float(entry.debit, precision=2)|n} €</td>
					<td class="col_number">${api.format_float(entry.credit, precision=2)|n} €</td>
					<td class="col_number">${api.format_float(entry.balance, precision=2)|n} €</td>
				</tr>
			% endfor
            </tbody>
        % else:
            <tbody>
				<tr>
					<td class='col_text'><em>Aucune écriture comptable correspondante</em></td>
				</tr>
            </tbody>
        % endif
        </table>
    </div>
    ${pager(records)}
</div>
</%block>
