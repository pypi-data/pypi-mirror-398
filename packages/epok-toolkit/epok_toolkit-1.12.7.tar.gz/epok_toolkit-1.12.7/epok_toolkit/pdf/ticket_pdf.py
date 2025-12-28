from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from datetime import date, datetime
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from dataclasses import dataclass
from typing import Optional
from PIL import Image
from uuid import uuid4, UUID
import os
import qrcode
from io import BytesIO
import importlib.resources



fuente_path = os.path.join(os.path.dirname(__file__), "fuentes", "Kollektif-Bold.ttf")
pdfmetrics.registerFont(TTFont("kollektif", fuente_path))


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    return tuple(int(hex_color[i:i + lv // 3], 16) / 255.0 for i in range(0, lv, lv // 3))


class Config:
    base_path = os.path.dirname(__file__)
    plantillas = base_path + "/plantillas/"
    plantilla_path = importlib.resources.files("epok_toolkit.pdf.plantillas").joinpath("Ticket_congrats.png")
    output_path = os.path.join(base_path, "ticket_final.pdf")
    fuente = "Helvetica"
    fuente_bold = "kollektif"
    #bg_color = "#0082FF"  
    bg_color = "#FFFFFF"  
    font_color = "#000000"  


class Contenedor:
    def __init__(self, x, y, w, h, bold: bool = False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = Config.bg_color
        self.font_size = 28
        self.font_color = Config.font_color
        self.fuente = Config.fuente_bold if bold else Config.fuente

    def dibujar(self, c):
        c.setFillColorRGB(*hex_to_rgb(self.color))
        c.rect(self.x, self.y, self.w, self.h, stroke=0, fill=1)


    def dibujar_texto(self, c, texto):
        c.setFillColorRGB(*hex_to_rgb(self.font_color))
        c.setFont(self.fuente, self.font_size)
        ascent = pdfmetrics.getAscent(self.fuente) * self.font_size / 1000
        descent = abs(pdfmetrics.getDescent(self.fuente) * self.font_size / 1000)
        text_h = ascent + descent
        baseline_x = self.x + self.w / 2
        baseline_y = self.y + (self.h - text_h) / 2 + descent
        c.drawCentredString(baseline_x, baseline_y, texto)


class ContenedorTexto(Contenedor):
    def __init__(self, x, y, w, h, bold: bool = False, texto="Demo",
                 font_size=28,
                 font_color=None,
                 color=None,
                 fuente=None):
        super().__init__(x, y, w, h, bold=bold)
        self.texto = texto
        if font_size:
            self.font_size = font_size
        if font_color:
            self.font_color = font_color
        if color:
            self.color = color
        if fuente:
            self.fuente = fuente
    
    def dibujar(self, c):
        super().dibujar(c)
        self.dibujar_texto(c, self.texto)


class ContenedorQR(Contenedor):
    def __init__(self, x, y, w, h, texto="QR vacío", color=None):
        super().__init__(x, y, w, h)
        self.texto = texto
        if color:
            self.color = color

    def dibujar(self, c):
        super().dibujar(c)
        qr = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_H, # type: ignore
            box_size=10,
            border=1,
        )
        qr.add_data(self.texto)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB") # type: ignore
        qr_img = qr_img.resize((self.w, self.h), Image.LANCZOS) # type: ignore
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)
        c.drawImage(ImageReader(buffer), self.x, self.y, width=self.w, height=self.h)


@dataclass
class TicketPDF:
    nombre_evento: str
    fecha: Optional[date]
    titulo_ticket: str
    precio: float
    edad_min: int
    tipo_evento: str
    direccion: str
    ticket_actual: int
    total_tickets: int
    nombre_persona: str
    uuid: Optional[UUID] = None
    hora_evento: Optional[str] = None
    qr : Optional[str] = None

    def __post_init__(self):
        if isinstance(self.fecha, str):
            self.fecha = datetime.strptime(self.fecha, "%Y-%m-%d %H:%M")
        elif isinstance(self.fecha, date) and not isinstance(self.fecha, datetime):
            hora = self.hora_evento or "00:00"
            self.fecha = datetime.combine(self.fecha, datetime.strptime(hora, "%H:%M").time())
        if not self.uuid:
            raise ValueError("UUID no puede ser None")
        
        self.hora_evento = self.fecha.strftime("%H:%M") # type: ignore
        self.width = 0
        self.height = 0
        self.font_size = 28
        self.font_color = Config.font_color
        self.color = Config.bg_color
        self.fuente = Config.fuente
        with Config.plantilla_path.open("rb") as f:
            self.img = Image.open(f)
            self.img.load()
        self.width, self.height = self.img.size
        self.buffer = BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=(self.width, self.height))


    def generate_ticket(self):
        def y(px): return self.height - px
        with Config.plantilla_path.open("rb") as f:
            self.c.drawImage(ImageReader(f), 0, 0, width=self.width, height=self.height, mask='auto')

        # NOMBRE EVENTO
        nombre_evento = ContenedorTexto(x=260, y=y(210), w=1400, h=90, texto=self.nombre_evento, font_size=78, bold=True)
        nombre_evento.dibujar(self.c)
        
        # FECHA
        SPANISH_DAYS = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
        }
        SPANISH_MONTHS = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
            'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
            'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        fecha_obj = self.fecha  # type: ignore
        day_name = SPANISH_DAYS[fecha_obj.strftime('%A')] # type: ignore
        month_name = SPANISH_MONTHS[fecha_obj.strftime('%B')] # type: ignore
        fecha = f"{day_name}, {fecha_obj.day} {month_name}".upper() #type: ignore
        fecha = ContenedorTexto(x=570, y=y(320), w=900, h=90, texto=fecha, font_size=38, bold=True)
        fecha.dibujar(self.c)

        # TICKET TITULO
        ticket_titulo = ContenedorTexto(x=260, y=y(525), w=950, h=90, texto=self.titulo_ticket, font_size=68, bold=True)
        ticket_titulo.dibujar(self.c)
        
        # PRECIO
        precio = f"{self.precio:,.2f} MXN"
        precio = ContenedorTexto(x=450, y=y(650), w=600, h=90, texto=precio, font_size=58, bold=True)
        precio.dibujar(self.c)
        
        # EDAD MINIMA
        edad_min = str(self.edad_min)
        edad_min = ContenedorTexto(x=345, y=y(760), w=80, h=30, texto=edad_min, font_size=18, bold=True)
        edad_min.dibujar(self.c)
        
        # HORA DE ACCESO
        hora_evento = ContenedorTexto(x=670, y=y(760), w=80, h=30, texto=self.hora_evento, font_size=18, bold=True) # type: ignore
        hora_evento.dibujar(self.c)
        
        # TIPO DE EVENTO
        tipo_evento = ContenedorTexto(x=995, y=y(760), w=150, h=30, texto=self.tipo_evento, font_size=18, bold=True)
        tipo_evento.dibujar(self.c)

        # DIRECCION
        direccion = ContenedorTexto(x=200, y=y(950), w=1400, h=50, texto=self.direccion, font_size=38, bold=True)
        direccion.dibujar(self.c)

        # TICKET ACTUAL
        texto = f"Ticket {self.ticket_actual} de {self.total_tickets}"
        ticket_actual = ContenedorTexto(x=680, y=y(1035), w=340, h=50, texto=texto, font_size=28, bold=True)
        ticket_actual.dibujar(self.c)
        
        # NOMBRE PERSONA
        nombre_persona = ContenedorTexto(x=1080, y=y(1035), w=760, h=60, texto=self.nombre_persona, font_size=48, bold=True)
        nombre_persona.dibujar(self.c)
        
        # UUID
        uuid_string = self.uuid
        # UUID
        uuid_string = str(self.uuid)
        uuid = ContenedorTexto(x=1390, y=y(770), w=400, h=30, texto=uuid_string, font_size=18, bold=True)
        uuid.dibujar(self.c)
        tam = 400
        qr = ContenedorQR(x=1390, y=y(740), w=tam, h=tam, texto=uuid_string, color=Config.bg_color)
        qr.dibujar(self.c)

        self.c.showPage()
        self.c.save()
        self.buffer.seek(0)
        return self.buffer.getvalue()



        
if __name__ == "__main__":
    ticket = TicketPDF(
        nombre_evento="14 aniversario Cerveza Libertad",
        fecha=datetime(2025, 5, 31, 14, 30),
        titulo_ticket="General",
        precio=410,
        edad_min=18,
        tipo_evento="Aniversario",
        direccion="Restaurante dentro de Hacienda del Conde",
        ticket_actual=2,
        total_tickets=5,
        nombre_persona="Carolina Franco Medina",
        uuid=uuid4(),
    )
    ticket.generate_ticket()