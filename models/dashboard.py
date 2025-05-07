from odoo import models, fields, api
from datetime import timedelta

class MaintenanceDashboard(models.Model):
    _name = 'parc.dashboard'
    _description = 'Tableau de bord analytique'
    
    name = fields.Char('Nom', default='Tableau de bord')
    date_debut = fields.Date('Date début', default=lambda self: fields.Date.today() - timedelta(days=30))
    date_fin = fields.Date('Date fin', default=fields.Date.today)
    
    nb_equipements = fields.Integer('Nombre d\'équipements', compute='_compute_statistiques')
    nb_maintenances = fields.Integer('Nombre de maintenances', compute='_compute_statistiques')
    temps_moyen_resolution = fields.Float('Temps moyen de résolution (h)', compute='_compute_statistiques')
    cout_total_maintenance = fields.Float('Coût total maintenance', compute='_compute_statistiques')
    revenu_contrats = fields.Float('Revenus contrats', compute='_compute_statistiques')
    taux_pannes_recurrentes = fields.Float('Taux de pannes récurrentes %', compute='_compute_statistiques')
    
    @api.depends('date_debut', 'date_fin')
    def _compute_statistiques(self):
        for record in self:
            # Calcul des statistiques sur la période
            maintenances = self.env['parc.maintenance'].search([
                ('date_intervention', '>=', record.date_debut),
                ('date_intervention', '<=', record.date_fin)
            ])
            
            # Équipements avec maintenances sur la période
            equipements_ids = maintenances.mapped('equipement_id').ids
            
            # Calcul du nombre d'équipements et de maintenances
            record.nb_equipements = len(equipements_ids)
            record.nb_maintenances = len(maintenances)
            
            # Temps moyen de résolution
            temps_total = sum(maintenances.mapped('temps_passe'))
            record.temps_moyen_resolution = temps_total / len(maintenances) if maintenances else 0
            
            # Calcul des revenus de contrats sur la période
            factures = self.env['account.move'].search([
                ('invoice_date', '>=', record.date_debut),
                ('invoice_date', '<=', record.date_fin),
                ('ref', 'ilike', 'Contrat'),
                ('state', 'in', ['posted', 'paid'])
            ])
            record.revenu_contrats = sum(factures.mapped('amount_total'))
            
            # Calcul du taux de pannes récurrentes (>1 maintenance pour un équipement)
            equipements_count = {}
            for m in maintenances:
                equipements_count[m.equipement_id.id] = equipements_count.get(m.equipement_id.id, 0) + 1
            
            equipements_recurrents = [id for id, count in equipements_count.items() if count > 1]
            record.taux_pannes_recurrentes = (len(equipements_recurrents) / record.nb_equipements * 100) if record.nb_equipements else 0