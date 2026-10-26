"""Genera el paquete gráfico del Reel testimonio Sebastián Paipa (Dra. Sofía Alegría).

Salida (1080x1920, 30 fps):
  tarjetas/*.mp4 y *.png   tarjetas de pregunta animadas (1 s)
  textos/*.png             textos clave con fondo transparente para poner encima del video
  titulo_antes_despues.png rótulos ANTES / DESPUÉS + nombre para la imagen IMG_0652
  cierre.mp4               cierre de marca (4 s)
  guia_60s.mp4             video guía con todos los tiempos del guion final

Uso: python3 generar.py <carpeta_con_fuentes_montserrat_woff>
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
PETROLEO = (11, 79, 92)
PROFUNDO = (7, 59, 69)
TURQUESA = (47, 181, 168)
BLANCO = (255, 255, 255)

FONT_DIR = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(__file__))


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"montserrat-latin-{weight}-normal.woff"), size)


def fondo():
    """Degradado vertical azul profundo -> azul petróleo."""
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(PROFUNDO[i] + (PETROLEO[i] - PROFUNDO[i]) * (1 - abs(2 * t - 1))) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    return img


FONDO = fondo()


def envolver(texto, f, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if f.getlength(prueba) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def texto_centrado(d, lineas, f, y_centro, color, interlinea=1.18, resaltar=()):
    alto = f.size * interlinea
    y = y_centro - alto * len(lineas) / 2
    for linea in lineas:
        x = (W - f.getlength(linea)) / 2
        for palabra in linea.split(" "):
            limpia = palabra.strip("¿?¡!.,…\"").upper()
            c = TURQUESA if limpia in resaltar else color
            d.text((x, y), palabra, font=f, fill=c)
            x += f.getlength(palabra + " ")
        y += alto


def tarjeta(pregunta, resaltar=()):
    """Capa de la tarjeta (texto + adornos) sobre fondo transparente."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    f = font(800, 92)
    lineas = envolver(pregunta, f, W - 200)
    texto_centrado(d, lineas, f, H / 2, BLANCO, resaltar=resaltar)
    alto = f.size * 1.18 * len(lineas)
    y_linea = H / 2 + alto / 2 + 50
    d.rounded_rectangle([W / 2 - 70, y_linea, W / 2 + 70, y_linea + 10], 5, fill=TURQUESA)
    etiqueta = "TESTIMONIO  ·  DRA. SOFÍA ALEGRÍA"
    fe = font(600, 30)
    d.text(((W - fe.getlength(etiqueta)) / 2, H / 2 - alto / 2 - 110), etiqueta, font=fe, fill=TURQUESA)
    return capa


def ease(t):
    return 1 - (1 - t) ** 3


