# models/equipement.py
from odoo import models, fields, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class Equipement(models.Model):
    _name = 'parc.equipement'
    _description = 'Équipement Informatique'
    
    name = fields.Char('Nom', required=True)
    numero_serie = fields.Char('Numéro de Série')
    type_equipement = fields.Selection([
        ('ordinateur', 'Ordinateur'),
        ('imprimante', 'Imprimante'),
        ('reseau', 'Équipement Réseau'),
        ('autre', 'Autre')
    ], string='Type', required=True)
    client_id = fields.Many2one('res.partner', string='Client')
    utilisateur_id = fields.Many2one('res.users', string='Utilisateur Final')
    date_achat = fields.Date('Date d\'achat')
    fin_garantie = fields.Date('Fin de Garantie')
    etat = fields.Selection([
        ('operationnel', 'Opérationnel'),
        ('maintenance', 'En Maintenance'),
        ('panne', 'En Panne'),
        ('retire', 'Retiré')
    ], string='État', default='operationnel')
    historique_maintenance_ids = fields.One2many('parc.maintenance', 'equipement_id', string='Historique de Maintenance')
    contrat_id = fields.Many2one('parc.contrat.service', string='Contrat de service')
    
    # Ajoutez cette méthode directement dans la classe
    def action_view_maintenance(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Maintenances",
            "res_model": "parc.maintenance",
            "domain": [("equipement_id", "=", self.id)],
            "view_mode": "tree,form",
            "context": {},
        }
    
    # Ajouter ces champs au modèle Equipement
    contact_technique_id = fields.Many2one('res.partner', string='Contact Technique', 
        help="Personne à contacter pour les questions techniques concernant cet équipement")
    emplacement = fields.Char('Emplacement', 
        help="Localisation physique de l'équipement (bureau, étage, bâtiment...)")
    notes_utilisateur = fields.Text('Notes utilisateur', 
        help="Informations spécifiques concernant l'utilisation de cet équipement")
    site_id = fields.Many2one('parc.site.client', string='Site')
    valeur_achat = fields.Float('Valeur d\'achat HT')
    duree_amortissement = fields.Integer('Durée amortissement (mois)', default=36)
    valeur_residuelle = fields.Float('Valeur résiduelle', compute='_compute_valeur_residuelle')
    taux_amortissement = fields.Float('Taux d\'amortissement (%)', compute='_compute_taux_amortissement')
    date_fin_amortissement = fields.Date('Fin d\'amortissement', compute='_compute_fin_amortissement')

    @api.model
    def _cron_verifier_garanties(self):
        """Vérifier les équipements dont la garantie expire bientôt"""
        date_limite = fields.Date.today() + timedelta(days=30)
        equipements = self.search([
            ('fin_garantie', '>=', fields.Date.today()),
            ('fin_garantie', '<=', date_limite)
        ])
        
        for equip in equipements:
            # Créer une activité pour le responsable
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                'note': f"La garantie de l'équipement {equip.name} expire le {equip.fin_garantie}",
                'res_id': equip.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'parc.equipement')], limit=1).id,
                'user_id': self.env.user.id,
            })
            
            # Envoyer un email au client
            template = self.env.ref('gestion_parc_informatique.email_template_garantie_expiration')
            template.send_mail(equip.id, force_send=True)

    @api.depends('valeur_achat', 'duree_amortissement', 'date_achat')
    def _compute_valeur_residuelle(self):
        for record in self:
            if not record.date_achat or not record.valeur_achat or not record.duree_amortissement:
                record.valeur_residuelle = 0
                continue
                
            # Calculer l'âge en mois de l'équipement
            today = fields.Date.today()
            age_en_mois = (today.year - record.date_achat.year) * 12 + (today.month - record.date_achat.month)
            
            # Si l'âge dépasse la durée d'amortissement, la valeur est nulle
            if age_en_mois >= record.duree_amortissement:
                record.valeur_residuelle = 0
            else:
                # Calcul linéaire: (durée restante / durée totale) * valeur initiale
                record.valeur_residuelle = ((record.duree_amortissement - age_en_mois) / record.duree_amortissement) * record.valeur_achat

    @api.depends('date_achat', 'duree_amortissement')
    def _compute_fin_amortissement(self):
        for record in self:
            if record.date_achat and record.duree_amortissement:
                record.date_fin_amortissement = record.date_achat + relativedelta(months=record.duree_amortissement)
            else:
                record.date_fin_amortissement = False

    @api.depends('valeur_achat', 'valeur_residuelle')
    def _compute_taux_amortissement(self):
        for record in self:
            if record.valeur_achat:
                record.taux_amortissement = (1 - (record.valeur_residuelle / record.valeur_achat)) * 100
            else:
                record.taux_amortissement = 0