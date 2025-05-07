from odoo import models, fields, api

class Maintenance(models.Model):
    _name = 'parc.maintenance'
    _description = 'Maintenance Informatique'
    _order = 'date_intervention desc'
    
    name = fields.Char('Référence', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('parc.maintenance') or 'MAINT0001')
    equipement_id = fields.Many2one('parc.equipement', string='Équipement', required=True)
    date_intervention = fields.Datetime('Date d\'intervention', required=True)
    technicien_id = fields.Many2one('hr.employee', string='Technicien', domain="[('user_id', 'in', allowed_technicien_ids)]")
    allowed_technicien_ids = fields.Many2many('res.users', compute="_compute_allowed_techniciens")
    description = fields.Text('Description de l\'intervention')
    temps_passe = fields.Float('Temps passé (heures)')
    etat = fields.Selection([
        ('planifie', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminée'),
        ('annule', 'Annulée')
    ], string='État', default='planifie')
    pieces_utilisees = fields.Text('Pièces utilisées')
    
    @api.depends()
    def _compute_allowed_techniciens(self):
        """Calculer les techniciens autorisés - uniquement les employés avec un poste technique assigné"""
        for maintenance in self:
            # Rechercher les employés qui ont un poste technique défini (techniciens)
            techniciens = self.env['hr.employee'].search([('poste_technique_id', '!=', False)])
            
            # Stocker les IDs des utilisateurs associés à ces techniciens
            techniciens_user_ids = techniciens.mapped('user_id').ids
            
            # Assigner ces utilisateurs au champ allowed_technicien_ids
            maintenance.allowed_technicien_ids = [(6, 0, techniciens_user_ids)]
    
    @api.onchange('technicien_id')
    def _onchange_technicien(self):
        """Auto-assigner l'utilisateur actuel s'il est technicien"""
        if not self.technicien_id and self.env.user.has_group('gestion_parc_informatique.group_parc_technicien'):
            tech = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            if tech:
                self.technicien_id = tech.id

    def write(self, vals):
        # Lorsqu'une maintenance passe en état "en_cours"
        if vals.get('etat') == 'en_cours' and self.equipement_id:
            # Mettre l'équipement en maintenance automatiquement
            self.equipement_id.sudo().write({'etat': 'maintenance'})
        
        # Lorsqu'une maintenance est terminée
        elif vals.get('etat') == 'termine' and self.equipement_id:
            # Remettre l'équipement en état opérationnel
            self.equipement_id.sudo().write({'etat': 'operationnel'})
        
        return super(Maintenance, self).write(vals)