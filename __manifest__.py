{
    'name': "Gestion Parc Informatique Pro",
    'summary': "Module de gestion de parc informatique pour techniciens",
    'description': """
        Module permettant de gérer:
        - Le parc informatique des clients
        - Les contrats de maintenance et services
        - La facturation périodique
        - L'historique des interventions
    """,
    'author': "Your Company Name",
    'website': "https://www.yourcompany.com",
    'category': 'Services/IT Management',
    'version': '1.0.1',
    'depends': [
        'base',
        'helpdesk',
        'sale',
        'account',
        'hr',
        'board',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/cron.xml',
        'data/mail_templates.xml',
        'views/menu.xml',
        'views/client_views.xml',  
        'views/equipement_views.xml',
        'views/contrat_views.xml',
        'views/helpdesk_ticket_views.xml',  
        'views/maintenance_views.xml',
        'views/helpdesk_views.xml',
        'views/employee_views.xml',
        'views/hr_department_views.xml',
        'views/hr_poste_technique_views.xml', 
        'views/technicien_views.xml',        
        'views/dashboard.xml',
        'reports/contrat_report.xml',
        'views/logiciel_views.xml',
        'views/licence_views.xml',
        'views/site_client_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
}