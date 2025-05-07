# Ajoutons des fonctionnalités avancées à HelpdeskTicket
from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    # Remplacer le champ equipement_id par un champ de référence
    objet_concerne = fields.Reference(selection=[
        ('parc.equipement', 'Équipement'),
        ('parc.licence', 'Licence')
    ], string='Objet concerné')
    
    # Garder ces champs pour la compatibilité mais les rendre calculés
    equipement_id = fields.Many2one('parc.equipement', string='Équipement concerné (ancien)', compute='_compute_equipement_id', store=True)
    licence_id = fields.Many2one('parc.licence', string='Licence concernée (ancien)', compute='_compute_licence_id', store=True)
    contrat_id = fields.Many2one('parc.contrat.service', string='Contrat associé')
    historique_maintenance_ids = fields.One2many('parc.maintenance', compute='_compute_historique')
    
    @api.depends('objet_concerne')
    def _compute_equipement_id(self):
        for ticket in self:
            if ticket.objet_concerne and ticket.objet_concerne._name == 'parc.equipement':
                ticket.equipement_id = ticket.objet_concerne.id
            else:
                ticket.equipement_id = False
    
    @api.depends('objet_concerne')
    def _compute_licence_id(self):
        for ticket in self:
            if ticket.objet_concerne and ticket.objet_concerne._name == 'parc.licence':
                ticket.licence_id = ticket.objet_concerne.id
            else:
                ticket.licence_id = False
    
    # Méthode pour calculer l'historique des maintenances
    def _compute_historique(self):
        for ticket in self:
            # Si l'objet est un équipement, on récupère son historique
            if ticket.objet_concerne and ticket.objet_concerne._name == 'parc.equipement':
                ticket.historique_maintenance_ids = self.env['parc.maintenance'].search([
                    ('equipement_id', '=', ticket.objet_concerne.id)
                ])
            # Si c'est une licence et qu'elle est liée à un équipement
            elif ticket.objet_concerne and ticket.objet_concerne._name == 'parc.licence' and ticket.objet_concerne.equipement_id:
                ticket.historique_maintenance_ids = self.env['parc.maintenance'].search([
                    ('equipement_id', '=', ticket.objet_concerne.equipement_id.id)
                ])
            else:
                ticket.historique_maintenance_ids = False
    
    # Méthode pour créer une maintenance à partir d'un ticket
    def create_maintenance(self):
        self.ensure_one()
        equipement_id = False
        
        # Déterminer l'équipement selon le type d'objet concerné
        if self.objet_concerne and self.objet_concerne._name == 'parc.equipement':
            equipement_id = self.objet_concerne.id
        elif self.objet_concerne and self.objet_concerne._name == 'parc.licence' and self.objet_concerne.equipement_id:
            equipement_id = self.objet_concerne.equipement_id.id
            
        if not equipement_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': 'Aucun équipement associé à ce ticket.',
                    'type': 'danger',
                }
            }
            
        # Créer une nouvelle maintenance pour l'équipement
        maintenance = self.env['parc.maintenance'].create({
            'equipement_id': equipement_id,
            'date_intervention': fields.Datetime.now(),
            'description': f"Intervention suite au ticket #{self.id}: {self.name}\n\n{self.description or ''}",
            'etat': 'planifie',
        })
        
        # Retourner une action pour voir la maintenance créée
        return {
            'name': 'Maintenance créée',
            'type': 'ir.actions.act_window',
            'res_model': 'parc.maintenance',
            'view_mode': 'form',
            'res_id': maintenance.id,
        }