# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HRMS - Attendances",
    "version": "1.0.0",
    "sequence": -100,
    "category": "HRMS Attendance",
    "author": "Joseph Patrick Vargas",
    "website": "",
    "depends": ["base", "mail", "hr", "barcodes", "web"],
    "data": [
        "data/attendance_data.xml",
        "security/attendance_security.xml",
        "security/ir.model.access.csv",
        "views/actions.xml",
        "views/menu.xml",
        "views/views.xml",
        "views/rules.xml",
        "views/hrms_attendance_kiosk_templates.xml",

    ],

    'assets': {
    'web.assets_backend': [
       
        
        
        
        
    ],
    },
    "application": True,
    "installable": True,
}