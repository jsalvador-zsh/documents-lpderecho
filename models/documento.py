# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import date

class CategoriaModel(models.Model):
    _name = 'categoria.documento'
    _description = 'Categorias generales para registro de documentos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Categoría', required=True)

class DocumentosModel(models.Model):
    _name = 'documentos'
    _description = 'Manejo de documentos por categoria'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre del documento', required=True)
    fecha_registro = fields.Date(string='Fecha', required=True, default=lambda self: fields.Date.context_today(self))
    categoria_documento = fields.Many2one('categoria.documento', string = 'Categoría')
    documento = fields.Binary(string="Dcoumento")
    name_documento = fields.Char(string="Nombre del documento")

    observaciones = fields.Char('Obsrevaciones', tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

class ConvenioModel(models.Model):
    _name = 'documento.convenio'
    _description = 'Convenios'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # campos convenio
    name = fields.Char('Nombre del documento', required=True)
    documento = fields.Binary(string="Documento")
    name_documento = fields.Char(string="Nombre del documento")
    estado = fields.Selection([
        ('vigente', 'Vigente'),
        ('vencer', 'Por vencer'),
        ('vencido', 'Vencido'),
        ('coordinacion', 'En coordinación')
    ], string='Estado', tracking=True, compute='_compute_estado', store=True)
    entidad = fields.Many2one('curso.convenio', string='Entidad', tracking=True)
    inicio = fields.Date(string='Inicio', tracking=True)
    fin = fields.Date(string='Fin', tracking=True)
    dias_faltantes = fields.Integer('Días faltantes', compute='_compute_dias_faltantes', store=True)
    # curso_relacionado = fields.Many2one('curso.curso', string='Curso relacionado', tracking=True)
    contacto_ids = fields.One2many('contacto.convenio', 'contacto_id', string='Contactos asociados')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    @api.depends('fin')
    def _compute_dias_faltantes(self):
        for record in self:
            if record.fin:
                fin_date = fields.Date.from_string(record.fin)
                today = date.today()
                record.dias_faltantes = (fin_date - today).days
            else:
                record.dias_faltantes = 0

    @api.depends('dias_faltantes', 'inicio', 'fin')
    def _compute_estado(self):
        for record in self:
            if record.inicio and record.fin:
                if record.dias_faltantes < 0:
                    record.estado = 'vencido'
                elif 0 <= record.dias_faltantes <= 45:
                    record.estado = 'vencer'
                else:
                    record.estado = 'vigente'
            else:
                record.estado = 'coordinacion'

    def write(self, vals):
        res = super(ConvenioModel, self).write(vals)
        for record in self:
            if 'fin' in vals or 'dias_faltantes' in vals:
                if 0 < record.dias_faltantes <= 60:
                    record.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary='Convenio por vencerse',
                        note=f'El convenio {record.name} está por vencerse en {record.dias_faltantes} días.',
                        user_id=self.env.user.id,
                        date_deadline=record.fin
                    )
                elif record.dias_faltantes <= 0:
                    record.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary='Convenio vencido',
                        note=f'El convenio {record.name} se ha vencido.',
                        user_id=self.env.user.id,
                        date_deadline=record.fin
                    )
        return res

    @api.model
    def create(self, vals):
        record = super(ConvenioModel, self).create(vals)
        if 0 < record.dias_faltantes <= 60:
            record.activity_schedule(
                'mail.mail_activity_data_todo',
                summary='Convenio por vencerse',
                note=f'El convenio {record.name} está por vencerse en {record.dias_faltantes} días.',
                user_id=self.env.user.id,
                date_deadline=record.fin
            )
        return record

class PersonaContactoConvenio(models.Model):
    _name ='contacto.convenio'
    _description = 'Convenio'

    contacto_id = fields.Many2one('documento.convenio', string='Contacto convenio', required=True)
    contacto = fields.Many2one('res.partner', string='Nombre', required=True)
    cargo = fields.Char('Cargo')

