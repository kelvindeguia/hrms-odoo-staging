/** @odoo-module **/

import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ParentComponent extends Component {
    static template = "ParentTemplate";
    setup() {
        this.state = useState({
            employeeName: "Loading...", // Placeholder
            checkedIn: false, // Attendance state
        });

        this.fetchEmployeeData();
    }

    async fetchEmployeeData() {
        try {
            const result = await rpc("/hrms_attendance/attendance_user_data");
            if (result) {
                this.state.employeeName = result.name || "User";
                this.state.checkedIn = result.attendance_state === "checked_in";
            }
        } catch (error) {
            console.error("Failed to fetch employee data:", error);
        }
    }
}

// Register ParentComponent in the systray
registry.category("systray").add("hrms_attendance.systray_parent_component", {
    Component: ParentComponent,
    sequence: 10,
});
