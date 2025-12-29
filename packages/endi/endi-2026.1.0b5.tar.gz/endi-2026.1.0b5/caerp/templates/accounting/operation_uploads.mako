<%inherit file="${context['main_template'].uri}" />
<%namespace file="/base/utils.mako" import="dropdown_item"/>
<%namespace file="/base/pager.mako" import="pager"/>
<%namespace file="/base/pager.mako" import="sortable"/>
<%namespace file="/base/searchformlayout.mako" import="searchform"/>

<%block name='beforecontent'>
<% action_links = stream_main_actions() %>
% if next(action_links, None):
	<div class='main_toolbar'>
		<div class='layout flex main_actions'>
			${request.layout_manager.render_panel('action_buttons', links=stream_main_actions())}
		</div>
	</div>
% endif
</%block>

<%block name='content'>

<div class='alert alert-warning'>
	<span class="icon">${api.icon('danger')}</span> <strong>Reports à nouveau</strong><br/><br/>
	Une fois que vos reports à nouveau sont passés en comptabilité pensez à déclarer la clôture comptable pour indiquer aux états de trésorerie de ne plus utiliser les données de l'exercice précédent.<br/><a href='/admin/accounting/accounting_closure' target="_blank" title="Cet écran s’ouvrira dans une nouvelle fenêtre" aria-label="Cet écran s’ouvrira dans une nouvelle fenêtre">Configuration -> Configuration -> Module Comptabilité -> Clôtures comptables</a>
</div>
<div class='alert alert-info'>
	<span class="icon">${api.icon('info-circle')}</span>
	Vous trouverez ci-dessous la liste des fichiers comptables ou synchronisations automatiques traités.
	<br /><br />
	Pour chaque remontée vous pouvez :
	<ul>
		<li>Consulter le détail des écritures importées <small>(pour essayer de comprendre les montants dans les états par exemple)</small></li>
		<li>Supprimer les écritures importées et les indicateurs associés <small>(en cas de problème)</small></li>
		<li>Recalculer les indicateurs pour mettre à jour les états comptables <small>(si vous avez modifié la configuration ou si la génération n'est pas automatisée)</small></li>
	</ul>
</div>

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
					<th scope="col" class="col_text">Type de remontée</th>
					<th scope="col" class="col_text">${sortable("Date", "date")}</th>
					<th scope="col" class="col_text">${sortable("Nom", "filename")}</th>
					<th scope="col" class="col_text">Statut</th>
					<th scope="col" class="col_actions" title="Actions"><span class="screen-reader-text">Actions</span></th>
				</tr>
			</thead>
			<tbody>
			% for entry in records:
				<tr class='tableelement' id='${entry.id}'>
					<td class="col_text">${entry.filetype_label}</td>
					<td class="col_text">
						% if entry.filetype != 'synchronized_accounting':
							Données du ${api.format_date(entry.date)} 
							<small>(importées le ${api.format_datetime(entry.updated_at)})</small>
						% else:
							Données mises à jour le ${api.format_datetime(entry.updated_at)}
						% endif
					</td>
					<td class="col_text">${entry.filename}</td>
					<td class="col_text">
						% if len(entry.operations) == 0:
							<span class="icon tag neutral" title="Cette remontée comptable ne contient aucune écriture">
								Vide
							</span>
						% elif entry.is_upload_valid:
							<span class="icon tag positive" title="Les données de cette remontée comptable sont valides">
								Valide
							</span>
						% else:
							<span class="icon tag negative" title="Cette remontée comptable a rencontré une erreur ou est en cours de traitement">
								Invalide
							</span>
						% endif
					</td>
					${request.layout_manager.render_panel('action_buttons_td', links=stream_actions(entry))}
				</tr>
			% endfor
			</tbody>
		</table>
		% else:
		<table>
			<tbody>
				<tr>
					<td class='col_text'><em>Aucun fichier n’a été traité</em></td>
				</tr>
			</tbody>
		</table>
		% endif
    </div>
    ${pager(records)}
</div>
</%block>
