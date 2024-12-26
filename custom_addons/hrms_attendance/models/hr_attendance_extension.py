from odoo import api, fields, models

class HrAttendanceExtension(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, vals):
        # Call the super method to create the attendance record
        attendance = super().create(vals)

        # Create the corresponding record in your custom module
        if attendance.employee_id:
            self.env['hrms.attendance'].create({
                'employee_id': attendance.employee_id.id,
                'attendance_id': attendance.id,
                'check_in': attendance.check_in,
                'check_out': attendance.check_out,
            })

        return attendance

    def write(self, vals):
        # Call the super method to update the attendance record
        res = super().write(vals)

        # Update the corresponding record in your custom module
        for attendance in self:
            hrms_record = self.env['hrms.attendance'].search([('attendance_id', '=', attendance.id)], limit=1)
            if hrms_record:
                hrms_record.write({
                    'check_in': attendance.check_in,
                    'check_out': attendance.check_out,
                })

        return res