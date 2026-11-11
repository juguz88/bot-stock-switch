import os
import sys
import time
import random
import re
from curl_cffi import requests
from bs4 import BeautifulSoup

# ================= CONFIGURACIÓN =================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MODO_PRUEBA = os.environ.get("MODO_PRUEBA", "false").lower() == "true"

HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    "Accept-Language": "es-ES,es;q=0.9"
}

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

avisados_en_este_turno = set()

def avisar_telegram(mensaje, url_compra=None):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    if url_compra:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": "🛒 ABRIR TIENDA Y COMPRAR", "url": url_compra}]]
        }

    for intento in range(2):
        try:
            r = requests.post(url_api, json=payload, timeout=10)
            if r.status_code == 200:
                break
        except Exception as e:
            print(f"Error al enviar Telegram (intento {intento + 1}): {e}")
            time.sleep(1)

def verificar_articulo(sesion, producto):
    nombre = producto["nombre"]
    url = producto["url"]

    try:
        respuesta = sesion.get(url, headers=HEADERS, timeout=8)

        if respuesta.status_code != 200:
            print(f"[{nombre}] HTTP {respuesta.status_code}. Saltando.")
            return False

        html = respuesta.text.lower()

        if "cf-browser-verification" in html or "challenge-platform" in html or "just a moment" in html:
            print(f"[{nombre}] Pantalla anti-bot temporal. Saltando.")
            return False

        soup = BeautifulSoup(respuesta.text, "html.parser")
        hay_stock = False

        # 1. Regla The Shop Gamer (PrestaShop)
        if "theshopgamer.com" in url:
            boton = soup.find("button", {"data-button-action": "add-to-cart"})
            bloque_stock = soup.find(id="product-availability")
            texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
            desactivado = boton.has_attr("disabled") if boton else True
            dice_agotado = any(p in texto_stock for p in ["agotado", "no disponible", "sin stock", "fuera de stock"])
            if boton and not desactivado and not dice_agotado:
                hay_stock = True

        # 2. Regla Impact Game (WooCommerce - Acotado a la ficha principal)
        elif "impactgame.es" in url:
            ficha = soup.find("div", class_=re.compile(r"summary|product-info|product-main", re.I)) or soup
            boton = ficha.find("button", {"name": "add-to-cart"}) or ficha.find(class_=re.compile(r"single_add_to_cart_button", re.I))
            etiqueta_agotado = ficha.find(class_=re.compile(r"out-of-stock", re.I))
            texto_ficha = etiqueta_agotado.get_text(strip=True).lower() if etiqueta_agotado else ""
            dice_sin_stock = any(p in texto_ficha for p in ["sin existencias", "agotado", "fuera de stock"])
            clases_boton = " ".join(boton.get("class", [])).lower() if boton else ""
            desactivado = (boton.has_attr("disabled") or "disabled" in clases_boton) if boton else True
            if boton and not desactivado and not dice_sin_stock:
                hay_stock = True

        # 3. Regla Xtralife (Acotado al botón de compra/reserva)
        elif "xtralife.com" in url:
            boton_compra = soup.find(["button", "a"], class_=re.compile(r"btn-buy|btn-reserve|add-to-cart", re.I))
            if boton_compra:
                texto_boton = boton_compra.get_text(strip=True).lower()
                clases_boton = " ".join(boton_compra.get("class", [])).lower()
                desactivado = boton_compra.has_attr("disabled") or "disabled" in clases_boton
                es_avisador = any(p in texto_boton for p in ["avísame", "avisadme", "agotado", "sin stock", "no disponible"])
                if not desactivado and not es_avisador:
                    hay_stock = True

        if hay_stock:
            print(f"¡¡¡STOCK REAL CONFIRMADO EN: {nombre}!!!")
            if url not in avisados_en_este_turno:
                mensaje = (
                    f"🚨 <b>¡HAY STOCK CONFIRMADO!</b> 🚨\n\n"
                    f"🎮 <b>{nombre}</b>\n\n"
                    f"🔗 {url}"
                )
                avisar_telegram(mensaje, url_compra=url)
                avisados_en_este_turno.add(url)
            return True
        else:
            print(f"[{nombre}] Sigue agotado.")
            return False

    except Exception as e:
        print(f"[{nombre}] Error de conexión: {e}")
        return False

# Si activaste la casilla de prueba manual en GitHub, manda confirmación a Telegram
if MODO_PRUEBA:
    print("Enviando mensaje de prueba a Telegram...")
    avisar_telegram(
        "✅ <b>Bot Switch 2 operativo</b>\n\n"
        "La conexión con Telegram funciona correctamente y los 9 artículos están bajo vigilancia.",
        url_compra="https://theshopgamer.com"
    )

total_rondas = 1 if MODO_PRUEBA else 3

with requests.Session(impersonate="chrome124") as sesion:
    for ronda in range(total_rondas):
        hora = time.strftime("%H:%M:%S")
        print(f"\n--- [{hora}] Ronda {ronda + 1}/{total_rondas} ---")

        for prod in PRODUCTOS:
            verificar_articulo(sesion, prod)
            time.sleep(random.uniform(1.2, 2.6))

        if ronda < total_rondas - 1:
            time.sleep(20)
