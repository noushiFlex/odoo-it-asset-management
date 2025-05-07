from odoo import models, fields

class PosteTechnique(models.Model):
    _name = 'hr.poste.technique'
    _description = 'Poste Technique'
    _order = 'sequence, name'
    
    name = fields.Char('Nom du poste', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Séquence', default=10)
    competences_requises = fields.Text('Compétences requises')
    niveau = fields.Selection([
        ('junior', 'Junior'),
        ('intermediaire', 'Intermédiaire'),
        ('senior', 'Senior'),
        ('expert', 'Expert')
    ], string='Niveau', default='intermediaire')
    active = fields.Boolean('Actif', default=True)