import os
import sys
import time
import re
from curl_cffi import requests
from bs4 import BeautifulSoup

# ================= CONFIGURACIÓN =================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PRODUCTOS = [
    # --- The Shop Gamer ---
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
    # --- Xtralife ---
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
    # --- Impact Game ---
    {
        "nombre": "IMPACT - Funda Zelda 40 Aniversario",
        "url": "https://impactgame.es/producto/reserva-funda-de-transporte-nintendo-switch-2-zelda-40o-aniversario/"
    },
    {
        "nombre": "IMPACT - Mando Zelda 40 Aniversario",
        "url": "https://impactgame.es/producto/reserva-mando-pro-nintendo-switch-2-the-legend-of-zelda-40o-aniversario/"
    }
]
# =================================================

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

    try:
        respuesta = requests.get(url, impersonate="chrome124", timeout=8)
        
        if respuesta.status_code != 200:
            print(f"[{nombre}] HTTP {respuesta.status_code}. Saltando.")
            return False

        html = respuesta.text.lower()

        # Filtro de pantallas anti-bot
        if "cf-browser-verification" in html or "challenge-platform" in html or "just a moment" in html:
            print(f"[{nombre}] Pantalla anti-bot temporal. Saltando.")
            return False

        soup = BeautifulSoup(respuesta.text, "html.parser")
        hay_stock = True

        # 1. Regla The Shop Gamer (PrestaShop)
        if "theshopgamer.com" in url:
            boton = soup.find("button", {"data-button-action": "add-to-cart"})
            bloque_stock = soup.find(id="product-availability")
            texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
            desactivado = boton.has_attr("disabled") if boton else True
            dice_agotado = any(p in texto_stock for p in ["agotado", "no disponible", "sin stock", "fuera de stock"])
            if boton and not desactivado and not dice_agotado:
                hay_stock = True

        # 2. Regla Impact Game (WooCommerce)
        elif "impactgame.es" in url:
            boton = soup.find("button", {"name": "add-to-cart"}) or soup.find(class_=re.compile(r"single_add_to_cart_button", re.I))
            texto_general = soup.get_text().lower()
            dice_sin_stock = "sin existencias" in texto_general or "agotado" in texto_general
            desactivado = boton.has_attr("disabled") if boton else True
            if boton and not desactivado and not dice_sin_stock:
                hay_stock = True

        # 3. Regla Xtralife
        elif "xtralife.com" in url:
            texto_general = soup.get_text().lower()
            boton_compra = soup.find(["button", "a"], class_=re.compile(r"btn-buy|btn-reserve|add-to-cart", re.I))
            dice_agotado = any(p in texto_general for p in ["avísame cuando esté disponible", "avisadme", "sin stock", "no disponible"])
            if boton_compra and not dice_agotado:
                hay_stock = True

        if hay_stock:
            print(f"¡¡¡STOCK REAL CONFIRMADO EN: {nombre}!!!")
            mensaje = (
                f"🚨 <b>¡HAY STOCK CONFIRMADO!</b> 🚨\n\n"
                f"<b>Artículo:</b> {nombre}\n"
                f"<b>Enlace de compra:</b>\n{url}"
            )
            avisar_telegram(mensaje)
            return True
        else:
            print(f"[{nombre}] Sigue agotado.")
            return False

    except Exception as e:
        print(f"[{nombre}] Error de conexión: {e}")
        return False

# 3 rondas completas para los 9 productos
for ronda in range(3):
    hora = time.strftime("%H:%M:%S")
    print(f"\n--- [{hora}] Ronda {ronda + 1}/3 ---")
    
    for prod in PRODUCTOS:
        verificar_articulo(prod)
        time.sleep(2)

    if ronda < 2:
        time.sleep(20)
