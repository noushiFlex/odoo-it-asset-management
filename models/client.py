from odoo import models, fields, api

class ParcClient(models.Model):
    _name = 'parc.client'
    _description = 'Client du parc informatique'
    _inherits = {'res.partner': 'partner_id'}  # Héritage par délégation
    
    partner_id = fields.Many2one('res.partner', string='Partenaire', required=True, ondelete='cascade')
    code_client = fields.Char('Code client', copy=False)
    date_debut_relation = fields.Date('Début de la relation')
    est_prospect = fields.Boolean('Prospect', default=False)
    niveau_service = fields.Selection([
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('vip', 'VIP')
    ], string='Niveau de service', default='standard')
    notes_techniques = fields.Text('Notes techniques')
    
    # Champs relationnels
    equipement_ids = fields.One2many('parc.equipement', 'client_id', string='Équipements')
    contrat_ids = fields.One2many('parc.contrat.service', 'client_id', string='Contrats')
    site_ids = fields.One2many('parc.site.client', 'client_id', string='Sites')
    
    equipement_count = fields.Integer(compute='_compute_counts', string="Nombre d'équipements")
    contrat_count = fields.Integer(compute='_compute_counts', string="Nombre de contrats")
    
    @api.depends('equipement_ids', 'contrat_ids')
    def _compute_counts(self):
        for client in self:
            client.equipement_count = len(client.equipement_ids)
            client.contrat_count = len(client.contrat_ids)
            
    def action_view_equipements(self):
        self.ensure_one()
        return {
            'name': 'Équipements',
            'type': 'ir.actions.act_window',
            'res_model': 'parc.equipement',
            'view_mode': 'list,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }
        
    def action_view_contrats(self):
        self.ensure_one()
        return {
            'name': 'Contrats',
            'type': 'ir.actions.act_window',
            'res_model': 'parc.contrat.service',
            'view_mode': 'list,form',
            'domain': [('client_id', '=', self.id)],
            'context': {'default_client_id': self.id},
        }