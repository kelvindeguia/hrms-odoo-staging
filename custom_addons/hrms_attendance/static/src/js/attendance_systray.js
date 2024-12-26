/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useDebounced } from "@web/core/utils/timing";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AttendanceSystray extends owl.Component {
    constructor() {
        super(...arguments);
        this.orm = useService("orm");
        this.notification = useService("notification");
        this._updateState();
    }

    async _updateState() {
        const result = await this.orm.call("hrms.attendance", "get_attendance_state", []);
        this.state = result || {};
        this.render();
    }

    async _onCheckIn() {
        await this.orm.call("hrms.attendance", "action_check_in", []);
        this.notification.add("Checked In Successfully", { type: "success" });
        await this._updateState();
    }

    async _onCheckOut() {
        await this.orm.call("hrms.attendance", "action_check_out", []);
        this.notification.add("Checked Out Successfully", { type: "success" });
        await this._updateState();
    }
}

// Ensure the template name matches the XML `t-name` attribute
AttendanceSystray.template = "AttendanceSystrayTemplate";

// Register the systray item
registry.category("systray").add("attendance_systray", {
    Component: AttendanceSystray,
    sequence: 10,
});