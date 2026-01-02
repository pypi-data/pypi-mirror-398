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

    async actionImportSaleFromSinli() {
        try {
            this.actionService.doAction("sinli.sinli_import_sale_order_action");
        } catch (error) {
            console.error("Error al abrir el wizard:", error);
        }
    }
}
CogMenu.template = "sinli_import_sale_dropdown";
CogMenu.components = { DropdownItem };

export const CogMenuItem = {
    Component: CogMenu,
    groupNumber: 20,
    isDisplayed: ({ searchModel }) => {
        return searchModel.resModel === 'sale.order';
    },
};

cogMenuRegistry.add("sinli_import_sale_dropdown", CogMenuItem, { sequence: 10 });