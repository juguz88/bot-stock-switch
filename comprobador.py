import os
import sys
import time
import requests
from bs4 import BeautifulSoup

# ================= CONFIGURACIÓN =================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Lista con tus 7 artículos:
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
            print(f"[{nombre}] Error HTTP {respuesta.status_code}")
            return False

        soup = BeautifulSoup(respuesta.text, "html.parser")
        bloque_stock = soup.find(id="product-availability")
        texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
        boton_compra = soup.find("button", {"data-button-action": "add-to-cart"})
        texto_completo = soup.get_text().lower()

        palabras_agotado = ["agotado", "no disponible", "sin stock", "fuera de stock"]
        esta_agotado = any(p in texto_stock for p in palabras_agotado) or any(p in texto_completo for p in palabras_agotado)
        boton_disponible = boton_compra and not boton_compra.has_attr("disabled")

        if boton_disponible or not esta_agotado:
            print(f"¡¡¡HAY STOCK DETECTADO EN: {nombre}!!!")
            mensaje = (
                f"🚨 <b>¡HAY STOCK DETECTADO!</b> 🚨\n\n"
                f"<b>Artículo:</b> {nombre}\n"
                f"<b>Enlace de compra:</b>\n{url}"
            )
            avisar_telegram(mensaje)
            return True
        else:
            print(f"[{nombre}] Sigue agotado.")
            return False

    except Exception as e:
        print(f"[{nombre}] Error al consultar: {e}")
        return False

# Realiza 4 rondas de revisión espaciadas 35 segundos (~2 minutos y 45 segundos en total)
for ronda in range(4):
    hora = time.strftime("%H:%M:%S")
    print(f"\n--- [{hora}] Ronda {ronda + 1}/4 ---")
    
    for prod in PRODUCTOS:
        verificar_articulo(prod)
        time.sleep(2)  # Pausa de cortesía de 2 segundos entre artículo y artículo

    if ronda < 3:
        time.sleep(35)
