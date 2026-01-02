# Copyright 2022 - Komun.org Álex Berbel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Importar lineas de pedido en compras',
    'version': "17.0.1.0.2",
    'summary': 'Importar de varias maneras líneas de compra en un pedido.',
    'category': 'Purchases',
    'description': """Este módulo se utiliza para importar líneas de pedidos de compras a granel desde el archivo de Excel. Importar líneas de orden de compra desde CSV o archivo de Excel.
Importar compras, Línea de orden de compra de importación, Importar líneas de compra, Importar línea SO. Importación de compra, agregue SO de Excel. Agregue líneas de orden de compra de Excel. Agregue archivo CSV. Importe de datos de compra. Importar archivo de Excel Este módulo se utiliza para importar clientes potenciales a granel del archivo de Excel. Importar plomo desde CSV o archivo de Excel.
Importar datos de clientes potenciales, agregar clientes potenciales de excel. Importar archivo de Excel-""",
    'author': 'Colectivo DEVCONTROL',
    'website': 'https://framagit.org/devcontrol',
    'depends': ['base','purchase'],
    "external_dependencies": {"python": [
        "openpyxl~=3.1.5"
    ]},
    'data': [
                'security/ir.model.access.csv',
    		    'importar_lineas_compra_view.xml',
                'data/attachment_sample.xml',
                'wizards/confirm_wizard_view.xml',
            ],
    'demo': [],
    'test': [],
    'installable':True,
    'auto_install':False,
    'application':False,
    'license': 'AGPL-3',
}

