# src/turbopdf/assemblers/form.py
from .base import BaseFormAssembler

class FormularioReposicionAssembler(BaseFormAssembler):
    def __init__(self, context=None):
        super().__init__(context)
        self.page_number = 1
        self.total_pages = 4

    def build(self):
        # === Página 1 ===
        self.add_component('titulo_logo.html', {
            'titulo1': "FORMULARIO DE RECURSO DE REPOSICIÓN",
            'titulo2': "CONTRA RESOLUCIONES DEL COMITÉ CERREM INDIVIDUAL Y COLECTIVO",
            'titulo3': "UNIDAD NACIONAL DE PROTECCIÓN"
        })

        self.add_component('titulo.html', {'titulo': "Datos del radicado (Espacio para uso exclusivo de la UNP)"})
        self.add_component('fila_tres.html', {
            'label1': "1. Número del radicado *", 'valor1': self.context.get('numRadicado', ''),
            'label2': "2. Fecha de radicado *", 'valor2': self.context.get('fechaRadicado', ''),
            'label3': "3. Sede/Oficina", 'valor3': self.context.get('sedeRadicado', ''),
        })
        self.add_component('titulo.html', {'titulo': "Fecha y lugar de diligenciamiento"})
        self.add_component('fila_cuatro.html', {
            'label1': "4. Fecha de diligenciamiento *", 'valor1': self.context.get('fechaDiligenciamiento', ''), 'ancho1': "30%",
            'label2': "5. País *", 'valor2': self.context.get('paisDiligenciamiento', ''), 'ancho2': "20%",
            'label3': "6. Departamento *", 'valor3': self.context.get('dptoDiligenciamiento', ''), 'ancho3': "25%",
            'label4': "7. Municipio *", 'valor4': self.context.get('mnpioDiligenciamiento', ''), 'ancho4': "25%",
        })
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-file-lines", 'titulo': "Resolución CERREM"
        })
        self.add_component('fila_dos.html', {
            'label1': "8. Número del radicado", 'valor1': self.context.get('numResolucion', ''),
            'label2': "9. Fecha de radicado", 'valor2': self.context.get('fechaResolucion', ''),
        })
        self.add_component('titulo.html', {'titulo': "Datos básicos"})
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-user", 'titulo': "Nombre(s) y apellido(s)"
        })
        self.add_component('fila_cuatro.html', {
            'label1': "10. Primer nombre *", 'valor1': self.context.get('primerNombre', ''), 'ancho1': "25%",
            'label2': "11. Segundo nombre", 'valor2': self.context.get('segundoNombre', ''), 'ancho2': "25%",
            'label3': "12. Primer apellido *", 'valor3': self.context.get('primerApellido', ''), 'ancho3': "25%",
            'label4': "13. Segundo apellido", 'valor4': self.context.get('segundoApellido', ''), 'ancho4': "25%",
        })
        self.add_component('tipos_checkbox.html', {
            'labelSelect': "15. Género *",
            'labelSelected1': "Femenino", 'labelSelected2': "Masculino", 'labelSelected3': "No binario",
            'genero': self.context.get('genero', '')
        })
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-address-card", 'titulo': "Número único de identificación personal (NUIP)"
        })
        self.add_component('tipo_identificacion.html', {
            'numeracion1': 16,
            'numeracion2': "17. Número de identificación *", 'numeroIdentificacion': self.context.get('NumeroIdentificacion', ''),
            'numeracion3': "18. Fecha de expedición *", 'fechaExpedicion': self.context.get('fechaExpedicion', ''),
            'tipoIdentificacion': self.context.get('tipoIdentificacion', ''),
        })
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-phone", 'titulo': "Datos de contacto"
        })
        self.add_component('fila_cuatro.html', {
            'label1': "19. Celular uno *", 'valor1': self.context.get('celularUno', ''), 'ancho1': "20%",
            'label2': "20. Celular dos", 'valor2': self.context.get('celularDos', ''), 'ancho2': "20%",
            'label3': "21. Teléfono", 'valor3': self.context.get('telefono', ''), 'ancho3': "20%",
            'label4': "22. Correo electrónico *", 'valor4': self.context.get('correo', ''), 'ancho4': "40%",
        })
        self.add_component('autoriza_envio.html', {
            'pregunta': "23. ¿Autoriza el envío de comunicaciones y notificaciones a través del correo electrónico inscrito?",
            'valor': self.context.get('autoriza', '')
        })
        self.add_component('leyenda_autoriza_correo.html', {})
        self.add_raw_html('<br>')
        self.add_component('pregunta_si_no.html', {
            'margen': 0,
            'pregunta': "24. ¿Presenta hechos sobrevinientes?",
            'valor': self.context.get('presenta_hechos', '')
        })
        self.add_component('encaso_de.html', {
            'encasode': "* En caso de haber marcado afirmativo la pregunta 24 diligencia los siguientes campos:"
        })

        # === Página 2 ===
        self.add_page_break()
        self.add_raw_html('<div style="border: 1px solid #303d50; border-radius: 5px; min-height: 1170px; font-family: \'Roboto\', sans-serif;">')
        self.add_component('hechos_sobrevinientes_vacio.html', {})
        self.add_raw_html('</div>')
        self.add_component('oficializacion.html', {
            'codigo': "GJU-FT-52-VX", 'fecha': "Oficialización: 00/00/0000", 'pagina': "Pág. 2 de 2"
        })

        # === Página 3 ===
        self.add_page_break()
        self.add_raw_html('<div style="border: 1px solid #303d50; border-radius: 5px; min-height: 1170px; font-family: \'Roboto\', sans-serif;">')
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-shield", 'titulo': "Medidas de Protección"
        })
        self.add_component('pregunta_si_no.html', {
            'margen': 0,
            'pregunta': "32. ¿Es beneficiario de medidas de protección por la UNP?",
            'valor': self.context.get('tiene_medidas', '')
        })
        self.add_component('titulo.html', {'titulo': "Datos apoderado"})
        self.add_component('pregunta_si_no.html', {
            'margen': 0,
            'pregunta': "33. ¿Presenta recurso mediante apoderado?",
            'valor': self.context.get('presentaApoderado', '')
        })
        self.add_component('encaso_de.html', {
            'encasode': "* En caso de respuesta afirmativa, diligencie los siguientes campos:"
        })
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-user", 'titulo': "Nombre(s) y apellido(s)"
        })
        self.add_component('fila_cuatro.html', {
            'label1': "34. Primer nombre *", 'valor1': self.context.get('primerNombreApoderado', ''), 'ancho1': "25%",
            'label2': "35. Segundo nombre", 'valor2': self.context.get('segundoNombreApoderado', ''), 'ancho2': "25%",
            'label3': "36. Primer apellido *", 'valor3': self.context.get('primerApellidoApoderado', ''), 'ancho3': "25%",
            'label4': "37. Segundo apellido", 'valor4': self.context.get('segundoApellidoApoderado', ''), 'ancho4': "25%",
        })
        self.add_component('subtitulo_icono.html', {
            'icono': "fa-solid fa-address-card", 'titulo': "Número único de identificación personal (NUIP)"
        })
        self.add_component('tipo_identificacion.html', {
            'numeracion1': 38,
            'numeracion2': "39. Número de identificación *", 'numeroIdentificacion': self.context.get('numeroIdentificacionApoderado', ''),
            'numeracion3': "40. Tarjeta Profesional*", 'tarjetaProfesional': self.context.get('tarjetaProfesional', ''),
        })
        self.add_component('titulo.html', {'titulo': "Inconformidad"})
        self.add_component('texarea.html', {
            'label': "41. Descripción clara de los motivos de inconformidad",
            'alto': "594px", 'valor': self.context.get('motivoInconformidad', '')
        })
        self.add_component('leyenda_superiol.html', {
            'mensaje': self.context.get('leyenda_motivo', '')
        })
        self.add_raw_html('</div>')
        self.add_component('oficializacion.html', {
            'codigo': "GJU-FT-52-VX", 'fecha': "Oficialización: 00/00/0000", 'pagina': "Pág. 3 de 3"
        })

        # === Página 4 ===
        self.add_page_break()
        self.add_raw_html('<div style="border: 1px solid #303d50; border-radius: 5px; min-height: 1120px; font-family: \'Roboto\', sans-serif;">')
        self.add_component('anexos_limpio.html', {})
        self.add_component('manifiesto.html', {'numeracion': "42. "})
        self.add_component('titulo.html', {'titulo': "Nombre y firma del solicitante"})
        self.add_component('firmaop2.html', {'nombre_completo': self.context.get('nombreCompleto', '')})
        self.add_raw_html('</div>')
        self.add_component('archivese.html', {})
        self.add_component('oficializacion.html', {
            'codigo': "GJU-FT-52-VX", 'fecha': "Oficialización: 00/00/0000", 'pagina': "Pág. 4 de 4"
        })

        # Generar PDF
        return super().build()