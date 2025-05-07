from odoo import models, fields

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    maintenance_ids = fields.One2many('parc.maintenance', 'technicien_id', string='Maintenances effectuées')
    equipement_count = fields.Integer(compute='_compute_equipement_count', string="Nombre d'équipements maintenus")
    # Nouveaux champs pour les techniciens
    certifications = fields.Char('Certifications', help="Certifications techniques obtenues")
    specialite = fields.Char('Spécialités', help="Domaines d'expertise technique")
    poste_technique_id = fields.Many2one('hr.poste.technique', string='Poste technique')
    
    def _compute_equipement_count(self):
        for emp in self:
            # Compter les équipements uniques sur lesquels l'employé a fait des maintenances
            emp.equipement_count = len(self.env['parc.maintenance'].search([
                ('technicien_id', '=', emp.id)
            ]).mapped('equipement_id'))
    
    def action_view_technicien_maintenances(self):
        """Voir toutes les maintenances effectuées par ce technicien"""
        self.ensure_one()
        return {
            'name': f'Interventions de {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'parc.maintenance',
            'view_mode': 'list,form',
            'domain': [('technicien_id', '=', self.id)],
            'context': {'default_technicien_id': self.id},
        }