def frames_tarjeta(capa, n=FPS):
    """Pop-in: la capa entra escalando de 0.88 a 1 y con fundido en 7 frames."""
    for i in range(n):
        t = ease(min(1, i / 7))
        esc = 0.88 + 0.12 * t
        cw, ch = int(W * esc), int(H * esc)
        c = capa.resize((cw, ch), Image.LANCZOS)
        a = c.getchannel("A").point(lambda v: int(v * t))
        c.putalpha(a)
        frame = FONDO.copy()
        frame.paste(c, ((W - cw) // 2, (H - ch) // 2), c)
        yield frame


def texto_clave(texto, resaltar=(), tam=118):
    """Texto grande con sombra, sobre transparente, en la zona media-baja."""
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = font(800, tam)
    lineas = envolver(texto, f, W - 140)
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    texto_centrado(ImageDraw.Draw(sombra), lineas, f, H * 0.56 + 6, (0, 0, 0, 170))
    sombra = sombra.filter(ImageFilter.GaussianBlur(10))
    capa.alpha_composite(sombra)
    texto_centrado(ImageDraw.Draw(capa), lineas, f, H * 0.56, BLANCO, resaltar=resaltar)
    return capa


def subtitulo(texto):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    f = font(700, 50)
    lineas = envolver(texto, f, W - 160)
    alto = f.size * 1.25 * len(lineas)
    y0 = H * 0.72
    d.rounded_rectangle([60, y0 - 30, W - 60, y0 + alto + 20], 28, fill=(7, 59, 69, 215))
    texto_centrado(d, lineas, f, y0 + alto / 2, BLANCO, interlinea=1.25)
    return capa


def placeholder_clip(tc, bn=False):
    """Fondo que marca dónde va el clip de Sebastián (con su tiempo en el original)."""
    img = Image.new("RGB", (W, H), (38, 38, 38) if bn else (26, 34, 37))
    d = ImageDraw.Draw(img)
    f1, f2 = font(600, 40), font(800, 70)
    t1 = "CLIP DE SEBASTIÁN" + ("  ·  BLANCO Y NEGRO" if bn else "")
    d.text(((W - f1.getlength(t1)) / 2, 330), t1, font=f1, fill=(150, 150, 150))
    d.text(((W - f2.getlength(tc)) / 2, 400), tc, font=f2, fill=(200, 200, 200) if bn else TURQUESA)
    d.rectangle([40, 40, W - 40, H - 40], outline=(80, 80, 80), width=3)
    return img


def compuesto(base, *capas):
    img = base.convert("RGBA")
    for c in capas:
        if c is not None:
            img.alpha_composite(c)
    return img.convert("RGB")


class Encoder:
    def __init__(self, ruta):
        self.p = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
             "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", ruta],
            stdin=subprocess.PIPE)

    def frame(self, img, veces=1):
        b = img.convert("RGB").tobytes()
        for _ in range(veces):
            self.p.stdin.write(b)

    def cerrar(self):
        self.p.stdin.close()
        self.p.wait()


# ---------- Contenido (guion final) ----------
TARJETAS = [
    ("01_como_te_sentias", "¿Cómo te sentías con tu sonrisa?", {"SONRISA"}),
    ("02_miedos", "¿Qué miedos tenías?", {"MIEDOS"}),
    ("03_por_que_dra_sofia", "¿Por qué elegiste a la Dra. Sofía?", {"SOFÍA"}),
    ("04_te_dolio", "¿Te dolió?", {"DOLIÓ"}),
    ("05_espejo", "¿Qué sentiste al verte al espejo?", {"ESPEJO"}),
    ("06_familia", "¿Qué te dijo tu familia?", {"FAMILIA"}),
    ("07_seguridad", "¿Hoy sonríes con seguridad?", {"SEGURIDAD"}),
    ("08_dra_sofia", "¿Qué le dirías a la Dra. Sofía?", {"SOFÍA"}),
]

TEXTOS = {
    "no_relucia": ("NO RELUCÍA", {"RELUCÍA"}),
    "felicidad_inmensa": ("FELICIDAD INMENSA", {"INMENSA"}),
    "me_cambio_la_vida": ("ME CAMBIÓ LA VIDA", {"VIDA"}),
    "seguridad": ("SEGURIDAD", {"SEGURIDAD"}),
    "danar_los_dientes": ("¿DAÑAR LOS DIENTES?", {"DIENTES"}),
    "respaldo_natural": ("RESPALDO · NATURAL", {"NATURAL"}),
    "no_dolio": ("NO DOLIÓ", {"DOLIÓ"}),
    "no_lo_hagas": ("“NO LO HAGAS”", set()),
    "vino_desde_eeuu": ("VINO DESDE EE. UU.", {"EE", "UU"}),
    "quien_era": ("DEMOSTRAR QUIÉN ERA", {"QUIÉN", "ERA"}),
}


