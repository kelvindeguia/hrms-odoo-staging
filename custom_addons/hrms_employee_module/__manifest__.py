# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HRMS Employee Odoo 18",
    "summary": """HRMS Employee Module Odoo 18""",
    "version": "1.0.1",
    "sequence": -100,
    # "license": "AGPL-3",
    "category": "Productivity",
    "author": "Marc Roda",
    "website": "",
    "depends": ["base", "mail", "utm", "website", 'hr'],
    # 'qweb': [
    #     'static/src/hris_style.scss',
    # ],
    "data": [
        "data/hrms_employee_groups.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/rule.xml",
        "views/actions.xml",
        "views/menus.xml",
        "views/kanban_views.xml",
        "views/list_views.xml",
        "views/search_filters.xml",
        "views/form_views.xml",
        "views/hierarchy_views.xml",
        "views/pivot_views.xml",
        "views/graph_views.xml",
    ],
    # "assets": {
    #     'web.assets_backend': [
    #         'hrms_employee_module/static/src/description/icon.png',  # Ensure static assets are correctly included
    #     ],
    # },
    "application": True,
    "auto_install": False,
    "installable": True,
}
