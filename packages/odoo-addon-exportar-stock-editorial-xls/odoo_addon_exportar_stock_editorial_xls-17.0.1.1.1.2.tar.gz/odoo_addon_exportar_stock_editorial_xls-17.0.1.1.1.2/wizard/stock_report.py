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
#############################################################################
from datetime import datetime
import pytz
import json
import datetime
import io
from odoo import fields, models, _
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class StockReport(models.TransientModel):
    _name = "stock.xls.report"
    _description = "Current Stock History"

    warehouse_id = fields.Many2one('stock.warehouse',
                                     string='Warehouse',
                                     required=True)
    category_ids = fields.Many2many('product.category',
                                    string='Category')
    
    # Return dict with product IDs and their quantities for a given location
    # So we make only one query per location
    def get_products_quantities_for_location(self, product_ids, location):
        location_ids = location.get_all_child_locations()
        domain = [
            ('product_id', 'in', product_ids),
            ('location_id', 'in', location_ids),
        ]

        grouped = self.env['stock.quant'].read_group(
            domain,
            ['product_id', 'quantity:sum'],
            ['product_id']
        )

        result = {}
        for group in grouped:
            if group.get('product_id'):
                pid = group['product_id'][0]
                qty = group['quantity']
                result[pid] = qty
        return result

    def export_xls(self):
        data = {
            "ids": self.ids,
            "model": self._name,
            "warehouse": self.warehouse_id.id,
            "category": self.category_ids.ids,
        }
        return {
            'type': 'ir.actions.report',
            "data": {
                "model": "stock.xls.report",
                "options": json.dumps(data, default=date_utils.json_default),
                "output_format": "xlsx",
                "report_name": "Current Stock History",
            },
            'report_type': 'stock_xlsx'
        }

    def get_warehouse(self, data):
        wh_id = data.warehouse_id.id
        warehouse = self.env["stock.warehouse"].search([("id", "=", wh_id)])
        return [warehouse.name], [warehouse.id]

    def get_lines(self, data):
        scrap_locations = self.env["stock.location"].search([("scrap_location", "=", True)])
        lines = []
        categ_id = data.mapped("id")
        if categ_id:
            products = self.env["product.product"].search(
                [("categ_id", "in", categ_id)]
            )
        else:
            products = self.env["product.product"].search([])

        product_ids = products.ids

        # Get map of product quantities for each location
        stock_qty_map = self.get_products_quantities_for_location(product_ids, self.env.ref("stock.stock_location_stock"))
        distribution_qty_map = self.get_products_quantities_for_location(product_ids, self.env.company.location_venta_deposito_id)
        promotion_qty_map = self.get_products_quantities_for_location(product_ids, self.env.company.location_promotion_id)
        authors_qty_map = self.get_products_quantities_for_location(product_ids, self.env.ref("gestion_editorial.stock_location_authors"))
        scrap_qty_maps = [
            self.get_products_quantities_for_location(product_ids, scrap_loc)
            for scrap_loc in scrap_locations
        ]

        for product in products:
            product_id = product.id
            authors = ', '.join([authorship.author_id.name for authorship in product.authorship_ids]) if product.authorship_ids else ''
            liquidated_sales_qty = product.get_liquidated_sales_qty()
            liquidated_purchases_qty = product.get_liquidated_purchases_qty()
            received_qty = product.get_received_qty()
            purchase_deposit_qty = received_qty - liquidated_purchases_qty

            # Calcula el total de productos "En almacén" (= on hand)
            on_hand_qty = stock_qty_map.get(product_id, 0.0)

            # Calcula el total de productos "En distribución - En librerias"
            in_distribution_qty = distribution_qty_map.get(product_id, 0.0)

            # Suma de libros en Partner Location/Autores e hijas 
            # + Libros vendidos con tarifa "Venta a Autoras"
            books_delivered_authorship = authors_qty_map.get(product_id, 0.0) + product.get_sales_to_author_qty()

            books_for_promotion = promotion_qty_map.get(product_id, 0.0)
            destroyed = sum(scrap_map.get(product_id, 0.0) for scrap_map in scrap_qty_maps)

            vals = {
                "sku": product.default_code,
                "name": product.name,
                "authors": authors,
                "category": product.categ_id.name,
                "list_price": product.list_price,
                "owned": on_hand_qty + in_distribution_qty,
                "available": on_hand_qty,
                "in_distribution": in_distribution_qty,
                "purchase_deposit_qty": purchase_deposit_qty,
                "received_qty": received_qty,
                "liquidated_purchases_qty": liquidated_purchases_qty,
                "liquidated_sales_qty": liquidated_sales_qty,
                "books_delivered_authorship": books_delivered_authorship,
                "books_for_promotion": books_for_promotion,
                "destroyed": destroyed,
            }
            lines.append(vals)
        return lines

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        lines = self.browse(data["ids"])
        d = lines.category_ids
        get_warehouse = self.get_warehouse(lines)
        comp = self.env.user.company_id.name
        sheet = workbook.add_worksheet("Stock Editorial")
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
        sheet.merge_range(1, 7, 2, 10, "Stock Editorial", format0)
        sheet.merge_range(3, 7, 3, 10, comp, format11)
        w_house = ", "
        cat = ", "
        category_names = d.mapped("name")
        if category_names:
            cat = ", ".join(category_names)
            sheet.merge_range(4, 0, 4, 1, "Categorías : ", format4)
            sheet.merge_range(4, 2, 4, 3 + len(category_names), cat, format4)
        sheet.merge_range(5, 0, 5, 1, "Almacén : ", format4)
        w_house = w_house.join(get_warehouse[0])
        sheet.merge_range(5, 2, 5, 3 + len(get_warehouse[0]), w_house, format4)
        user = self.env["res.users"].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else "UTC")
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        sheet.merge_range(
            "A8:G8", "Fecha: " + str(times.strftime("%Y-%m-%d %H:%M %p")), format1
        )
        sheet.merge_range("A9:E9", "Información de producto", format11)
        w_col_no = 4
        w_col_no1 = 5
        for i in get_warehouse[0]:
            w_col_no = w_col_no + 10
            sheet.merge_range(8, w_col_no1, 8, w_col_no, i, format11)
            w_col_no1 = w_col_no1 + 10
        sheet.write(9, 0, "SKU", format21)
        sheet.write(9, 1, "Nombre", format21)
        sheet.write(9, 2, "Autores", format21)
        sheet.write(9, 3, "Categoría", format21)
        sheet.write(9, 4, "PVP", format21)
        sheet.set_column("B:B", 35)
        sheet.set_column("C:C", 23)
        sheet.set_column("E:K", 17)
        sheet.set_column("L:L", 22)
        sheet.set_column("M:M", 21)
        sheet.set_column("N:N", 17)

        p_col_no1 = 5

        for i in get_warehouse[0]:
            sheet.write(9, p_col_no1, "Existencias totales", format21)
            sheet.write(9, p_col_no1 + 1, "En almacén", format21)
            sheet.write(9, p_col_no1 + 2, "En distribución", format21)
            sheet.write(9, p_col_no1 + 3, "Depósito de compra", format21)
            sheet.write(9, p_col_no1 + 4, "Recibidos", format21)
            sheet.write(9, p_col_no1 + 5, "Compras liquidadas", format21)
            sheet.write(9, p_col_no1 + 6, "Ventas liquidadas", format21)
            sheet.write(9, p_col_no1 + 7, "Entregados a autoría", format21)
            sheet.write(9, p_col_no1 + 8, "Promoción", format21)
            sheet.write(9, p_col_no1 + 9, "Destruidos", format21)
            p_col_no1 = p_col_no1 + 10
        prod_row = 10
        prod_col = 0

        lines = self.get_lines(d)

        for line in lines:
            sheet.write(prod_row, prod_col, line["sku"], font_size_8)
            sheet.write(prod_row, prod_col + 1, line["name"], font_size_8_l)
            sheet.write(prod_row, prod_col + 2, line["authors"], font_size_8_l) 
            sheet.write(prod_row, prod_col + 3, line["category"], font_size_8_l)
            sheet.write(prod_row, prod_col + 4, line["list_price"], font_size_8)
            prod_row = prod_row + 1

        prod_row = 10
        prod_col = 5
        for line in lines:
            cell_format = red_mark if line["owned"] < 0 else font_size_8
            sheet.write(prod_row, prod_col, line["owned"], cell_format)

            cell_format = red_mark if line["available"] < 0 else font_size_8
            sheet.write(prod_row, prod_col + 1, line["available"], cell_format)

            cell_format = red_mark if line["in_distribution"] < 0 else font_size_8
            sheet.write(
                prod_row, prod_col + 2, line["in_distribution"], cell_format
            )

            cell_format = (
                red_mark if line["purchase_deposit_qty"] < 0 else font_size_8
            )
            sheet.write(
                prod_row, prod_col + 3, line["purchase_deposit_qty"], cell_format
            )

            cell_format = red_mark if line["received_qty"] < 0 else font_size_8
            sheet.write(prod_row, prod_col + 4, line["received_qty"], cell_format)

            cell_format = (
                red_mark if line["liquidated_purchases_qty"] < 0 else font_size_8
            )
            sheet.write(
                prod_row,
                prod_col + 5,
                line["liquidated_purchases_qty"],
                cell_format,
            )

            cell_format = (
                red_mark if line["liquidated_sales_qty"] < 0 else font_size_8
            )
            sheet.write(
                prod_row, prod_col + 6, line["liquidated_sales_qty"], cell_format
            )

            sheet.write(prod_row, prod_col + 7, line["books_delivered_authorship"], font_size_8)
            sheet.write(prod_row, prod_col + 8, line["books_for_promotion"], font_size_8)
            sheet.write(prod_row, prod_col + 9, line["destroyed"], font_size_8)

            prod_row = prod_row + 1

        prod_row = 10
        prod_col = prod_col + 14
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
