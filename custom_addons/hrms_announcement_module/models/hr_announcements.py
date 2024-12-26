import logging
import pytz
import threading
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import date_utils, email_split, is_html_empty, groupby
from odoo.tools.misc import get_lang
from random import randint
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class HR_Announcement(models.Model):
    _name = 'hr.announcements'
    _description = 'HR Announcement Module'
    _rec_name = ''
    
    # _inherit = ['hr.employee.masterlist', 'hr.departments','hr.job.positions','mail.thread', 'mail.activity.mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Code No:', help="Sequence of Announcement")
    announcement_reason = fields.Text(string='Title', required=True, help="Announcement subject")
    state = fields.Selection(selection=[('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
                                        ('approved', 'Approved'), ('rejected', 'Refused'),
                                        ('expired', 'Expired')],
        string='Status', default='draft', help="State of announcement.", track_visibility='always')
    requested_date = fields.Date(string='Requested Date', default=fields.Datetime.now(). strftime('%Y-%m-%d'), help="Create date of record")
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4', string="Attachment", help='Attach copy of your document')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, readonly=True, help="Login user Company")
    is_announcement = fields.Boolean(string='Is general Announcement?', help="Enable, if this is a " "General Announcement")
    announcement_type = fields.Selection([('employee', 'By Employee'), ('department', 'By Department'),('job_position', 'By Job Position')], string="Announcement Type",
                        help="By Employee: Announcement intended for specific Employees.\n"
                            "By Department: Announcement intended for Employees in "
                            "specific Departments.\n"
                            "By Job Position: Announcement intended for Employees "
                            "who are having specific Job Positions")
    employee_ids = fields.Many2many('hr.employee.masterlist', 'hr_employee_announcements',
                                    'announcement', 'employee',
                                    string='Employees',
                                    help="Employees who want to see "
                                         "this announcement")
    department_ids = fields.Many2many('hr.departments',
                                      'hr_department_announcements',
                                      'announcement', 'department',
                                      string='Departments',
                                      help="Department which can see "
                                           "this announcement")
    position_ids = fields.Many2many('hr.job.positions', 'hr_job_position_announcements',
                                    'announcement', 'job_position',
                                    string='Job Positions',
                                    help="Position of the employee "
                                         "who is authorized "
                                         "to view this announcements.")
    announcement = fields.Html(string='Letter', help="Announcement message")
    date_start = fields.Date(string='Start Date', default=fields.Date.today(),
                             required=True, help="Start date of announcement")
    date_end = fields.Date(string='End Date', default=fields.Date.today(),
                           required=True, help="End date of announcement")
    
    # user_id = fields.Many2one('res.users', string='Related User', store=True)
    

    @api.constrains('date_start', 'date_end')
    def _check_date_start(self):
        """ Raise validation error when start date is greater than end date """
        if self.date_start > self.date_end:
            raise ValidationError(_("The Start Date must be earlier "
                                    "than the End Date"))

    def create(self, vals):
        """ Create method for HrAnnouncement model, adding sequence
        number to announcements. """
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.announcements.general')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.announcements')
        return super(HR_Announcement, self).create(vals)

    def action_reject_announcement(self):
        """ Refuse button action """
        self.state = 'rejected'

    def action_approve_announcement(self):
        """ Approve button action """
        self.state = 'approved'

    def action_sent_announcement(self):
        """ 'Send For Approval' button action"""
        self.state = 'to_approve'

    def get_expiry_state(self):
        """
        Expire announcements based on their End date, triggered by a
        scheduled cron job.
        """
        announcements = self.search([('state', '!=', 'rejected')])
        for announcement in announcements:
            if announcement.date_end < fields.Date.today():
                announcement.write({
                    'state': 'expired'
                })
    
    def filter_announcements(self):
        current_employee = self.env['hr.employee.masterlist'].search([('user_id', '=', self.env.uid)], limit=1)
        domain = ['|', ('is_announcement', '=', True)]
        if self.env.user.has_group('hrms_announcement_module.group_hrms_announcements_manager'):
            return self.search(domain)  # Managers see all announcements
        if current_employee:
            domain.append(('employee_ids', 'in', [current_employee.id]))
        _logger.info("Computed domain: %s", domain)
        return self.search(domain)
    
    # def filter_announcements(self):
    #     """Filter announcements visible to the current user."""
    #     current_employee = self.env['hr.employee.masterlist'].search([('user_id', '=', self.env.uid)], limit=1)
    #     domain = ['|', ('is_announcement', '=', True)]

    #     if self.env.user.has_group('hrms_announcement_module.group_hrms_announcements_manager'):
    #         return self.search(domain)  # Managers see all announcements

    #     if current_employee:
    #         department_domain = [('department_ids', 'in', [current_employee.department_id.id])]
    #         employee_domain = [('employee_ids', 'in', [current_employee.id])]
    #         domain = expression.OR([domain, department_domain, employee_domain])
    #         _logger.info("Computed domain for employee %s: %s", current_employee.id, domain)
    #     else:
    #         _logger.warning("No employee record linked to the current user.")
        
    #     return self.search(domain)
    
    # def filter_announcements(self):
    #     """Filter announcements visible to the current user."""
    #     current_employee = self.env['hr.employee.masterlist'].search([('user_id', '=', self.env.uid)], limit=1)
    #     _logger.info("Current Employee: %s", current_employee)
        
    #     domain = ['|', ('is_announcement', '=', True)]

    #     if self.env.user.has_group('hrms_announcement_module.group_hrms_announcements_manager'):
    #         _logger.info("User is a manager, returning all announcements.")
    #         return self.search(domain)  # Managers see all announcements

    #     if current_employee:
    #         _logger.info("Employee's Department: %s", current_employee.department_id)
    #         _logger.info("Employee's Department ID: %s", current_employee.department_id.id)

    #         department_domain = [('department_ids', 'in', [current_employee.department_id.id])]
    #         employee_domain = [('employee_ids', 'in', [current_employee.id])]
    #         domain = expression.OR([domain, department_domain, employee_domain])
    #         _logger.info("Computed domain for employee %s: %s", current_employee.id, domain)
    #     else:
    #         _logger.warning("No employee record linked to the current user.")
        
    #     return self.search(domain)
        
    is_manager = fields.Boolean(
        string="Is Manager", compute="_compute_is_manager", store=True
    )

    def _compute_is_manager(self):
        """Compute if the current user is a manager."""
        for record in self:
            record.is_manager = self.env.user.has_group('hrms_announcement_module.group_hrms_announcements_manager')
    