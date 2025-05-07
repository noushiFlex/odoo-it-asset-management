from odoo import models, fields, api

class SiteClient(models.Model):
    _name = 'parc.site.client'
    _description = 'Site client'
    
    name = fields.Char('Nom du site', required=True)
    client_id = fields.Many2one('res.partner', string='Client', required=True)
    adresse = fields.Text('Adresse')
    code_postal = fields.Char('Code postal')
    ville = fields.Char('Ville')
    pays_id = fields.Many2one('res.country', string='Pays')
    contact_id = fields.Many2one('res.partner', string='Contact sur site')
    telephone = fields.Char('Téléphone')
    email = fields.Char('Email')
    equipement_ids = fields.One2many('parc.equipement', 'site_id', string='Équipements sur site')
    notes = fields.Text('Notes')