def cierre_frames(n=4 * FPS):
    f1, f2, f3 = font(500, 54), font(800, 96), font(700, 46)
    for i in range(n):
        frame = FONDO.copy().convert("RGBA")
        d = ImageDraw.Draw(frame)
        a1 = ease(min(1, i / 10))
        a2 = ease(min(1, max(0, (i - 12) / 10)))
        a3 = ease(min(1, max(0, (i - 26) / 10)))
        t1 = "Tu sonrisa también puede cambiar"
        d.text(((W - f1.getlength(t1)) / 2, 700 + 30 * (1 - a1)), t1, font=f1, fill=(255, 255, 255, int(255 * a1)))
        for j, t in enumerate(["Dra. Sofía", "Alegría"]):
            d.text(((W - f2.getlength(t)) / 2, 850 + j * 110 + 30 * (1 - a2)), t, font=f2,
                   fill=(255, 255, 255, int(255 * a2)))
        bw, bh = 640, 110
        bx, by = (W - bw) / 2, 1160 + 30 * (1 - a3)
        d.rounded_rectangle([bx, by, bx + bw, by + bh], 55, fill=TURQUESA + (int(255 * a3),))
        t3 = "Agenda tu valoración"
        d.text(((W - f3.getlength(t3)) / 2, by + (bh - 56) / 2), t3, font=f3, fill=(255, 255, 255, int(255 * a3)))
        d.text(((W - font(600, 30).getlength("[ LOGO AQUÍ ]")) / 2, 520), "[ LOGO AQUÍ ]", font=font(600, 30),
               fill=(255, 255, 255, int(110 * a1)))
        yield frame.convert("RGB")


def titulo_antes_despues():
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    f = font(800, 56)
    for txt, x in (("ANTES", 70), ("DESPUÉS", W - 70 - f.getlength("DESPUÉS"))):
        w = f.getlength(txt)
        d.rounded_rectangle([x - 26, 150, x + w + 26, 250], 22, fill=PETROLEO + (235,))
        d.text((x, 168), txt, font=f, fill=BLANCO)
    fn, fs = font(800, 64), font(500, 40)
    d.rounded_rectangle([60, 1500, W - 60, 1700], 30, fill=PETROLEO + (235,))
    d.rectangle([60, 1530, 72, 1670], fill=TURQUESA)
    d.text((110, 1530), "Sebastián Paipa", font=fn, fill=BLANCO)
    d.text((110, 1615), "27 años  ·  Diseño de sonrisa", font=fs, fill=TURQUESA)
    return capa


