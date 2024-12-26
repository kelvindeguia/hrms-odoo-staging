/** @odoo-module **/

import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class CheckInOut extends Component {
    static template = "hrms_attendance.CheckInOut";
    static props = {
        checkedIn: Boolean,
        employeeName: String, // Display name of the current user
    };

    setup() {
        this.notification = useService("notification");
    }

    async signInOut() {
        try {
            // No need to pass employee ID, as the backend infers it
            const result = await rpc("/hrms_attendance/check_in_out");

            if (result.success) {
                this.notification.add(result.message || "Attendance updated successfully!", { type: "success" });
                this.trigger("reload");
            } else {
                throw new Error(result.error || "Unknown error occurred");
            }
        } catch (error) {
            console.error("Error during signInOut:", error);
            this.notification.add(`Failed to update attendance: ${error.message}`, { type: "danger" });
        }
    }
}

// Register the component in the systray
registry.category("systray").add("hrms_attendance.systray_check_in_out", {
    Component: CheckInOut,
    sequence: 10,
});
