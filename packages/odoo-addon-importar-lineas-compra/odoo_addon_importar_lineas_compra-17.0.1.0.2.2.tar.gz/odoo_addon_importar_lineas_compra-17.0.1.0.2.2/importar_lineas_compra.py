# Copyright 2022 - Komun.org Álex Berbel
# 2025 - Colectivo Devcontrol
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models, _
import binascii
import tempfile
import xlrd
from tempfile import TemporaryFile
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import io

try:
	import xlrd
except ImportError:
	_logger.debug('Cannot `import xlrd`.')
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')
		
class order_line_wizard(models.TransientModel):

	_name='purchase.order.line.wizard'
	_description = "Purchase Order Line Wizard"

	purchase_order_file=fields.Binary(string="Select File")
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
	import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='barcode')
	product_details_option = fields.Selection([('from_product','Take Details From The Product'),('from_xls','Take Details From The XLS File'),('from_pricelist','Take Details With Adapted Pricelist')],default='from_product')

	sample_option = fields.Selection([('csv', 'CSV'),('xls', 'XLS')],string='Tipo de ejemplo',default='csv')
	down_samp_file = fields.Boolean(string='Descarga ficheros de prueba')

	def import_sol(self):
		res = False
		action = False
		missing_taxes_acc = set()
		if self.import_option == 'csv':
			keys = ['product', 'quantity', 'uom','description', 'price', 'tax']
			try:
				csv_data = base64.b64decode(self.purchase_order_file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)

			except Exception:
				raise UserError(_("Please select any file or You have selected invalid file"))

			values = {}
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						if self.product_details_option == 'from_product':
							values.update({
											'product' : field[0],
											'quantity' : field[1]
										})
						elif self.product_details_option == 'from_xls':
							values.update({'product':field[0],
										   'quantity':field[1],
										   'uom':field[2],
										   'description':field[3],
										   'price':field[4],
										   'tax':field[5]
										   })
						else:
							values.update({
											'product' : field[0],
											'quantity' : field[1],
										})  
					res = self.create_order_line(values, missing_taxes_acc)
		else:
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.purchase_order_file))
				fp.seek(0)
				values = {}
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)
			except Exception:
				raise UserError(_("Please select any file or You have selected invalid file"))

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					if self.product_details_option == 'from_product':
						values.update({
										'product' : line[0].split('.')[0],
										'quantity' : line[1],
										'description': line[3]
									})
					elif self.product_details_option == 'from_xls':
						values.update({'product':line[0].split('.')[0],
									   'quantity':line[1],
									   'uom':line[2],
									   'description':line[3],
									   'price':line[4],
									   'tax':line[5]
									   })
					else:
						values.update({
										'product' : line[0].split('.')[0],
										'quantity' : line[1],
									})  
					res = self.create_order_line(values, missing_taxes_acc)
		# Build a combined confirmation message for issues detected across all lines
		provider_mismatches = self.check_providers()
		if missing_taxes_acc or provider_mismatches:
			sections = []
			if missing_taxes_acc:
				items = sorted(n for n in missing_taxes_acc if n)
				items_html = "<ul>" + "".join([f"<li>{n}</li>" for n in items]) + "</ul>"
				sections.append(_("<h3>Impuestos no encontrados</h3><p>Se importarán las líneas ignorando estos impuestos:</p>%s") % items_html)
			if provider_mismatches:
				plist_html = "<ul>" + "".join([f"<li>{p}</li>" for p in provider_mismatches]) + "</ul>"
				sections.append(_("<h3>Productos sin proveedor configurado</h3><p>Estos productos no tienen configurado el proveedor del pedido. ¿Quieres continuar? Si continúas, se añadirá este proveedor a sus fichas:</p>%s") % plist_html)
			message = "".join(sections)
			wizard = self.env['purchase.order.import.confirm.wizard'].create({'message': message})
			return {
				'type': 'ir.actions.act_window',
				'res_model': 'purchase.order.import.confirm.wizard',
				'view_mode': 'form',
				'view_id': self.env.ref('importar_lineas_compra.confirm_message_wizard_view').id,
				'target': 'new',
				'res_id': wizard.id,
			}
		return res

	def check_providers(self):
		purchase_order_brw = self.env['purchase.order'].browse(self._context.get('active_id'))
		if not purchase_order_brw:
			return []
		matched_products = []
		partner = purchase_order_brw.partner_id
		for line in purchase_order_brw.order_line:
			product = line.product_id
			if not product:
				continue
			product_tmpl = product.product_tmpl_id
			if not product_tmpl:
				continue
			
			partner_in_sellers = False
			for seller in product_tmpl.seller_ids:
				if seller.partner_id and seller.partner_id == partner:
					partner_in_sellers = True
					break
			if not partner_in_sellers:
				matched_products.append(product.display_name or product.name)
		return matched_products

	def create_order_line(self,values, missing_taxes_acc):
		purchase_order_brw = self.env['purchase.order'].browse(self._context.get('active_id'))
		_logger.warning(f"Values: {values}")
		product_title=values.get('product')
		if self.product_details_option == 'from_product':
			if self.import_prod_option == 'barcode':
				product_obj_search=self.env['product.product'].search([('barcode',  '=',values['product'])])
			elif self.import_prod_option == 'code':
				product_obj_search=self.env['product.product'].search([('default_code', '=',values['product'])])
			else:
				product_obj_search=self.env['product.product'].search([('name', '=',values['description'])])
				product_title=values.get('description')
	
			if not product_obj_search:
				raise UserError(_('%s product is not found.') % product_title)
			if len(product_obj_search) > 1:
				raise UserError(_('More than one product found for "%s". Please use a unique identifier (barcode or code).') % product_title)
			product_id = product_obj_search[:1]

			if purchase_order_brw.state == 'draft':
				order_lines=self.env['purchase.order.line'].create({
												'order_id':purchase_order_brw.id,
												'product_id':product_id.id,
												'name':product_id.name,
												'product_uom_qty':values.get('quantity'),
												'product_qty':values.get('quantity'),
												'product_uom':product_id.uom_id.id,
												'price_unit':product_id.lst_price,
												'date_planned':purchase_order_brw.date_order,
												'taxes_id':product_id.supplier_taxes_id,
												})

			elif purchase_order_brw.state == 'sent':
				order_lines=self.env['purchase.order.line'].create({
												'order_id':purchase_order_brw.id,
												'product_id':product_id.id,
												'name':product_id.name,
												'product_uom_qty':values.get('quantity'),
												'product_qty':values.get('quantity'),
												'product_uom':product_id.uom_id.id,
												'price_unit':product_id.lst_price,
												'date_planned':purchase_order_brw.date_order,
												'taxes_id':product_id.supplier_taxes_id,
												})
			elif purchase_order_brw.state != 'sent' or purchase_order_brw.state != 'draft':
				raise UserError(_('We cannot import data in validated or confirmed order.'))
		elif self.product_details_option == 'from_xls':
			uom=values.get('uom')
			if self.import_prod_option == 'barcode':
				product_obj_search=self.env['product.product'].search([('barcode',  '=',values['product'])])
			elif self.import_prod_option == 'code':
				product_obj_search=self.env['product.product'].search([('default_code', '=',values['product'])])
			else:
				product_obj_search=self.env['product.product'].search([('name', '=',values['description'])])
				product_title=values.get('description')
				
			uom_obj_search=self.env['uom.uom'].search([('name','=',uom)])
			tax_id_lst=[]
			if values.get('tax'):
				if ';' in  values.get('tax'):
					tax_names = values.get('tax').split(';')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', 'in', name),('type_tax_use','=','purchase')])
						if not tax:
							missing_taxes_acc.add(name.strip())
						else:
							tax_id_lst.append(tax.id)

				elif ',' in  values.get('tax'):
					tax_names = values.get('tax').split(',')
					for name in tax_names:
						tax= self.env['account.tax'].search([('name', 'in', name),('type_tax_use','=','purchase')])
						if not tax:
							missing_taxes_acc.add(name.strip())
						else:
							tax_id_lst.append(tax.id)
				else:
					tax_names = values.get('tax').split(',')
					tax= self.env['account.tax'].search([('name', 'in', tax_names),('type_tax_use','=','purchase')])
					if not tax:
						for name in tax_names:
							missing_taxes_acc.add(name.strip())
					else:
						tax_id_lst.append(tax.id)
			
			if not uom_obj_search:
				raise UserError(_('UOM "%s" is Not Available') % uom)

			if product_obj_search:
				if len(product_obj_search) > 1:
					raise Warning(_('More than one product found for "%s". Please use a unique identifier (barcode or code).') % product_title)
				product_id = product_obj_search[:1]

			else:
				raise UserError(_('%s product is not found.') % product_title)

			if purchase_order_brw.state == 'draft':
				order_lines=self.env['purchase.order.line'].create({
													'order_id':purchase_order_brw.id,
													'product_id':product_id.id,
													'name':values.get('description'),
													'product_uom_qty':values.get('quantity'),
													'product_qty':values.get('quantity'),
													'product_uom':uom_obj_search.id,
													'price_unit':values.get('price'),
													'date_planned':purchase_order_brw.date_order,
													})
			elif purchase_order_brw.state == 'sent':
				order_lines=self.env['purchase.order.line'].create({
													'order_id':purchase_order_brw.id,
													'product_id':product_id.id,
													'name':values.get('description'),
													'product_uom_qty':values.get('quantity'),
													'product_qty':values.get('quantity'),
													'product_uom':uom_obj_search.id,
													'price_unit':values.get('price'),
													'date_planned':purchase_order_brw.date_order,
													})
			elif purchase_order_brw.state != 'sent' or purchase_order_brw.state != 'draft':
				raise UserError(_('We cannot import data in validated or confirmed order.'))
			if tax_id_lst:
				order_lines.write({'taxes_id':([(6,0,tax_id_lst)])})
		else:
			if self.import_prod_option == 'barcode':
				product_obj_search=self.env['product.product'].search([('barcode',  '=',values['product'])])
			elif self.import_prod_option == 'code':
				product_obj_search=self.env['product.product'].search([('default_code', '=',values['product'])])
			else:
				product_obj_search=self.env['product.product'].search([('name', '=',values['description'])])
				product_title=values.get('description')
			if product_obj_search:
				if len(product_obj_search) > 1:
					raise Warning(_('More than one product found for "%s". Please use a unique identifier (barcode or code).') % product_title)
				product_id = product_obj_search[:1]

			else:
				raise UserError(_('%s product is not found.') % product_title)

			if purchase_order_brw.state == 'draft':
				order_lines=self.env['purchase.order.line'].create({
													'order_id':purchase_order_brw.id,
													'product_id':product_id.id,
													'product_uom_qty':values.get('quantity'),
													'product_qty':values.get('quantity'),
													'date_planned':purchase_order_brw.date_order,
													})
				order_lines.product_id_change() 
				order_lines._onchange_discount()                                                   
														
			elif purchase_order_brw.state == 'sent':
				order_lines=self.env['purchase.order.line'].create({
													'order_id':purchase_order_brw.id,
													'product_id':product_id.id,
													'product_uom_qty':values.get('quantity'),
													'product_qty':values.get('quantity'),
													'date_planned':purchase_order_brw.date_order,
													})
				order_lines.product_id_change()
				order_lines._onchange_discount()
																	
			elif purchase_order_brw.state != 'sent' or purchase_order_brw.state != 'draft':
				raise UserError(_('We cannot import data in validated or confirmed order.'))

		return True
	
	
	def download_auto(self):
		if self.sample_option == 'csv':
			return {
				'type' : 'ir.actions.act_url',
				'url': '/web/content/importar_lineas_compra.sample_purchase_order_line_csv?download=true',
				'target': 'new',
			}
		else:
			return {
				'type' : 'ir.actions.act_url',
				'url': '/web/content/importar_lineas_compra.sample_purchase_order_line_xls?download=true',
				'target': 'new',
			}


class PurchaseOrderImportConfirmWizard(models.TransientModel):

	_name = 'purchase.order.import.confirm.wizard'
	_description = 'Import Purchase Lines Confirmation'

	message = fields.Html(readonly=True)

	def action_ok(self):
		return {'type': 'ir.actions.act_window_close'}
