/** @odoo-module **/
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component } = owl;
const cogMenuRegistry = registry.category("cogMenu");

export class CogMenu extends Component {
    setup() {
        this.actionService = useService("action");
    }

    async actionImportPurchaseFromSinli() {
        try {
            this.actionService.doAction("sinli.sinli_import_purchase_order_action");
        } catch (error) {
            console.error("Error al abrir el wizard:", error);
        }
    }
}
CogMenu.template = "sinli_import_purchase_dropdown";
CogMenu.components = { DropdownItem };

export const CogMenuItem = {
    Component: CogMenu,
    groupNumber: 20,
    isDisplayed: ({ searchModel }) => {
        return searchModel.resModel === 'purchase.order';
    },
};

cogMenuRegistry.add("sinli_import_purchase_dropdown", CogMenuItem, { sequence: 10 });