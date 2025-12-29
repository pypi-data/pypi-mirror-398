<%inherit file="/layouts/default.mako" />
<%namespace file="/base/utils.mako" import="format_text" />


<%block name='actionmenucontent'>
<div class='main_toolbar action_tools'>
    <div class='layout flex main_actions'>
        ${request.layout_manager.render_panel('action_buttons', links=stream_main_actions())}
        ${request.layout_manager.render_panel('action_buttons', links=stream_more_actions())}
    </div>
</div>
</%block>

<%block name='content'>
    <div class="separate_bottom layout flex">
        <div>
            <div class="layout flex">
                <span class="user_avatar">${api.icon('building')}</span>
                <div>
                    <h3>${supplier_data.company_name}</h3>
                    SIREN : ${supplier_data.siren}
                </div>
            </div>
            <div class="data_display">
                <div>
                    ${supplier_data.address}<br/>
                    % if supplier_data.additional_address:
                        ${supplier_data.additional_address}<br/>
                    % endif
                    ${supplier_data.zip_code} ${supplier_data.city}
                </div>
            </div>
        </div>
    </div>

Utilisé par ${len(company_suppliers)} enseignes :
<div class='table_container'>
<table class="hover_table">
    <thead>
        <th scope="col" class="col_text">Enseigne</th>
        <th scope="col" class="col_text">Nom</th>
        <th scope="col" class="col_text">Ville</th>
        <th scope="col" class="col_text">Compte Général</th>
        <th scope="col" class="col_text">Compte Tiers</th>
        <th scope="col" class="col_text">Factures HT</th>
        <th scope="col" class="col_actions">Actions</th>
    </thead>
    <tbody>

            <tr class="row_recap">
                <th scope="row" colspan="5" class="col_text">Total</th>
                <td class="col_number">${api.format_amount(total_invoiced)}&nbsp;€</td>
                <td></td>
            </tr>
    % for company_supplier in company_suppliers:
        <tr>
            <td class="col_text">${company_supplier.company.name}</td>
            <td class="col_text">${company_supplier.label}
            % if company_supplier.siret:
            <small>${company_supplier.siret}</small>
            % endif
            
            % if company_supplier.registration:
            <small>${company_supplier.registration}</small>
            % endif
            </td>
            <td class="col_text">${company_supplier.city}</td>
            <td class="col_text">${company_supplier.compte_cg}</td>
            <td class="col_text">${company_supplier.compte_tiers}</td>
            <td class='col_number'>${api.format_amount(get_row_total_ht(company_supplier))}&nbsp;€</td>
            ${request.layout_manager.render_panel('action_buttons_td', links=stream_col_actions(company_supplier))}
        </tr>
        
    % endfor

            <tr class="row_recap">
                <th scope="row" colspan="5" class="col_text">Total</th>
                <td class="col_number">${api.format_amount(total_invoiced)}&nbsp;€</td>
                <td></td>
            </tr>
    </tbody>
</table>
</div>
</%block>
