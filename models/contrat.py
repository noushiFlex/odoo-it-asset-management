# models/contrat.py
from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ContratService(models.Model):
    _name = 'parc.contrat.service'
    _description = 'Contrat de Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Ajouter ces mixins
    
    name = fields.Char('Référence', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('parc.contrat.service') or 'CNT0001')
    client_id = fields.Many2one('parc.client', string='Client', required=True)
    date_debut = fields.Date('Date de début', required=True)
    date_fin = fields.Date('Date de fin')
    periodicite_facturation = fields.Selection([
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel')
    ], string='Périodicité de facturation', default='mensuel')
    equipements_ids = fields.One2many('parc.equipement', 'contrat_id', string='Équipements couverts')
    montant = fields.Float("Montant HT", required=True)
    derniere_facture = fields.Date("Date de dernière facturation")
    facture_ids = fields.Many2many('account.move', string='Factures')
    sale_order_id = fields.Many2one('sale.order', string='Commande récurrente liée')
    
    @api.model
    def _cron_generer_factures(self):
        """Cron job amélioré pour générer les factures"""
        aujourd_hui = fields.Date.today()
        contrats_a_facturer = self.env['parc.contrat.service'].search([
            '|', ('date_fin', '=', False), ('date_fin', '>=', aujourd_hui),
            ('date_debut', '<=', aujourd_hui)
        ])

        factures_generees = 0
        total_montant = 0
        
        for contrat in contrats_a_facturer:
            date_prochaine = self._calculer_date_prochaine_facture(contrat)
            
            if date_prochaine <= aujourd_hui:
                facture, montant = contrat._generer_facture()
                factures_generees += 1
                total_montant += montant
                
                # Notification par email au client
                template = self.env.ref('gestion_parc_informatique.email_template_nouvelle_facture')
                template.send_mail(facture.id, force_send=True)
                
        return {
            'factures_generees': factures_generees,
            'montant_total': total_montant
        }
    
    def _calculer_date_prochaine_facture(self, contrat):
        """Calcule la date de la prochaine facture basée sur la périodicité"""
        date_prochaine_facture = contrat.derniere_facture or contrat.date_debut
        
        if contrat.periodicite_facturation == 'mensuel':
            date_prochaine_facture = date_prochaine_facture + relativedelta(months=1)
        elif contrat.periodicite_facturation == 'trimestriel':
            date_prochaine_facture = date_prochaine_facture + relativedelta(months=3)
        elif contrat.periodicite_facturation == 'semestriel':
            date_prochaine_facture = date_prochaine_facture + relativedelta(months=6)
        elif contrat.periodicite_facturation == 'annuel':
            date_prochaine_facture = date_prochaine_facture + relativedelta(years=1)
            
        return date_prochaine_facture
    
    def _generer_facture(self):
        """Génère une facture pour le contrat donné avec une meilleure intégration"""
        self.ensure_one()
        # Créer une facture (account.move)
        journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1).id
        
        # Vérifier si ce n'est pas une facturation en double
        aujourd_hui = fields.Date.today()
        factures_recentes = self.env['account.move'].search([
            ('partner_id', '=', self.client_id.id),
            ('invoice_date', '=', aujourd_hui),
            ('ref', '=', f'Contrat {self.name}')
        ])
        
        if factures_recentes:
            return factures_recentes[0], self.montant, {
                'name': 'Facture déjà créée',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': factures_recentes[0].id,
            }
        
        # Générer une description détaillée incluant les équipements
        description = f"Services Infogérance {self.name} - Période: {aujourd_hui.strftime('%d/%m/%Y')}"
        equipements_str = ", ".join([eq.name for eq in self.equipements_ids])
        if equipements_str:
            description += f"\nÉquipements couverts: {equipements_str}"
        
        facture_vals = {
            'partner_id': self.client_id.id,
            'move_type': 'out_invoice',
            'invoice_date': aujourd_hui,
            'journal_id': journal_id,
            'payment_reference': f'Contrat {self.name}',
            'ref': f'Contrat {self.name} - {self.periodicite_facturation}',
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1,
                'price_unit': self.montant,
                'tax_ids': [(6, 0, self.env['account.tax'].search([('type_tax_use', '=', 'sale')], limit=1).ids)],
            })],
        }
        
        # Créer la facture
        facture = self.env['account.move'].create(facture_vals)
        
        # Mettre à jour la date de dernière facture
        self.derniere_facture = aujourd_hui
        
        # Lier la facture au contrat
        self.write({
            'facture_ids': [(4, facture.id)]
        })
        
        # Créer une action pour voir la facture
        action = {
            'name': 'Facture créée',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': facture.id,
        }
        
        return facture, self.montant, action
    
    def action_generer_facture(self):
        """Génère une facture manuellement pour ce contrat"""
        self.ensure_one()
        facture, montant, action = self._generer_facture()
        return action
    
    def action_convert_to_subscription(self):
        """Convertir le contrat de service en commande récurrente Odoo 18"""
        self.ensure_one()
        
        # Créer une commande de vente récurrente
        sale_order_vals = {
            'partner_id': self.client_id.id,
            'date_order': fields.Datetime.now(),
            'validity_date': self.date_fin,
            'note': f"Contrat d'infogérance: {self.name}",
        }
        
        # Créer une ligne de commande
        order_line_vals = {
            'name': f"Services Infogérance {self.name}",
            'product_uom_qty': 1,
            'price_unit': self.montant,
        }
        
        # Si un produit 'Service' existe, l'utiliser
        product = self.env['product.product'].search([('name', 'ilike', 'service'), ('type', '=', 'service')], limit=1)
        if product:
            order_line_vals['product_id'] = product.id
        else:
            # Créer un produit de service par défaut si nécessaire
            product = self.env['product.product'].create({
                'name': 'Service Infogérance',
                'type': 'service',
                'invoice_policy': 'order',
                'uom_id': self.env.ref('uom.product_uom_unit').id,
                'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            })
            order_line_vals['product_id'] = product.id
        
        # Créer la commande
        sale_order = self.env['sale.order'].create(sale_order_vals)
        sale_order.write({
            'order_line': [(0, 0, order_line_vals)]
        })
        
        # Convertir en abonnement après création
        # La méthode peut varier selon votre installation exacte d'Odoo 18
        if hasattr(sale_order, 'prepare_subscription'):
            # Configurer la récurrence
            interval = 1
            unit = 'month' if self.periodicite_facturation == 'mensuel' else 'year'
            sale_order.prepare_subscription(interval, unit)
        elif hasattr(sale_order, 'action_subscription_create'):
            # Alternative pour certaines installations
            sale_order.action_subscription_create()
        
        # Lier la commande au contrat
        self.sale_order_id = sale_order.id
        
        return {
            'name': 'Commande récurrente créée',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
        }
    
    @api.model
    def _cron_verifier_contrats_expiration(self):
        """Vérifier les contrats qui arrivent à expiration"""
        # Période d'alerte: contrats qui expirent dans les 30 prochains jours
        date_debut_alerte = fields.Date.today()
        date_fin_alerte = fields.Date.today() + timedelta(days=30)
        
        # Rechercher les contrats qui expirent dans cette période
        contrats_expiration = self.search([
            ('date_fin', '>=', date_debut_alerte),
            ('date_fin', '<=', date_fin_alerte)
        ])
        
        # Créer des activités pour chaque contrat proche de l'expiration
        for contrat in contrats_expiration:
            # Calculer le nombre de jours restants
            jours_restants = (contrat.date_fin - fields.Date.today()).days
            
            # Créer une activité pour le responsable commercial
            responsable_id = contrat.client_id.user_id.id or self.env.user.id
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': f"Le contrat {contrat.name} avec {contrat.client_id.name} expire dans {jours_restants} jours. Contactez le client pour discuter du renouvellement.",
                'res_id': contrat.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'parc.contrat.service')], limit=1).id,
                'user_id': responsable_id,
                'summary': f"Contrat expirant dans {jours_restants} jours",
                'date_deadline': fields.Date.today() + timedelta(days=2)  # Urgent: 2 jours pour agir
            })
            
            # Envoyer un email au commercial responsable
            template_id = self.env.ref('gestion_parc_informatique.email_template_contrat_expiration', False)
            if template_id:
                template_id.send_mail(contrat.id, force_send=True)
                
        return {
            'contrats_notification': len(contrats_expiration)
        }
    
    def action_envoyer_notification_expiration(self):
        """Permet à l'administrateur d'envoyer manuellement une notification d'expiration"""
        self.ensure_one()
        
        if not self.date_fin:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': 'Ce contrat n\'a pas de date de fin définie.',
                    'type': 'danger',
                }
            }
        
        # Calculer le nombre de jours restants
        jours_restants = (self.date_fin - fields.Date.today()).days
        
        if jours_restants < 0:
            message = f"Le contrat a déjà expiré depuis {abs(jours_restants)} jours."
            notification_type = 'danger'
        else:
            message = f"Le contrat expire dans {jours_restants} jours."
            notification_type = 'warning' if jours_restants <= 30 else 'info'
        
        # Créer une activité pour le responsable commercial
        responsable_id = self.client_id.user_id.id or self.env.user.id
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'note': f"[MANUEL] Le contrat {self.name} avec {self.client_id.name} {message} Contactez le client pour discuter du renouvellement.",
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', 'parc.contrat.service')], limit=1).id,
            'user_id': responsable_id,
            'summary': f"Contrat expirant dans {jours_restants} jours",
            'date_deadline': fields.Date.today() + timedelta(days=1)  # Urgent: 1 jour pour agir
        })
        
        # Envoyer un email au commercial responsable
        template_id = self.env.ref('gestion_parc_informatique.email_template_contrat_expiration', False)
        if template_id:
            template_id.send_mail(self.id, force_send=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notification envoyée',
                'message': f"Une notification a été envoyée au responsable commercial. {message}",
                'type': notification_type,
            }
        }