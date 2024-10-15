# -*- coding: utf-8 -*-
{
    'name': "Documentos",
    'summary': "Registro de documentos según categoría (convenios, informes, oficios, etc.)",
    'description': """
    """,
    'author': "Juan Salvador",
    # 'website': "https://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Productivity',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'students'],
    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'views/documento_view.xml',
        'views/documento_convenio_view.xml',
        'views/documento_oficio_view.xml',
        'views/documento_informe_view.xml',
        'views/documento_resolucion_view.xml',
        'views/documento_vigencia_view.xml',
        'views/menu_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
