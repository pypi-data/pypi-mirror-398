# Copyright 2022 - Komun.org Álex Berbel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Importar lineas de pedido en ventas",
    "version": "17.0.1.1.1",
    "summary": "Importar de varias maneras líneas de venta en un pedido.",
    "category": "Sales",
    "description": """Este módulo se utiliza para importar líneas de pedidos de ventas a granel desde el archivo de Excel. Importar líneas de orden de venta desde CSV o archivo de Excel.
Importar ventas, Línea de orden de venta de importación, Importar líneas de venta, Importar línea SO. Importación de venta, agregue SO de Excel. Agregue líneas de orden de venta de Excel. Agregue archivo CSV. Importe de datos de venta. Importar archivo de Excel Este módulo se utiliza para importar clientes potenciales a granel del archivo de Excel. Importar plomo desde CSV o archivo de Excel.
Importar datos de clientes potenciales, agregar clientes potenciales de excel. Importar archivo de Excel -""",
    "author": "Colectivo DEVCONTROL",
    "website": "https://framagit.org/devcontrol",
    "depends": ["base","sale_management"],
    "external_dependencies": {"python" : [
        "pandas==2.3.0",
        "filetype==1.2.0",
        "openpyxl~=3.1.5"
    ]},
    "data": [
        "security/ir.model.access.csv",
        "views/importar_lineas_pedido_view.xml",
        "data/attachment_sample.xml",
    ],
    "demo": [],
    "test": [],
    "installable":True,
    "auto_install":False,
    "application":False,
    "license": "AGPL-3",
}

