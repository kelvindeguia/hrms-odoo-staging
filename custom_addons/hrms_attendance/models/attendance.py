import uuid
import pytz

from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
from pytz import timezone

from odoo import models, fields, api, exceptions, _
from odoo.addons.resource.models.utils import Intervals
from odoo.tools import format_datetime
from odoo.osv.expression import AND, OR
from odoo.exceptions import AccessError
from odoo.tools import format_duration
from odoo.exceptions import ValidationError

class Attendance(models.Model):
    _name = "hrms.attendance"
    _description = "HRMS - Attendances"
    _order = "check_in desc"
    _inherit = [ 'mail.thread', 'mail.activity.mixin',]

    def _default_employee(self):
        return self.env.user.employee_id
    
    # employee_name_id = fields.Many2one("res.users", string="Employee", required=True, ondelete='cascade', index=True)


    user_id = fields.Many2one('res.users', string='Related User', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=True)
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)


    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.worked_hours = delta.total_seconds() / 3600.0
            else:
                record.worked_hours = 0.0

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    attendance_id = fields.Many2one('hr.attendance', string='Attendance', required=True)
    latitude = fields.Float('Latitude')
    longitude = fields.Float('Longitude')
    # check_in_out = fields.Datetime('Check In/Out Time', required=True)
    # action = fields.Selection([
    #     ('check_in', 'Check In'),
    #     ('check_out', 'Check Out')
    # ], string='Action', required=True)


    user_id = fields.Char('User ID Reference', store=True)
    old_check_in = fields.Datetime("Old Check In", readonly=True, tracking=True, store=True)
    reason_check_in = fields.Char("Updated Check In Remarks")
    old_check_out = fields.Datetime("Old Check Out", readonly=True, tracking=True, store=True)
    reason_check_out = fields.Char("Updated Check Out Remarks")
    updated_by_check_in_id = fields.Many2one('res.users', string='Updated By', store=True)
    updated_by_check_out_id = fields.Many2one('res.users', string='Updated By', store=True)
    # worked_hours = fields.Float(string='Worked Hours', store=True, readonly=True)
    # overtime_hours = fields.Float(string="Over Time", compute='_compute_overtime_hours', store=True)
    overtime_hours = fields.Float(string="Over Time", store=True)
    in_country_name = fields.Char(string="Country", help="Based on IP Address", readonly=True)
    in_city = fields.Char(string="City", readonly=True)
    in_ip_address = fields.Char(string="IP Address", readonly=True)
    in_browser = fields.Char(string="Browser", readonly=True)
    in_mode = fields.Selection(string="Mode",
                               selection=[('kiosk', "Kiosk"),
                                          ('systray', "Systray"),
                                          ('manual', "Manual")],
                               readonly=True,
                               default='manual')
    out_country_name = fields.Char(help="Based on IP Address", readonly=True)
    out_city = fields.Char(readonly=True)
    out_ip_address = fields.Char(readonly=True)
    out_browser = fields.Char(readonly=True)
    out_mode = fields.Selection(selection=[('kiosk', "Kiosk"),
                                           ('systray', "Systray"),
                                           ('manual', "Manual")],
                                readonly=True,
                                default='manual')

    break_time_start = fields.Datetime("Break Time Start")
    break_time_end = fields.Datetime("Break Time End")
    break_time_total = fields.Float("Total Break Time", compute='_compute_time_difference', store=True)

    is_flexible = fields.Boolean(string="Flexible Schedule", default=False)

    unique_url_token = fields.Char('Unique URL Token', default=lambda self: str(uuid.uuid4()), readonly=True)
    unique_url = fields.Char('Unique URL', compute='_compute_unique_url')


    # @api.depends("check_in", "check_out")
    # def _compute_worked_hours(self):
    #     """Compute worked hours based on check_in and check_out"""
    #     for record in self:
    #         if record.check_in and record.check_out:
    #             delta = record.check_out - record.check_in
    #             record.worked_hours = delta.total_seconds() / 3600.0
    #         else:
    #             record.worked_hours = 0.0

    def update_last_position(self, latitude, longitude):
        """Update the last known GPS position of the employee."""
        self.write({
            'last_latitude': latitude,
            'last_longitude': longitude,
        })

    @api.model
    def get_attendance_state(self):
        """Return the current state of the attendance."""
        record = self.search([('create_uid', '=', self.env.uid), ('check_out', '=', False)], limit=1)
        return {
            "is_checked_in": bool(record and record.check_in),
        }

    def action_check_in(self):
        """Mark Check-In."""
        record = self.search([('create_uid', '=', self.env.uid), ('check_out', '=', False)], limit=1)
        if record:
            raise UserError("You are already checked in.")
        self.create({"check_in": fields.Datetime.now()})

    def action_check_out(self):
        """Mark Check-Out."""
        record = self.search([('create_uid', '=', self.env.uid), ('check_out', '=', False)], limit=1)
        if not record:
            raise UserError("You need to check in first.")
        record.write({"check_out": fields.Datetime.now()})


    @api.depends('check_in', 'check_out')
    def _compute_action_label(self):
        """Compute the label for the action button dynamically."""
        for record in self:
            if not record.check_in:
                record.action_label = "Check In"
            elif not record.check_out:
                record.action_label = "Check Out"
            else:
                record.action_label = "Done"

    def action_toggle_check_in_out(self):
        """Perform either Check-In or Check-Out based on current state."""
        for record in self:
            if not record.check_in:
                # Perform Check-In
                record.check_in = fields.Datetime.now()
            elif not record.check_out:
                # Perform Check-Out
                record.check_out = fields.Datetime.now()
            else:
                raise UserError(_("Both Check-In and Check-Out are already recorded."))

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ Verifies that Check-Out time is after Check-In time. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Validates overlapping and open attendance records for the same employee. """
        for attendance in self:
            last_attendance_before_check_in = self.env['hrms.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)

            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise ValidationError(_("Cannot create a new attendance record for %(empl_name)s. The employee was already checked in on %(datetime)s.",
                                        empl_name=attendance.employee_id.name,
                                        datetime=format_datetime(self.env, attendance.check_in, dt_format=False)))

            if not attendance.check_out:
                no_check_out_attendances = self.env['hrms.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], limit=1)
                if no_check_out_attendances:
                    raise ValidationError(_("Cannot create a new attendance record for %(empl_name)s. The employee hasn't checked out since %(datetime)s.",
                                            empl_name=attendance.employee_id.name,
                                            datetime=format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False)))
                
    def get_kiosk_url(self):
        return self.unique_url() + "/hrms_attendance/" + self.env.company
    
    # def get_kiosk_url(self):
    #     return self.unique_url() + "/hrms_attendance/" + self.env.company.attendance_kiosk_key

    # def get_kiosk_url(self):
    #     base_url = self.get_base_url()
    #     kiosk_key = self.env.company.attendance_kiosk_key or ""
    #     if kiosk_key:
    #         return base_url + "/hrms_attendance/" + kiosk_key
    #     else:
    #         return base_url + "/hrms_attendance/default_kiosk_key"
    
    def action_try_kiosk(self):
        if not self.env.user.has_group("hrms_attendance.group_hrms_attendance_admin"):
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _("You don't have the rights to execute that action."),
                        'type': 'info',
                    }
            }
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.env.company.attendance_kiosk_url + '?from_trial_mode=True'
        }
    
    # class HRMSKioskMode(models.Model):
    #     _name = 'hrms.kioskmode'
    #     _description = 'Kiosk Mode'
    #     _rec_name = ''

    def _compute_unique_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.unique_url = f"{base_url}/hrms_attendance/{record.unique_url_token}"