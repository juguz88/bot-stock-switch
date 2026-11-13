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
PROXY_URL = os.environ.get("PROXY_URL")
MODO_PRUEBA = os.environ.get("MODO_PRUEBA", "false").lower() == "true"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.es/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1"
}

PRODUCTOS = [
    # --- TIENDAS SIN BLOQUEO (usar_proxy: False -> 100% GRATIS) ---
    {
        "nombre": "TSG - Nintendo Switch 2 Edición Zelda",
        "url": "https://theshopgamer.com/es/consolas-switch-2/21472-consola-nintendo-switch-2-edicion-especial-zelda-40-aniversario-version-espanola-garantia-europea-european-warranty-0045496337292.html",
        "usar_proxy": False
    },
    {
        "nombre": "TSG - Funda Zelda 40 Aniversario",
        "url": "https://theshopgamer.com/es/accesorios-switch-2/21559-funda-y-protector-de-pantalla-de-para-nintendo-switch-2-edicion-limitada-the-legend-of-zelda-40-aniversario-version-espanola-0045496322052.html",
        "usar_proxy": False
    },
    {
        "nombre": "TSG - Mando Zelda 40 Aniversario con Batería Extraíble",
        "url": "https://theshopgamer.com/es/accesorios-switch-2/21587-nintendo-switch-2-pro-controller-edicion-limitada-the-legend-of-zelda-40-aniversario-btr-bateria-extraible-para-nintendo-switch2-0045496322229.html",
        "usar_proxy": False
    },
    {
        "nombre": "TSG - Mando Zelda 40 Aniversario",
        "url": "https://theshopgamer.com/es/accesorios-switch-2/21558-nintendo-switch-2-pro-controller-edicion-limitada-the-legend-of-zelda-40-aniversario-para-nintendo-switch-2-version-espanola-0045496322045.html",
        "usar_proxy": False
    },
    {
        "nombre": "XTRALIFE - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.xtralife.com/producto/nintendo-switch-2-edicion-the-legend-of-zelda-40-aniversario-switch-2-edicion-especial/113185",
        "usar_proxy": False
    },
    {
        "nombre": "XTRALIFE - Funda Zelda 40 Aniversario",
        "url": "https://www.xtralife.com/producto/funda-de-transporte-nintendo-switch-2-zelda-40-aniversario-switch-2/113180",
        "usar_proxy": False
    },
    {
        "nombre": "XTRALIFE - Mando Zelda 40 Aniversario",
        "url": "https://www.xtralife.com/producto/nintendo-switch-2-pro-controller-zelda-40-aniversario-switch-2/113184",
        "usar_proxy": False
    },
    {
        "nombre": "IMPACT - Funda Zelda 40 Aniversario",
        "url": "https://impactgame.es/producto/reserva-funda-de-transporte-nintendo-switch-2-zelda-40o-aniversario/",
        "usar_proxy": False
    },
    {
        "nombre": "IMPACT - Mando Zelda 40 Aniversario",
        "url": "https://impactgame.es/producto/reserva-mando-pro-nintendo-switch-2-the-legend-of-zelda-40o-aniversario/",
        "usar_proxy": False
    },
    {
        "nombre": "TodoCon. - Mando Zelda 40 Aniversario",
        "url": "https://www.todoconsolas.com/accesorios-switch-2/215838-mando_pro_controller_edicion_zelda_40_aniversario_btr_switch_2_280598-045496322229.html",
        "usar_proxy": False
    },

    # --- GRANDES SUPERFICIES (usar_proxy: True -> CON PROXY ESPAÑOL) ---
    {
        "nombre": "ECI - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.elcorteingles.es/videojuegos/A202302815-nintendo-switch-2-edicion-zelda-40-aniversario/",
        "usar_proxy": True
    },
    {
        "nombre": "MediaMarkt - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.mediamarkt.es/es/product/_consola-nintendo-switch-2-edicion-zelda-40-aniversario-79-full-hd-hdr-120-hz-256-gb-magnetic-joy-con-2-con-modo-raton-1674231.html",
        "usar_proxy": True
    },
    {
        "nombre": "MediaMarkt - Funda Zelda 40 Aniversario",
        "url": "https://www.mediamarkt.es/es/product/_funda-protector-pantalla-nintendo-case-edicion-zelda-40-aniversario-para-nintendo-switch-2-1674234.html",
        "usar_proxy": True
    },
    {
        "nombre": "MediaMarkt - Mando Zelda 40 Aniversario",
        "url": "https://www.mediamarkt.es/es/product/_mando-nintendo-switch-2-nintendo-pro-edicion-zelda-40-aniversario-para-nintendo-switch-2-bluetooth-vibracion-hd-2-boton-c-para-gamechat-1674233.html",
        "usar_proxy": True
    },
    {
        "nombre": "GAME - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.game.es/nintendo-switch-2-edicion-zelda-40th/267689",
        "usar_proxy": True
    },
    {
        "nombre": "GAME - Mando Zelda 40 Aniversario",
        "url": "https://www.game.es/nintendo-switch-2-pro-controller-edicion-zelda-40th/269139",
        "usar_proxy": True
    },
    {
        "nombre": "GAME - Mando Zelda 40 Aniversario (Day One)",
        "url": "https://www.game.es/nintendo-switch-2-pro-controller-edicion-zelda-40th-day-one/267690",
        "usar_proxy": True
    },
    {
        "nombre": "GAME - Funda Zelda 40 Aniversario",
        "url": "https://www.game.es/funda-y-protector-de-pantalla-edicion-zelda-40th/267691",
        "usar_proxy": True
    },
    {
        "nombre": "PC Comp. - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.pccomponentes.com/nintendo-switch-2-7-9-fullhd-hdr-120hz-256gb-the-legend-of-zelda-40-aniversario-edition",
        "usar_proxy": True
    },
    {
        "nombre": "PC Comp. - Mando Zelda 40 Aniversario",
        "url": "https://www.pccomponentes.com/mando-pro-nintendo-switch-2-zelda-40-aniversario-edicion-especial",
        "usar_proxy": True
    },
    {
        "nombre": "PC Comp. - Funda Zelda 40 Aniversario",
        "url": "https://www.pccomponentes.com/funda-de-transporte-nintendo-switch-2-zelda-40-aniversario",
        "usar_proxy": True
    },
    {
        "nombre": "COOL - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.coolmod.com/nintendo-switch-2-edicion-especial-the-legend-of-zelda-40th-aniversario-256gb/",
        "usar_proxy": True
    },
    {
        "nombre": "Carrefour - Funda Zelda 40 Aniversario",
        "url": "https://www.carrefour.es/funda-y-protector-de-pantalla-nintendo-switch-2-edicion-zelda-40-aniversario/VC4A-34646850/p",
        "usar_proxy": True
    },
    {
        "nombre": "Nintendo - Nintendo Switch 2 Edición Zelda",
        "url": "https://store.nintendo.com/es-es/nintendo-switch-2-edicin-40-aniversario-de-the-legend-of-zelda-P00211",
        "usar_proxy": True
    },
    {
        "nombre": "Nintendo - Mando Zelda 40 Aniversario",
        "url": "https://store.nintendo.com/es-es/mando-pro-de-nintendo-switch-2-the-legend-of-zelda-edicin-40-aniversario-soporte-expositor-000000000010019437",
        "usar_proxy": True
    },
    {
        "nombre": "Nintendo - Funda Zelda 40 Aniversario",
        "url": "https://store.nintendo.com/es-es/funda-edicin-40-aniversario-de-the-legend-of-zelda-y-protector-de-pantalla-de-nintendo-switch-2-000000000010019439",
        "usar_proxy": True
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

def boton_esta_activo(boton):
    if not boton:
        return False
    clases = " ".join(boton.get("class", [])).lower()
    if boton.has_attr("disabled") or "disabled" in clases or "out-of-stock" in clases:
        return False
    texto = boton.get_text(strip=True).lower()
    palabras_compra = ["comprar", "reservar", "añadir", "cesta", "carrito"]
    palabras_agotado = ["agotado", "sin stock", "no disponible", "avísame", "avisarme", "avisadme", "sin existencias", "registrar"]
    tiene_accion = any(p in texto for p in palabras_compra)
    esta_agotado = any(p in texto for p in palabras_agotado)
    return tiene_accion and not esta_agotado

def verificar_articulo(sesion, producto):
    nombre = producto["nombre"]
    url = producto["url"]
    requiere_proxy = producto.get("usar_proxy", False)

    proxies_peticion = {"http": PROXY_URL, "https": PROXY_URL} if (requiere_proxy and PROXY_URL) else None

    if requiere_proxy and not PROXY_URL:
        print(f"[{nombre}] Aviso: requiere proxy pero PROXY_URL no está configurado.")
        return False

    try:
        if requiere_proxy:
            # PcComponentes y Carrefour abren mejor entrando directamente con perfil Safari
            navegador = "safari17_0" if any(t in url for t in ["pccomponentes.com", "carrefour.es"]) else "chrome124"
            respuesta = requests.get(url, headers=HEADERS, proxies=proxies_peticion, impersonate=navegador, timeout=12)
            if respuesta.status_code == 403:
                time.sleep(1)
                navegador_alt = "chrome124" if navegador == "safari17_0" else "safari17_0"
                respuesta = requests.get(url, headers=HEADERS, proxies=proxies_peticion, impersonate=navegador_alt, timeout=12)
        else:
            respuesta = sesion.get(url, headers=HEADERS, timeout=12)
            if respuesta.status_code in [403, 429, 503] and PROXY_URL:
                proxies_emergencia = {"http": PROXY_URL, "https": PROXY_URL}
                respuesta = requests.get(url, headers=HEADERS, proxies=proxies_emergencia, impersonate="chrome124", timeout=12)

        if respuesta.status_code != 200:
            print(f"[{nombre}] HTTP {respuesta.status_code}. Saltando.")
            return False

        html = respuesta.text.lower()
        soup = BeautifulSoup(respuesta.text, "html.parser")
        titulo_pagina = soup.title.get_text(strip=True).lower() if soup.title else ""

        # Comprobación precisa de pantallas de bloqueo reales (sin falsas alarmas por scripts de fondo)
        es_bloqueo_titulo = any(b in titulo_pagina for b in ["just a moment", "un momento", "access denied", "attention required", "you have been blocked"])
        es_bloqueo_corto = len(html) < 15000 and any(b in html for b in ["captcha-delivery.com", "cf-browser-verification"])

        if es_bloqueo_titulo or es_bloqueo_corto:
            print(f"[{nombre}] Pantalla anti-bot temporal. Saltando.")
            return False

        hay_stock = False

        # 1. Regla PrestaShop (The Shop Gamer, TodoConsolas)
        if any(t in url for t in ["theshopgamer.com", "todoconsolas.com"]):
            boton = soup.find("button", {"data-button-action": "add-to-cart"}) or soup.find("button", id="add_to_cart") or soup.find("button", class_=re.compile(r"add-to-cart", re.I))
            bloque_stock = soup.find(id="product-availability") or soup.find(id="availability_statut")
            texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
            clases_boton = " ".join(boton.get("class", [])).lower() if boton else ""
            desactivado = (boton.has_attr("disabled") or "disabled" in clases_boton) if boton else True
            dice_agotado = any(p in texto_stock for p in ["agotado", "no disponible", "sin stock", "fuera de stock", "avísame"])
            if boton and not desactivado and not dice_agotado:
                hay_stock = True

        # 2. Regla WooCommerce (Impact Game)
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

        # 3. Regla Xtralife
        elif "xtralife.com" in url:
            boton_compra = soup.find(["button", "a"], class_=re.compile(r"btn-buy|btn-reserve|add-to-cart", re.I))
            if boton_esta_activo(boton_compra):
                hay_stock = True

        # 4. Regla GAME España
        elif "game.es" in url:
            panel_compra = soup.find("div", class_=re.compile(r"buy-panel|product-buy", re.I)) or soup
            boton = panel_compra.find(["a", "button"], class_=re.compile(r"btn-buy|buy-button|cm-btn-buy", re.I))
            if boton_esta_activo(boton):
                hay_stock = True

        # 5. Regla Grandes Superficies y My Nintendo Store (ECI, MediaMarkt, PcComponentes, Coolmod, Carrefour, Nintendo)
        elif any(t in url for t in ["elcorteingles.es", "mediamarkt.es", "pccomponentes.com", "coolmod.com", "carrefour.es", "store.nintendo.com"]):
            botones_candidatos = soup.find_all(
                ["button", "a"],
                attrs={"id": re.compile(r"add-cart|add-to-cart|buy-button|pdp-add", re.I)}
            ) + soup.find_all(
                ["button", "a"],
                class_=re.compile(r"add-to-cart|add-to-basket|buy-button|btn-buy|js-add-to-cart|c_button--primary", re.I)
            ) + soup.find_all(
                "button",
                attrs={"data-test": re.compile(r"a2c-Button|add-to-cart", re.I)}
            )
            for b in botones_candidatos:
                if boton_esta_activo(b):
                    hay_stock = True
                    break

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

if MODO_PRUEBA:
    estado_proxy = "Conectado y listo" if PROXY_URL else "No configurado (modo gratuito activo)"
    print("Enviando mensaje de prueba a Telegram...")
    avisar_telegram(
        f"✅ <b>Bot Switch 2 operativo</b>\n\n"
        f"📡 <b>Estado del Proxy:</b> {estado_proxy}\n"
        f"🛡️ Vigilando {len(PRODUCTOS)} artículos correctamente.",
        url_compra="https://theshopgamer.com"
    )

total_rondas = 1 if MODO_PRUEBA else 2

with requests.Session(impersonate="chrome124") as sesion:
    for ronda in range(total_rondas):
        hora = time.strftime("%H:%M:%S")
        print(f"\n--- [{hora}] Ronda {ronda + 1}/{total_rondas} ---")

        for prod in PRODUCTOS:
            verificar_articulo(sesion, prod)
            time.sleep(random.uniform(0.8, 1.5))

        if ronda < total_rondas - 1:
            time.sleep(15)