def main():
    os.makedirs(os.path.join(OUT, "tarjetas"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "textos"), exist_ok=True)

    capas_tarjeta = {}
    for nombre, pregunta, res in TARJETAS:
        capa = tarjeta(pregunta, res)
        capas_tarjeta[nombre] = capa
        compuesto(FONDO, capa).save(os.path.join(OUT, "tarjetas", nombre + ".png"))
        enc = Encoder(os.path.join(OUT, "tarjetas", nombre + ".mp4"))
        for fr in frames_tarjeta(capa):
            enc.frame(fr)
        enc.cerrar()

    capas_texto = {}
    for nombre, (txt, res) in TEXTOS.items():
        capas_texto[nombre] = texto_clave(txt, res)
        capas_texto[nombre].save(os.path.join(OUT, "textos", nombre + ".png"))
    cien = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = font(800, 330)
    ImageDraw.Draw(cien).text(((W - f.getlength("100%")) / 2, H * 0.44), "100%", font=f, fill=TURQUESA)
    cien.save(os.path.join(OUT, "textos", "100_porciento.png"))
    capas_texto["100"] = cien

    titulo = titulo_antes_despues()
    titulo.save(os.path.join(OUT, "titulo_antes_despues.png"))

    enc = Encoder(os.path.join(OUT, "cierre.mp4"))
    for fr in cierre_frames():
        enc.frame(fr)
    enc.cerrar()

    # ---------- Video guía de 60 s ----------
    # (duración s, tipo, datos)
    T = capas_texto
    guion = [
        (1.4, "clip", ("01:02–01:06", "…no relucía, ni en las fotos…", "no_relucia", True)),
        (1.3, "clip", ("05:50–05:53", "Uf… una felicidad inmensa.", "felicidad_inmensa", False)),
        (1.3, "clip", ("10:01–10:03", "Me cambió la vida.", "me_cambio_la_vida", False)),
        (2.0, "antes", None),
        (1.0, "tarjeta", "01_como_te_sentias"),
        (4.0, "clip", ("01:32–01:38", "No tenía seguridad al hablar o sonreír en público.", "seguridad", False)),
        (1.0, "tarjeta", "02_miedos"),
        (3.0, "clip", ("01:59–02:04", "Te vas a dañar los dientes.", "danar_los_dientes", False)),
        (1.0, "tarjeta", "03_por_que_dra_sofia"),
        (8.0, "clip", ("03:02–03:08 + 03:20–03:29",
                       "Con la Dra. Sofía Alegría sentí el respaldo que necesitaba… No quería una sonrisa de "
                       "Colgate, quería algo natural, adaptado a mi rostro.", "respaldo_natural", False)),
        (1.0, "tarjeta", "04_te_dolio"),
        (3.0, "clip", ("04:00–04:04", "Creía que iba a doler… no dolió para nada.", "no_dolio", False)),
        (1.0, "tarjeta", "05_espejo"),
        (3.0, "antes_clip", ("05:50–05:53", "Uf… una felicidad inmensa.")),
        (1.0, "tarjeta", "06_familia"),
        (4.0, "clip", ("06:27–06:29 + 07:10–07:16", "Quedaron impactados con mi sonrisa… Mi mamá me decía: "
                       "no lo hagas, definitivamente no lo hagas…", "no_lo_hagas", False)),
        (6.0, "clip", ("07:18–07:23", "…y hoy vive en Estados Unidos y viene hasta Colombia a hacerse el proceso.",
                       "vino_desde_eeuu", False)),
        (4.0, "clip", ("06:50–06:55", "Me sentí más relajado para reírme con ellos… y demostrar quién era.",
                       "quien_era", False)),
        (1.0, "tarjeta", "07_seguridad"),
        (2.0, "clip", ("08:55–08:58", "100%. 100%.", "100", False)),
        (1.0, "tarjeta", "08_dra_sofia"),
        (5.0, "clip", ("10:00–10:03 + 2 s sonriendo", "Muchas gracias… me cambió la vida.", "me_cambio_la_vida",
                       False)),
        (4.0, "cierre", None),
    ]
    total = sum(s for s, _, _ in guion)
    assert abs(total - 60) < 0.01, total

    antes_base = Image.new("RGB", (W, H), (30, 30, 30))
    da = ImageDraw.Draw(antes_base)
    fa = font(800, 60)
    for txt, x in (("IMAGEN", W / 4), ("IMG_0652", 3 * W / 4)):
        da.text((x - fa.getlength(txt) / 2, H / 2 - 40), txt, font=fa, fill=(110, 110, 110))
    da.line([(W / 2, 0), (W / 2, H)], fill=TURQUESA, width=6)

    enc = Encoder(os.path.join(OUT, "guia_60s.mp4"))
    for seg, tipo, datos in guion:
        n = round(seg * FPS)
        if tipo == "tarjeta":
            for fr in frames_tarjeta(capas_tarjeta[datos], n):
                enc.frame(fr)
        elif tipo == "clip":
            tc, sub, clave, bn = datos
            enc.frame(compuesto(placeholder_clip(tc, bn), T[clave], subtitulo(sub)), n)
        elif tipo == "antes":
            enc.frame(compuesto(antes_base, titulo), n)
        elif tipo == "antes_clip":
            tc, sub = datos
            enc.frame(compuesto(antes_base, T["felicidad_inmensa"], subtitulo(sub)), n)
        elif tipo == "cierre":
            for fr in cierre_frames(n):
                enc.frame(fr)
    enc.cerrar()


if __name__ == "__main__":
    main()