class InformeModel(models.Model):
    _name = 'documento.informe'
    _description = 'Informe'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # campos informe
    name = fields.Char('Código', tracking=True, default='/')
    nombre = fields.Char('Nombre del documento')
    documento = fields.Binary(string="Documento")
    name_documento = fields.Char(string="Nombre del documento")
    tipo = fields.Selection([
        ('inicial', 'Inicial'),
        ('final', 'Final'),
        ('confirmacion', 'Confirmación datos'),
        ('otros', 'Otros')
    ], string='Tipo', tracking=True)
    inicio = fields.Date(related='curso_relacionado.fecha_inicio', string='Inicio', tracking=True)
    fin = fields.Date(related='curso_relacionado.fecha_fin', string='Fin', tracking=True)
    fecha = fields.Date(string='Fecha', required=True, default=lambda self: fields.Date.context_today(self))
    motivo = fields.Char('Motivo', tracking=True)
    entidad_destino = fields.Many2one('curso.convenio', string='Entidad', tracking=True)
    redactado = fields.Many2one('res.users', string='Redactado por', default=lambda self: self.env.user)
    oficio_asociado = fields.Many2one('documento.oficio', string='Oficio asociado')

    curso_relacionado = fields.Many2one('curso.curso', string='Curso relacionado', tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self._generate_codigo()
        return super(InformeModel, self).create(vals)

    def _generate_codigo(self):
        current_year = date.today().year
        sequence = self.env['ir.sequence'].next_by_code('documento.informe.sequence') or '001'
        return f"{sequence}-{current_year}-LP"

    @api.model
    def _get_next_sequence(self):
        self.env.cr.execute("""
            SELECT COALESCE(MAX(SUBSTRING(name FROM '^[0-9]+'))::INTEGER, 0) + 1
            FROM documento_informe
            WHERE name LIKE %s
        """, [f"%-{date.today().year}-%"])
        result = self.env.cr.fetchone()
        return str(result[0]).zfill(3) if result else '001'

class OficioModel(models.Model):
    _name = 'documento.oficio'
    _description = 'Oficio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # campos oficio
    name = fields.Char('Código', tracking=True, default='/')
    nombre = fields.Char('Nombre del documento')
    documento = fields.Binary(string="Documento")
    name_documento = fields.Char(string="Nombre del documento")
    tipo = fields.Selection([
        ('inicial', 'Inicial'),
        ('final', 'Final'),
        ('confirmacion', 'Confirmación datos'),
        ('otros', 'Otros')
    ], string='Tipo', tracking=True)
    fecha = fields.Date(string='Fecha', required=True, default=lambda self: fields.Date.context_today(self))
    entidad_destino = fields.Many2one('curso.convenio', string='Entidad', tracking=True)
    motivo = fields.Char('Motivo', tracking=True)
    redactado = fields.Many2one('res.users', string='Redactado por', default=lambda self: self.env.user)
    informe_ids = fields.One2many('documento.informe', 'oficio_asociado', string='Lista de informes')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self._generate_codigo()
        return super(OficioModel, self).create(vals)

    def _generate_codigo(self):
        current_year = date.today().year
        sequence = self.env['ir.sequence'].next_by_code('documento.oficio.sequence') or '001'
        return f"{sequence}-{current_year}-LP"

    @api.model
    def _get_next_sequence(self):
        self.env.cr.execute("""
            SELECT COALESCE(MAX(SUBSTRING(name FROM '^[0-9]+'))::INTEGER, 0) + 1
            FROM documento_oficio
            WHERE name LIKE %s
        """, [f"%-{date.today().year}-%"])
        result = self.env.cr.fetchone()
        return str(result[0]).zfill(3) if result else '001'

class MyDocuments(models.Model):
    _inherit = 'ir.attachment'

class ResolucionModel(models.Model):
    _name = 'documento.resolucion'
    _description = 'Resolucion'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    year = fields.Char('Año', tracking=True)
    resolucion_decanal = fields.Char('Resolución decanal', tracking=True, required=True)
    emision = fields.Date('Emisión', tracking=True)
    nombre_programa = fields.Many2one('curso.curso', string='Nombre programa', tracking=True)
    inicio = fields.Date(related='nombre_programa.fecha_inicio', string='Inicio', tracking=True)
    termino = fields.Date(related='nombre_programa.fecha_fin', string='Término', tracking=True)
    informe_inicial = fields.Many2one('documento.informe', string='Informe inicial', tracking=True)
    oficio_inicial = fields.Many2one('documento.oficio', string='Oficio inicial', tracking=True)
    dias_faltantes = fields.Float('Días faltantes', compute='_compute_dias_faltantes', store=True, tracking=True)
    cantidad_certi = fields.Integer('Cantidad certi/diplo', tracking=True)
    cantidad_pagada = fields.Integer('Cantidad pagada', tracking=True)
    monto_depositar = fields.Integer('Monto a depositar', tracking=True)
    fecha_deposito = fields.Date('Fecha depósito', tracking=True)
    informe_final = fields.Many2one('documento.informe', string='Informe final', tracking=True)
    oficio_final = fields.Many2one('documento.oficio', string='Oficio final', tracking=True)
    observacion = fields.Char('Observación', tracking=True)
    entidad = fields.Many2one('curso.convenio', string='Entidad', tracking=True)

    documento = fields.Binary(string="Documento")
    name_documento = fields.Char(string="Nombre del documento")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    @api.depends('termino')
    def _compute_dias_faltantes(self):
        for record in self:
            if record.termino:
                termino_date = fields.Date.from_string(record.termino)
                today = date.today()
                record.dias_faltantes = (termino_date - today).days
            else:
                record.dias_faltantes = 0

class VigenciaPoderModel(models.Model):
    _name = 'documento.vigencia'
    _description = 'Vigencia poder y ficha ruc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Código', tracking=True)
    fecha_solicitud = fields.Date('Fecha solicitud', tracking=True)
    fecha_atencion = fields.Date('Fecha atención', tracking=True)
    estado = fields.Selection([('porvencer','Por vencer'),('vigente','Vigente'),('vencido','Vencido')], string='Estado', tracking=True)
    vigencia_inicio = fields.Date('Inicio', tracking=True)
    vigencia_fin = fields.Date('Fin', tracking=True)
    dias_faltantes = fields.Float('Días faltantes', compute='_compute_dias_faltantes', store=True, tracking=True)
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    @api.depends('vigencia_fin')
    def _compute_dias_faltantes(self):
        for record in self:
            if record.vigencia_fin:
                today = fields.Date.today()
                record.dias_faltantes = (record.vigencia_fin - today).days
            else:
                record.dias_faltantes = 0

            if record.dias_faltantes >= 6:
                record.estado = 'vigente'
            elif 1 <= record.dias_faltantes < 6:
                record.estado = 'porvencer'
            else:
                record.estado = 'vencido'

    def write(self, vals):
        res = super(VigenciaPoderModel, self).write(vals)
        for record in self:
            if 'vigencia_fin' in vals or 'dias_faltantes' in vals:
                if 0 < record.dias_faltantes <= 7:
                    record.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary='La vigencia poder está por vencerse',
                        note=f'La vigencia {record.name} está por vencerse en {record.dias_faltantes} días.',
                        user_id=self.env.user.id,
                        date_deadline=record.vigencia_fin
                    )
                elif record.dias_faltantes <= 0:
                    record.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary='Convenio vencido',
                        note=f'El convenio {record.name} se ha vencido.',
                        user_id=self.env.user.id,
                        date_deadline=record.vigencia_fin
                    )
        return res

    @api.model
    def create(self, vals):
        record = super(VigenciaPoderModel, self).create(vals)
        if 0 < record.dias_faltantes <= 7:
            record.activity_schedule(
                'mail.mail_activity_data_todo',
                summary='Vigencia poder por vencerse',
                note=f'La vigencia poder {record.name} está por vencerse en {record.dias_faltantes} días.',
                user_id=self.env.user.id,
                date_deadline=record.vigencia_fin
            )
        return record


   











    
