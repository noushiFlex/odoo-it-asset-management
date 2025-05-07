from odoo import models, fields, api
from datetime import timedelta

class Logiciel(models.Model):
    _name = 'parc.logiciel'
    _description = 'Logiciel'
    
    name = fields.Char('Nom', required=True)
    editeur = fields.Char('Éditeur')
    version = fields.Char('Version')
    type = fields.Selection([
        ('os', 'Système d\'exploitation'),
        ('bureautique', 'Bureautique'),
        ('securite', 'Sécurité'),
        ('metier', 'Application Métier'),
        ('autre', 'Autre')
    ], string='Type', default='autre')
    description = fields.Text('Description')
    licence_ids = fields.One2many('parc.licence', 'logiciel_id', string='Licences')
    
class Licence(models.Model):
    _name = 'parc.licence'
    _description = 'Licence logicielle'
    
    name = fields.Char('Référence', required=True)
    logiciel_id = fields.Many2one('parc.logiciel', string='Logiciel', required=True)
    equipement_id = fields.Many2one('parc.equipement', string='Équipement')
    client_id = fields.Many2one('res.partner', string='Client')
    cle_activation = fields.Char('Clé d\'activation')
    date_achat = fields.Date('Date d\'achat')
    date_expiration = fields.Date('Date d\'expiration')
    type_licence = fields.Selection([
        ('perpetuelle', 'Perpétuelle'),
        ('abonnement', 'Abonnement'),
        ('oem', 'OEM'),
        ('volume', 'Contrat de volume')
    ], string='Type de licence', default='perpetuelle')
    nb_utilisateurs = fields.Integer('Nombre d\'utilisateurs', default=1)
    active = fields.Boolean('Active', default=True)
    notes = fields.Text('Notes')
    
    @api.model
    def _cron_verifier_licences_expirees(self):
        """Vérifier les licences qui expireront bientôt"""
        date_limite = fields.Date.today() + timedelta(days=30)
        licences = self.search([
            ('date_expiration', '>=', fields.Date.today()),
            ('date_expiration', '<=', date_limite)
        ])
        
        for licence in licences:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                'note': f"La licence {licence.name} pour {licence.logiciel_id.name} expire le {licence.date_expiration}",
                'res_id': licence.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'parc.licence')], limit=1).id,
                'user_id': self.env.user.id,
            })