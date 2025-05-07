from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import datetime

class ParcinformatiquePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        
        partner = request.env.user.partner_id
        
        if 'equipement_count' in counters:
            equipement_count = request.env['parc.equipement'].search_count([('client_id', '=', partner.id)])
            values['equipement_count'] = equipement_count
            
        if 'contrat_count' in counters:
            contrat_count = request.env['parc.contrat.service'].search_count([('client_id', '=', partner.id)])
            values['contrat_count'] = contrat_count
            
        if 'ticket_count' in counters:
            ticket_count = request.env['helpdesk.ticket'].search_count([('partner_id', '=', partner.id)])
            values['ticket_count'] = ticket_count
            
        # Ajout du compteur de licences
        if 'licence_count' in counters:
            licence_count = request.env['parc.licence'].search_count([('client_id', '=', partner.id)])
            values['licence_count'] = licence_count

        # Ajout du compteur de factures
        if 'invoice_count' in counters:
            invoice_count = request.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('state', 'in', ['posted', 'paid'])
            ])
            values['invoice_count'] = invoice_count
            
        return values
    
    @http.route(['/my/equipements', '/my/equipements/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipements(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Equipement = request.env['parc.equipement']
        
        domain = [('client_id', '=', partner.id)]
        
        # Pagination
        equipement_count = Equipement.search_count(domain)
        pager = portal_pager(
            url="/my/equipements",
            total=equipement_count,
            page=page,
            step=self._items_per_page
        )
        
        # Recherche des équipements avec pagination
        equipements = Equipement.search(domain, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'equipements': equipements,
            'page_name': 'equipement',
            'pager': pager,
            'default_url': '/my/equipements',
        })
        
        return request.render("gestion_parc_informatique.portal_my_equipements", values)
    
    @http.route(['/my/equipements/<int:equipement_id>'], type='http', auth="user", website=True)
    def portal_equipement_page(self, equipement_id, **kw):
        equipement = request.env['parc.equipement'].browse(equipement_id)
        
        if not equipement or equipement.client_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = {
            'equipement': equipement,
            'page_name': 'equipement',
        }
        
        return request.render("gestion_parc_informatique.portal_equipement_page", values)
    
    @http.route(['/my/licences', '/my/licences/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_licences(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Licence = request.env['parc.licence']
        
        domain = [('client_id', '=', partner.id)]
        
        licence_count = Licence.search_count(domain)
        pager = portal_pager(
            url="/my/licences",
            total=licence_count,
            page=page,
            step=self._items_per_page
        )
        
        licences = Licence.search(domain, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'licences': licences,
            'page_name': 'licence',
            'pager': pager,
            'default_url': '/my/licences',
        })
        
        return request.render("gestion_parc_informatique.portal_my_licences", values)
    
    @http.route(['/my/licences/<int:licence_id>'], type='http', auth="user", website=True)
    def portal_licence_page(self, licence_id, **kw):
        licence = request.env['parc.licence'].browse(licence_id)
        
        if not licence or licence.client_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = {
            'licence': licence,
            'page_name': 'licence',
        }
        
        return request.render("gestion_parc_informatique.portal_licence_page", values)

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tickets(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        HelpdeskTicket = request.env['helpdesk.ticket']
        
        domain = [('partner_id', '=', partner.id)]
        
        ticket_count = HelpdeskTicket.search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            total=ticket_count,
            page=page,
            step=self._items_per_page
        )
        
        tickets = HelpdeskTicket.search(domain, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'tickets': tickets,
            'page_name': 'ticket',
            'pager': pager,
            'default_url': '/my/tickets',
        })
        
        return request.render("gestion_parc_informatique.portal_my_tickets", values)

    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=True)
    def portal_ticket_page(self, ticket_id, **kw):
        ticket = request.env['helpdesk.ticket'].browse(ticket_id)
        
        if not ticket or ticket.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = {
            'ticket': ticket,
            'page_name': 'ticket',
        }
        
        return request.render("gestion_parc_informatique.portal_ticket_page", values)

    @http.route(['/my/tickets/create'], type='http', auth="user", website=True)
    def portal_create_ticket(self, **kw):
        """Affiche le formulaire de création de ticket"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Récupérer les équipements du client
        equipements = request.env['parc.equipement'].search([('client_id', '=', partner.id)])
        
        # Récupérer les licences du client
        licences = request.env['parc.licence'].search([('client_id', '=', partner.id)])
        
        values.update({
            'equipements': equipements,
            'licences': licences,
            'page_name': 'create_ticket',
        })
        
        return request.render("gestion_parc_informatique.portal_create_ticket", values)

    @http.route(['/my/tickets/submit'], type='http', auth="user", website=True)
    def portal_submit_ticket(self, **kw):
        """Traite la soumission du formulaire de ticket"""
        partner = request.env.user.partner_id
        
        ticket_vals = {
            'name': kw.get('name'),
            'description': kw.get('description'),
            'partner_id': partner.id,
        }
        
        # Gestion du type de ticket
        ticket_type = kw.get('ticket_type')
        
        if ticket_type == 'equipement' and kw.get('equipement_id'):
            equipement_id = int(kw.get('equipement_id'))
            # Utiliser le nouveau champ de référence
            ticket_vals['objet_concerne'] = f'parc.equipement,{equipement_id}'
            
            # Récupérer le contrat associé à l'équipement
            equipement = request.env['parc.equipement'].browse(equipement_id)
            if equipement.contrat_id:
                ticket_vals['contrat_id'] = equipement.contrat_id.id
        
        elif ticket_type == 'licence' and kw.get('licence_id'):
            licence_id = int(kw.get('licence_id'))
            # Utiliser le nouveau champ de référence
            ticket_vals['objet_concerne'] = f'parc.licence,{licence_id}'
            
            # Récupérer d'autres informations de la licence
            licence = request.env['parc.licence'].browse(licence_id)
            ticket_vals['description'] = f"Problème avec licence: {licence.name} - {licence.logiciel_id.name}\n\n{ticket_vals['description']}"
            
            # Si la licence est associée à un contrat via son équipement
            if licence.equipement_id and licence.equipement_id.contrat_id:
                ticket_vals['contrat_id'] = licence.equipement_id.contrat_id.id
        
        # Créer le ticket avec sudo() pour contourner les restrictions d'accès
        ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)
        
        # Rediriger vers la page du ticket
        return request.redirect('/my/tickets/%s' % ticket.id)

    @http.route(['/my/contrats', '/my/contrats/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contrats(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Contrat = request.env['parc.contrat.service']
        
        domain = [('client_id', '=', partner.id)]
        
        contrat_count = Contrat.search_count(domain)
        pager = portal_pager(
            url="/my/contrats",
            total=contrat_count,
            page=page,
            step=self._items_per_page
        )
        
        contrats = Contrat.search(domain, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'contrats': contrats,
            'page_name': 'contrat',
            'pager': pager,
            'default_url': '/my/contrats',
        })
        
        return request.render("gestion_parc_informatique.portal_my_contrats", values)

    @http.route(['/my/contrats/<int:contrat_id>'], type='http', auth="user", website=True)
    def portal_contrat_page(self, contrat_id, **kw):
        contrat = request.env['parc.contrat.service'].browse(contrat_id)
        
        if not contrat or contrat.client_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = {
            'contrat': contrat,
            'page_name': 'contrat',
        }
        
        return request.render("gestion_parc_informatique.portal_contrat_page", values)

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        AccountMove = request.env['account.move']
        
        domain = [
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice')
        ]
        
        invoice_count = AccountMove.search_count(domain)
        pager = portal_pager(
            url="/my/invoices",
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        
        invoices = AccountMove.search(domain, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'invoices': invoices,
            'page_name': 'invoice',
            'pager': pager,
            'default_url': '/my/invoices'
        })
        
        return request.render("gestion_parc_informatique.portal_my_invoices", values)

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="user", website=True)
    def portal_invoice_page(self, invoice_id, **kw):
        invoice = request.env['account.move'].browse(invoice_id)
        
        if not invoice or invoice.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = {
            'invoice': invoice,
            'page_name': 'invoice',
        }
        
        return request.render("gestion_parc_informatique.portal_invoice_page", values)

    @http.route(['/my/invoices/<int:invoice_id>/download'], type='http', auth="user", website=True)
    def portal_invoice_download(self, invoice_id, **kw):
        invoice = request.env['account.move'].browse(invoice_id)
        
        if not invoice or invoice.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        pdf = request.env.ref('account.account_invoices').sudo()._render_qweb_pdf([invoice.id])[0]
        
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', f'attachment; filename=Facture_{invoice.name}.pdf;')
        ]
        
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/contracts/<int:contract_id>/create_invoice'], type='http', auth="user", website=True)
    def portal_contract_create_invoice(self, contract_id, **kw):
        contrat = request.env['parc.contrat.service'].browse(contract_id)
        
        if not contrat or contrat.client_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        # Créer la facture pour ce contrat
        facture, montant, action = contrat.sudo()._generer_facture()
        
        # Rediriger vers la facture créée
        return request.redirect(f'/my/invoices/{facture.id}')