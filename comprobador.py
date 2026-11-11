import os
import sys
import time
import requests
from bs4 import BeautifulSoup

# ================= CONFIGURACIÓN =================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Lista con tus 11 artículos:
PRODUCTOS = [
    {
        "nombre": "TSG - Nintendo Switch 2 Edición Zelda",
        "url": "https://theshopgamer.com/es/consolas-switch-2/21472-consola-nintendo-switch-2-edicion-especial-zelda-40-aniversario-version-espanola-garantia-europea-european-warranty-0045496337292.html"
    },
    {
        "nombre": "TSG - Funda Zelda 40 Aniversario",
        "url": "https://theshopgamer.com/es/accesorios-switch-2/21559-funda-y-protector-de-pantalla-de-para-nintendo-switch-2-edicion-limitada-the-legend-of-zelda-40-aniversario-version-espanola-0045496322052.html"
    },
    {
        "nombre": "TSG - Mando Zelda 40 Aniversario con Batería Extraíble",
        "url": "https://theshopgamer.com/es/accesorios-switch-2/21587-nintendo-switch-2-pro-controller-edicion-limitada-the-legend-of-zelda-40-aniversario-btr-bateria-extraible-para-nintendo-switch2-0045496322229.html"
    },
    {
        "nombre": "TSG - Mando Zelda 40 Aniversario",
        "url": "https://theshopgamer.com/es/accesorios-switch-2/21558-nintendo-switch-2-pro-controller-edicion-limitada-the-legend-of-zelda-40-aniversario-para-nintendo-switch-2-version-espanola-0045496322045.html"
    },
    {
        "nombre": "XTRALIFE - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.xtralife.com/producto/nintendo-switch-2-edicion-the-legend-of-zelda-40-aniversario-switch-2-edicion-especial/113185"
    },
    {
        "nombre": "XTRALIFE - Funda Zelda 40 Aniversario",
        "url": "https://www.xtralife.com/producto/funda-de-transporte-nintendo-switch-2-zelda-40-aniversario-switch-2/113180"
    },
    {
        "nombre": "XTRALIFE - Mando Zelda 40 Aniversario",
        "url": "https://www.xtralife.com/producto/nintendo-switch-2-pro-controller-zelda-40-aniversario-switch-2/113184"
    },
    {
        "nombre": "TODOCONSOLA - Mando Zelda 40 Aniversario",
        "url": "https://www.todoconsolas.com/accesorios-switch-2/215838-mando_pro_controller_edicion_zelda_40_aniversario_btr_switch_2_280598-045496322229.html"
    },
    {
        "nombre": "IMPACT - Funda Zelda 40 Aniversario",
        "url": "https://impactgame.es/producto/reserva-funda-de-transporte-nintendo-switch-2-zelda-40o-aniversario/"
    },
    {
        "nombre": "IMPACT - Mando Zelda 40 Aniversario",
        "url": "https://impactgame.es/producto/reserva-mando-pro-nintendo-switch-2-the-legend-of-zelda-40o-aniversario/"
    },
    {
        "nombre": "COOL - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.coolmod.com/nintendo-switch-2-edicion-especial-the-legend-of-zelda-40th-aniversario-256gb/"
    }
]
# =================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def avisar_telegram(mensaje):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        requests.post(url_api, json=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar Telegram: {e}")

def verificar_articulo(producto):
    nombre = producto["nombre"]
    url = producto["url"]

    # Si todavía no has pegado el enlace real, salta este artículo sin dar error
    if "PEGA_AQUI" in url:
        return False

    try:
        respuesta = requests.get(url, headers=HEADERS, timeout=15)
        if respuesta.status_code != 200:
            print(f"[{nombre}] Respuesta no válida (HTTP {respuesta.status_code}).")
            return False

        html = respuesta.text.lower()

        # 1. Filtro anti-falsos positivos: si salta pantalla de verificación, ignorar
        if "cf-browser-verification" in html or "challenge-platform" in html or "just a moment" in html:
            print(f"[{nombre}] Pantalla de verificación anti-bot detectada. Saltando.")
            return False

        soup = BeautifulSoup(respuesta.text, "html.parser")

        # 2. Localizar el botón de compra
        boton_compra = soup.find("button", {"data-button-action": "add-to-cart"})
        if not boton_compra:
            print(f"[{nombre}] Botón de compra no encontrado en la página. Sigue en espera.")
            return False

        # 3. Comprobar si el botón está desactivado
        esta_desactivado = boton_compra.has_attr("disabled") or "disabled" in boton_compra.get("class", [])

        # 4. Comprobar mensaje de disponibilidad
        bloque_stock = soup.find(id="product-availability")
        texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
        palabras_agotado = ["agotado", "no disponible", "sin stock", "fuera de stock"]
        dice_agotado = any(p in texto_stock for p in palabras_agotado)

        # 5. SOLO avisa si el botón está físicamente activo Y no indica agotado
        if not esta_desactivado and not dice_agotado:
            print(f"¡¡¡STOCK REAL DETECTADO EN: {nombre}!!!")
            mensaje = (
                f"🚨 <b>¡HAY STOCK REAL!</b> 🚨\n\n"
                f"<b>Artículo:</b> {nombre}\n"
                f"<b>Enlace de compra:</b>\n{url}"
            )
            avisar_telegram(mensaje)
            return True
        else:
            print(f"[{nombre}] Sigue agotado.")
            return False

    except Exception as e:
        print(f"[{nombre}] Error de red: {e}")
        return False

# Realiza 3 rondas completas para los 11 productos
for ronda in range(3):
    hora = time.strftime("%H:%M:%S")
    print(f"\n--- [{hora}] Ronda {ronda + 1}/3 ---")
    
    for prod in PRODUCTOS:
        verificar_articulo(prod)
        time.sleep(2)  # Pausa de 2 segundos entre artículo y artículo

    if ronda < 2:
        time.sleep(25)
