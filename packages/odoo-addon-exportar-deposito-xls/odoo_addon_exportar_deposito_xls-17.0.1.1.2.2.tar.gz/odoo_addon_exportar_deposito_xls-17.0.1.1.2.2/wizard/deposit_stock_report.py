# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#    Modify by Team Devcontrol
#
#############################################################################
from collections import defaultdict
from datetime import datetime
import pytz
import json
import datetime
import io
from odoo import fields, models, _
from odoo.tools import date_utils
from odoo.exceptions import ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DepositStockReport(models.TransientModel):
    _name = "deposit.stock.xls.report"
    _description = "Current deposit stock report"

    warehouse = fields.Many2many('stock.warehouse',
                                     string='Warehouse',
                                     required=True)
    owner = fields.Many2one(
        "res.partner", string="Owner", domain="[('is_author','=',False)]"
    )
    deposit = fields.Selection(
        [("ventas", "Deposito de ventas"), ("compras", "Deposito de compras")],
        string="Tipo de Depósito",
        default="ventas",
        required=True,
    )

    def export_summary_xls(self):
        report_name = f"Deposito_general_de_{self.deposit}"
        data = {
            "ids": self.ids,
            "model": self._name,
            "warehouse": self.warehouse.ids,
            "deposit_type": self.deposit,
        }
        return {
            'type': 'ir.actions.report',
            "data": {
                "model": "deposit.stock.xls.report",
                "options": json.dumps(data, default=date_utils.json_default),
                "output_format": "xlsx",
                "report_name": report_name,
                "summary": True,
            },
            'report_type': 'deposit_stock_xlsx'
        }

    def export_xls(self):
        if not self.owner:
            raise ValidationError(
                "Para exportar un deposito individual hay que seleccionar un contacto."
            )

        obj = self.env["res.partner"].browse(self.owner.ids[0])
        report_name = f"Deposito_de_{self.deposit}_de_{obj.name}"
        data = {
            "ids": self.ids,
            "model": self._name,
            "warehouse": self.warehouse.ids,
            "owner": self.owner.ids,
            "deposit_type": self.deposit,
        }
        return {
            'type': 'ir.actions.report',
            "data": {
                "model": "deposit.stock.xls.report",
                "options": json.dumps(data, default=date_utils.json_default),
                "output_format": "xlsx",
                "report_name": report_name,
                "resumen": False,
            },
            'report_type': 'deposit_stock_xlsx',
        }

    def get_warehouse(self, data):
        wh = data.warehouse.mapped("id")
        obj = self.env["stock.warehouse"].search([("id", "in", wh)])
        l1 = []
        l2 = []
        for j in obj:
            l1.append(j.name)
            l2.append(j.id)
        return l1, l2

    def get_owner(self, data):
        ow = data.owner.mapped("id")
        obj = self.env["res.partner"].search([("id", "in", ow)])
        l1 = []
        l2 = []
        for j in obj:
            l1.append(j.name)
            l2.append(j.id)
        return l1, l2

    def get_quants_sales_deposit(self, partner_id):
        domain = [
            ("owner_id", "=", partner_id),
            ("location_id", "=", self.env.company.location_venta_deposito_id.id),
            ("quantity", ">", 0), 
        ]
        deposit_quants = self.env["stock.quant"].search(domain)
        print(deposit_quants)
        return deposit_quants

    def get_lines_deposito_compras(self, partner_id):
        domain = [
            ("partner_id", "=", partner_id),
            ("state", "in", ["done", "purchase"]),
            ("is_liquidated", "=", False),
            (
                "order_id.picking_type_id",
                "=",
                self.env.company.stock_picking_type_compra_deposito_id.id,
            ),
        ]
        deposito_lines = self.env["purchase.order.line"].search(domain)
        return deposito_lines

    def get_lines(self, partner_id, deposit_type):
        partner = self.env["res.partner"].browse(partner_id)

        if deposit_type == "ventas":
            report_lines = partner.get_sales_deposit_lines()
        elif deposit_type == "compras":
            deposit_lines = partner.get_purchases_deposit_lines()
            report_lines = {}
            for move_line in deposit_lines:
                key = move_line.product_id.id
                report_lines.setdefault(key, 0)
                report_lines[key] += (
                    move_line.qty_received - move_line.liquidated_qty
                )

        lines = []
        # falataria filtrar las línas por la categoría (en caso de que nos interese)
        # añadir aquí los campos isbn, name, category, deposito
        for key_prod_id, qty_in_deposit in report_lines.items():
            product = self.env["product.product"].browse(key_prod_id)
            vals = {
                "isbn": product.isbn_number,
                "name": product.name,
                "category": product.categ_id.name,
                "cost_price": product.list_price,
                "deposito": qty_in_deposit,
            }

            if deposit_type == "compras":
                products_sold = product.get_liquidated_sales_qty()
                products_purchased_and_liquidated = (
                    product.get_liquidated_purchases_qty()
                )
                vendidos_sin_liquidar = max(
                    0, products_sold - products_purchased_and_liquidated
                )
                vendidos_sin_liquidar = min(
                    vendidos_sin_liquidar, qty_in_deposit
                )
                vals["vendidos_sin_liquidar"] = vendidos_sin_liquidar

            lines.append(vals)
        return lines

    def get_date_last_liq(self, partner_id, deposit_type):
        liq_type = "SALE_LIQ" if deposit_type == "ventas" else "PURCHASE_LIQ"
        state = ["sale","done"] if deposit_type == "ventas" else ["purchase","done"]
        domain = [
            ("partner_id", "=", partner_id),
            ("order_type", "=", liq_type),
            ("state", "in", state),
        ]

        if liq_type == "SALE_LIQ":
            last_liq = self.env["sale.order"].search(
                domain, order="create_date desc", limit=1
            )
            return last_liq.date_order if last_liq.date_order else "Sin fecha conocida"
        else:   # PURCHASE_LIQ
            last_liq = self.env["purchase.order"].search(
                domain, order="date_approve desc", limit=1
            )
            return last_liq.date_approve if last_liq.date_approve else "Sin fecha conocida"


    def get_xlsx_resumen_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        lines = self.browse(data["ids"])
        deposit_type = data["deposit_type"]
        get_warehouse = self.get_warehouse(lines)
        comp = self.env.user.company_id.name
        sheet = workbook.add_worksheet("Resumen depósitos")
        format0 = workbook.add_format(
            {"font_size": 20, "align": "center", "bold": True}
        )
        format1 = workbook.add_format(
            {"font_size": 14, "align": "vcenter", "bold": True}
        )
        format11 = workbook.add_format(
            {"font_size": 12, "align": "center", "bold": True}
        )
        format21 = workbook.add_format(
            {"font_size": 10, "align": "center", "bold": True}
        )
        format3 = workbook.add_format({"bottom": True, "top": True, "font_size": 12})
        format4 = workbook.add_format({"font_size": 12, "align": "left", "bold": True})
        font_size_8 = workbook.add_format({"font_size": 8, "align": "center"})
        font_size_8_l = workbook.add_format({"font_size": 8, "align": "left"})
        red_mark = workbook.add_format({"font_size": 8, "bg_color": "red"})
        justify = workbook.add_format({"font_size": 12})
        format3.set_align("center")
        justify.set_align("justify")
        format1.set_align("center")
        red_mark.set_align("center")
        sheet.merge_range(
            "A1:G2", f"Informe resumen de depósitos {deposit_type}", format0
        )
        sheet.merge_range("A3:G3", comp, format11)
        w_house = ", "
        sheet.write(4, 0, "Warehouses : ", format4)
        w_house = w_house.join(get_warehouse[0])
        sheet.write("B5", w_house, format4)
        user = self.env["res.users"].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else "UTC")
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        sheet.merge_range(
            "A7:D7",
            "Fecha de informe: " + str(times.strftime("%Y-%m-%d %H:%M %p")),
            format1,
        )
        sheet.merge_range("A9:G9", "Información de clientes", format11)
        sheet.write(9, 0, "Nombre", format21)
        sheet.write(9, 1, "Valor en depósito PVP (€)", format21)
        sheet.write(9, 2, "Fecha uĺtima liquidación de depósito", format21)
        if deposit_type == "compras":
            sheet.write(9, 3, "PVP Total vendidos sin liquidar (€)", format21)
            sheet.set_column("D:D", 30)

        prod_row = 10
        prod_col = 0
        sheet.set_column("A:A", 60)
        sheet.set_column("B:B", 25)
        sheet.set_column("C:C", 30)

        clientes = self.env["res.partner"].search([])
        for cliente in clientes:
            fecha_liq = self.get_date_last_liq(cliente.id, deposit_type)
            get_line = self.get_lines(cliente.id, deposit_type)
            valor_deposito = sum(x["deposito"] * x["cost_price"] for x in get_line)
            client_full_name = cliente.name
            sheet.write(prod_row, prod_col, client_full_name, font_size_8)
            sheet.write(prod_row, prod_col + 1, valor_deposito, font_size_8_l)
            sheet.write(prod_row, prod_col + 2, str(fecha_liq), font_size_8)
            if deposit_type == "compras":
                pendiente_liq = sum(
                    x["vendidos_sin_liquidar"] * x["cost_price"] for x in get_line
                )
                sheet.write(prod_row, prod_col + 3, str((pendiente_liq)), font_size_8)
            prod_row = prod_row + 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        lines = self.browse(data["ids"])
        # get_warehouse = self.get_warehouse(lines)
        deposit_type = data["deposit_type"]
        get_owner = self.get_owner(lines)
        comp = self.env.user.company_id.name
        fecha_liq = self.get_date_last_liq(get_owner[1][0], deposit_type)
        sheet = workbook.add_worksheet(f"{get_owner[0][0][:31]}")
        format0 = workbook.add_format(
            {"font_size": 20, "align": "center", "bold": True}
        )
        format1 = workbook.add_format(
            {"font_size": 14, "align": "vcenter", "bold": True}
        )
        format11 = workbook.add_format(
            {"font_size": 12, "align": "center", "bold": True}
        )
        format21 = workbook.add_format(
            {"font_size": 10, "align": "center", "bold": True}
        )
        format3 = workbook.add_format({"bottom": True, "top": True, "font_size": 12})
        format4 = workbook.add_format({"font_size": 12, "align": "left", "bold": True})
        font_size_8 = workbook.add_format({"font_size": 8, "align": "center"})
        font_size_8_l = workbook.add_format({"font_size": 8, "align": "left"})
        font_size_8_r = workbook.add_format({"font_size": 8, "align": "right"})
        red_mark = workbook.add_format({"font_size": 8, "bg_color": "red"})
        justify = workbook.add_format({"font_size": 12})
        format3.set_align("center")
        justify.set_align("justify")
        format1.set_align("center")
        red_mark.set_align("center")
        sheet.merge_range("A1:G2", f"Informe de depósito de {deposit_type}", format0)
        sheet.merge_range("A3:G3", comp, format11)
        w_house = ", "
        sheet.write(4, 0, "Depósito : ", format4)
        w_house = w_house.join(get_owner[0])
        sheet.write("B5", w_house, format4)
        user = self.env["res.users"].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else "UTC")
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        sheet.merge_range(
            "A7:D7",
            "Fecha de informe: " + str(times.strftime("%Y-%m-%d %H:%M %p")),
            format1,
        )
        sheet.merge_range("F7:K7", f"Fecha última liq.: {fecha_liq}", format1)
        sheet.merge_range("A9:G9", "Información de producto", format11)
        sheet.write(9, 0, "ISBN", format21)
        sheet.write(9, 1, "Nombre", format21)
        sheet.write(9, 2, "Categoria", format21)
        sheet.write(9, 3, "Precio PVP", format21)
        sheet.write(9, 4, "Deposito", format21)
        if deposit_type == "compras":
            sheet.write(9, 5, "Vendidos sin liquidar", format21)
            sheet.set_column("F:F", 20)

        prod_row = 10
        prod_col = 0
        sheet.set_column("A:A", 20)
        sheet.set_column("B:B", 50)
        sheet.set_column("D:D", 10)
        get_line = self.get_lines(get_owner[1][0], deposit_type)
        for line in get_line:
            sheet.write(prod_row, prod_col, line["isbn"], font_size_8)
            sheet.write(prod_row, prod_col + 1, line["name"], font_size_8_l)
            sheet.write(prod_row, prod_col + 2, line["category"], font_size_8)
            sheet.write(prod_row, prod_col + 3, line["cost_price"], font_size_8_r)
            if line["deposito"] < 0:
                sheet.write(prod_row, prod_col + 4, line["deposito"], red_mark)
            else:
                sheet.write(prod_row, prod_col + 4, line["deposito"], font_size_8)
            if deposit_type == "compras":
                sheet.write(
                    prod_row, prod_col + 5, line["vendidos_sin_liquidar"], font_size_8
                )
            prod_row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
