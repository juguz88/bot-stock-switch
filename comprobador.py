import os
import sys
import time
import random
import re
import json
import string
import threading
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
    ZONA_MADRID = ZoneInfo("Europe/Madrid")
except Exception:
    ZONA_MADRID = timezone(timedelta(hours=1))

# ================= CONFIGURACIÓN =================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PROXY_URL = os.environ.get("PROXY_URL", "").strip()
MODO_PRUEBA = False

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
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
    {
        "nombre": "Videodis - Nintendo Switch 2 Edición Zelda",
        "url": "https://videodis.es/consolas/50622-preventa-consiola-nintendo-switch-2-disponible-el-05062025.html",
        "usar_proxy": False
    },
    {
        "nombre": "Videodis - Mando Zelda 40 Aniversario",
        "url": "https://videodis.es/juegos/50076-reserva-funda-y-protector-de-pantalla-edicion-zelda-40th-switch-2-disponible-el-29102026.html",
        "usar_proxy": False
    },
    {
        "nombre": "Videodis - Funda Zelda 40 Aniversario",
        "url": "https://videodis.es/juegos/50075-reserva-funda-y-protector-de-pantalla-edicion-zelda-40th-switch-2-disponible-el-29102026.html",
        "usar_proxy": False
    },
    {
        "nombre": "HíperOcio - Nintendo Switch 2 Edición Zelda",
        "url": "https://hiperocio.com/products/nintendo-switch-2-edicion-zelda-40-aniversario",
        "usar_proxy": False
    },
    {
        "nombre": "HíperOcio - Mando Zelda 40 Aniversario",
        "url": "https://hiperocio.com/products/mando-pro-nintendo-switch-2-zelda-40-aniversario",
        "usar_proxy": False
    },
    {
        "nombre": "Baba - Funda Zelda 40 Aniversario",
        "url": "https://www.baba.es/es/sw2-bolsa-transporte-protector-de-pantalla-zelda-40-aniversario/41903",
        "usar_proxy": False
    },
    {
        "nombre": "Baba - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.baba.es/es/sw-consola-nintendo-switch-2-/41902",
        "usar_proxy": False
    },
    {
        "nombre": "Baba - Mando Zelda 40 Aniversario (Ficha 1)",
        "url": "https://www.baba.es/es/sw2-mando-pro-wireless-resident-evil-requiem-edition/42352",
        "usar_proxy": False
    },
    {
        "nombre": "Baba - Mando Zelda 40 Aniversario (Ficha 2)",
        "url": "https://www.baba.es/es/sw2-mando-pro-wireless-resident-evil-requiem-edition/41901",
        "usar_proxy": False
    },

    # --- GRANDES SUPERFICIES (usar_proxy: True -> CON PROXY ESPAÑOL) ---
    {
        "nombre": "Amazon - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.amazon.es/dp/B0F2TN43GH",
        "usar_proxy": True
    },
    {
        "nombre": "Amazon - Mando Zelda 40 Aniversario",
        "url": "https://www.amazon.es/dp/B0F2T6WM33",
        "usar_proxy": True
    },
    {
        "nombre": "Amazon - Funda Zelda 40 Aniversario",
        "url": "https://www.amazon.es/dp/B0HJ89X1VQ",
        "usar_proxy": True
    },
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
    },
    {
        "nombre": "Caseking - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.caseking.es/consola-nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition/10019448.html",
        "usar_proxy": True
    },
    {
        "nombre": "Caseking - Mando Zelda 40 Aniversario",
        "url": "https://www.caseking.es/gamepad-nintendo-switch-2-pro-controller-the-legend-of-zelda-40th-anniversary-edition/10019438.html",
        "usar_proxy": True
    },
    {
        "nombre": "Caseking - Funda Zelda 40 Aniversario",
        "url": "https://www.caseking.es/bolsa-nintendo-switch-2-carrying-case-the-legend-of-zelda-40th-anniversary-edition/10019439.html",
        "usar_proxy": True
    },
    {
        "nombre": "Mielectro - Nintendo Switch 2 Edición Zelda",
        "url": "https://www.mielectro.es/nintendo-switch-2-edicion-legend-of-zelda-31391071/",
        "usar_proxy": True
    }
]
# =================================================

avisados_en_este_turno = set()
candado_stats = threading.Lock()
candado_telegram = threading.Lock()
candados_dominio = {}
ultimo_acceso_dominio = {}
candado_maestro_dominios = threading.Lock()

stats = {
    "revisados_ok": 0,
    "gratis_ok": 0,
    "proxy_ok": 0,
    "reintentos_recuperados": 0,
    "errores_proxy_407": 0,
    "errores_red_proxy": 0,
    "antibot": 0
}

def esperar_turno_dominio(url):
    dominio = urlparse(url).netloc.lower()
    with candado_maestro_dominios:
        if dominio not in candados_dominio:
            candados_dominio[dominio] = threading.Lock()
        lock_dom = candados_dominio[dominio]

    lock_dom.acquire()
    try:
        ahora = time.time()
        ultimo = ultimo_acceso_dominio.get(dominio, 0)
        espera = random.uniform(0.9, 1.4) - (ahora - ultimo)
        if espera > 0:
            time.sleep(espera)
        ultimo_acceso_dominio[dominio] = time.time()
    finally:
        lock_dom.release()

def obtener_icono_categoria(nombre):
    n = nombre.lower()
    if "funda" in n or "bolsa" in n:
        return "🎒"
    elif "mando" in n or "controller" in n:
        return "🕹️"
    return "🎮"

def extraer_precio(soup, html_raw):
    try:
        meta_precio = (
            soup.find("meta", {"property": "product:price:amount"}) or
            soup.find("meta", {"property": "og:price:amount"}) or
            soup.find("meta", {"itemprop": "price"})
        )
        if meta_precio and meta_precio.get("content"):
            valor = meta_precio["content"].strip().replace(".", ",")
            if re.match(r"^\d+([.,]\d{1,2})?$", valor):
                return f"{valor} €"

        for script in soup.find_all("script", type="application/ld+json"):
            texto_json = script.string or ""
            m = re.search(r'"price"\s*:\s*"?(\d{2,3}(?:[.,]\d{1,2})?)"?', texto_json)
            if m:
                return f"{m.group(1).replace('.', ',')} €"

        m_euro = re.search(r'(\d{2,3}[.,]\d{2})\s*€', soup.get_text(" ", strip=True))
        if m_euro:
            return f"{m_euro.group(1)} €"
    except Exception:
        pass
    return "Ver en tienda"

def fijar_mensaje_telegram(message_id):
    url_pin = f"https://api.telegram.org/bot{TOKEN}/pinChatMessage"
    payload_pin = {
        "chat_id": CHAT_ID,
        "message_id": message_id,
        "disable_notification": False
    }
    try:
        requests.post(url_pin, json=payload_pin, timeout=10)
    except Exception as e:
        print(f"No se pudo fijar el mensaje en Telegram: {e}")

def enviar_un_mensaje_telegram(texto_mensaje, url_compra=None, url_cesta_directa=None):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": texto_mensaje,
        "parse_mode": "HTML",
        "disable_notification": False
    }
    if url_compra:
        botones = []
        if url_cesta_directa:
            botones.append([{"text": "⚡ AÑADIR DIRECTO A LA CESTA (1 CLIC)", "url": url_cesta_directa}])
        botones.append([{"text": "🛒 ABRIR TIENDA Y COMPRAR", "url": url_compra}])
        payload["reply_markup"] = {"inline_keyboard": botones}

    for intento in range(3):
        try:
            r = requests.post(url_api, json=payload, timeout=10)
            if r.status_code == 200:
                datos = r.json()
                return datos.get("result", {}).get("message_id")
            elif r.status_code == 429:
                time.sleep(2)
        except Exception as e:
            print(f"Error al enviar Telegram (intento {intento + 1}): {e}")
            time.sleep(1)
    return None

def avisar_telegram(mensaje, url_compra=None, url_cesta_directa=None, alarma_combate=False):
    with candado_telegram:
        if not alarma_combate:
            enviar_un_mensaje_telegram(mensaje, url_compra, url_cesta_directa)
            return

        primer_id = None
        for num_alerta in range(1, 4):
            encabezado_rafaga = f"🚨 <b>¡HAY STOCK CONFIRMADO! (Alerta {num_alerta}/3)</b> 🚨"
            mensaje_rafaga = mensaje.replace("🚨 <b>¡HAY STOCK CONFIRMADO!</b> 🚨", encabezado_rafaga)
            msg_id = enviar_un_mensaje_telegram(mensaje_rafaga, url_compra, url_cesta_directa)
            if num_alerta == 1 and msg_id:
                primer_id = msg_id
                fijar_mensaje_telegram(primer_id)
            if num_alerta < 3:
                time.sleep(3)

def elemento_oculto(elem):
    for p in [elem] + list(elem.parents):
        if not hasattr(p, "attrs") or not p.attrs:
            continue
        if p.name in ["template", "noscript", "script", "style"]:
            return True
        if p.has_attr("hidden") or p.get("aria-hidden") == "true":
            return True
        clases = " ".join(p.get("class", [])).lower()
        if any(c in clases.split() for c in ["hidden", "d-none", "hide", "invisible", "is-hidden", "uk-hidden"]):
            return True
        estilo = p.get("style", "").lower().replace(" ", "")
        if "display:none" in estilo or "visibility:hidden" in estilo:
            return True
    return False

def boton_esta_activo(boton):
    if not boton or elemento_oculto(boton):
        return False
    if boton.find_parent(class_=re.compile(r"related|recommend|upsell|cross-sell|carousel|slider|similar|accessories|bundle", re.I)):
        return False
    clases = " ".join(boton.get("class", [])).lower()
    if boton.has_attr("disabled") or "disabled" in clases or "out-of-stock" in clases or boton.get("aria-disabled") == "true":
        return False
    texto = (
        boton.get_text(" ", strip=True) + " " +
        boton.get("value", "") + " " +
        boton.get("title", "") + " " +
        boton.get("aria-label", "")
    ).lower()
    palabras_compra = ["comprar", "reservar", "añadir", "cesta", "carrito"]
    palabras_agotado = [
        "agotado", "sin stock", "no disponible", "avísame", "avisarme",
        "avisadme", "sin existencias", "registrar", "próximamente", "notificar"
    ]
    tiene_accion = any(p in texto for p in palabras_compra)
    esta_agotado = any(p in texto for p in palabras_agotado)
    return tiene_accion and not esta_agotado

def es_pantalla_antibot(html, titulo_pagina):
    es_bloqueo_titulo = any(b in titulo_pagina for b in [
        "just a moment", "un momento", "access denied",
        "attention required", "you have been blocked", "robot check"
    ])
    es_bloqueo_corto = len(html) < 15000 and any(b in html for b in [
        "captcha-delivery.com", "cf-browser-verification",
        "validatecaptcha", "api-services-support@amazon.com"
    ])
    return es_bloqueo_titulo or es_bloqueo_corto

def generar_proxy_rotado(proxy_base, intento):
    if not proxy_base:
        return None
    if intento == 0:
        return {"http": proxy_base, "https": proxy_base}

    nuevo_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    if "_session-" in proxy_base:
        proxy_mod = re.sub(r"_session-[a-zA-Z0-9]+", f"_session-{nuevo_id}", proxy_base)
    elif "_country-" in proxy_base:
        proxy_mod = re.sub(r"(_country-[a-zA-Z]{2})", rf"\1_session-{nuevo_id}_lifetime-1m", proxy_base, count=1)
    elif "@" in proxy_base:
        partes = proxy_base.rsplit("@", 1)
        proxy_mod = f"{partes[0]}_session-{nuevo_id}_lifetime-1m@{partes[1]}"
    else:
        proxy_mod = proxy_base
    return {"http": proxy_mod, "https": proxy_mod}

def realizar_peticion(url, requiere_proxy, proxy_base):
    max_intentos = 5 if requiere_proxy else 2
    ultimo_error = None
    headers_peticion = dict(HEADERS_BASE)
    if requiere_proxy:
        headers_peticion["Connection"] = "close"

    for intento in range(max_intentos):
        esperar_turno_dominio(url)
        try:
            if requiere_proxy:
                proxies_actuales = generar_proxy_rotado(proxy_base, intento)
                navegador = "safari17_0" if any(t in url for t in ["pccomponentes.com", "carrefour.es", "amazon.es", "caseking.es"]) else "chrome124"
                if intento % 2 == 1:
                    navegador = "chrome124" if navegador == "safari17_0" else "safari17_0"

                resp = requests.get(
                    url,
                    headers=headers_peticion,
                    proxies=proxies_actuales,
                    impersonate=navegador,
                    timeout=12
                )

                if resp.status_code >= 500 or resp.status_code == 403 or "validatecaptcha" in resp.text.lower():
                    if intento < max_intentos - 1:
                        time.sleep(1.2)
                        continue
                if intento > 0 and resp.status_code == 200:
                    with candado_stats:
                        stats["reintentos_recuperados"] += 1
                return resp
            else:
                resp = requests.get(url, headers=headers_peticion, impersonate="chrome124", timeout=12)
                if resp.status_code in [403, 429, 503] and proxy_base:
                    headers_emergencia = dict(HEADERS_BASE)
                    headers_emergencia["Connection"] = "close"
                    for sub_intento in range(2):
                        try:
                            proxies_emergencia = generar_proxy_rotado(proxy_base, sub_intento + 1)
                            resp = requests.get(url, headers=headers_emergencia, proxies=proxies_emergencia, impersonate="safari17_0", timeout=12)
                            if resp.status_code == 200:
                                with candado_stats:
                                    stats["reintentos_recuperados"] += 1
                                break
                        except Exception:
                            time.sleep(1.0)
                return resp
        except Exception as e:
            ultimo_error = e
            if intento < max_intentos - 1:
                time.sleep(1.2)

    # Salvavidas gratuito: si los 5 intentos con proxy fallan por caída de nodo (Error 500),
    # probamos 1 intento directo sin proxy antes de rendirnos
    if requiere_proxy:
        try:
            resp_directa = requests.get(url, headers=HEADERS_BASE, impersonate="safari17_0", timeout=10)
            if resp_directa.status_code == 200:
                with candado_stats:
                    stats["reintentos_recuperados"] += 1
                return resp_directa
        except Exception:
            pass

    if ultimo_error:
        raise ultimo_error

    class RespuestaVacia:
        status_code = 500
        text = ""
    return RespuestaVacia()

def verificar_articulo(producto):
    nombre = producto["nombre"]
    url = producto["url"]
    requiere_proxy = producto.get("usar_proxy", False)

    if requiere_proxy and not PROXY_URL:
        return f"[{nombre}] Aviso: requiere proxy pero PROXY_URL no está configurado."

    try:
        respuesta = realizar_peticion(url, requiere_proxy, PROXY_URL)

        if respuesta.status_code in [407, 402]:
            with candado_stats:
                stats["errores_proxy_407"] += 1
            return f"[{nombre}] Error {respuesta.status_code}: Proxy sin saldo o credenciales rechazadas."

        if respuesta.status_code != 200:
            return f"[{nombre}] HTTP {respuesta.status_code}. Saltando."

        html = respuesta.text.lower()
        soup = BeautifulSoup(respuesta.text, "html.parser")
        titulo_pagina = soup.title.get_text(strip=True).lower() if soup.title else ""

        if es_pantalla_antibot(html, titulo_pagina):
            if not requiere_proxy and PROXY_URL:
                headers_emergencia = dict(HEADERS_BASE)
                headers_emergencia["Connection"] = "close"
                for sub_intento in range(2):
                    try:
                        proxies_emergencia = generar_proxy_rotado(PROXY_URL, sub_intento + 1)
                        respuesta = requests.get(url, headers=headers_emergencia, proxies=proxies_emergencia, impersonate="safari17_0", timeout=12)
                        if respuesta.status_code == 200:
                            html = respuesta.text.lower()
                            soup = BeautifulSoup(respuesta.text, "html.parser")
                            titulo_pagina = soup.title.get_text(strip=True).lower() if soup.title else ""
                            if not es_pantalla_antibot(html, titulo_pagina):
                                with candado_stats:
                                    stats["reintentos_recuperados"] += 1
                                break
                    except Exception:
                        time.sleep(1.0)

            if es_pantalla_antibot(html, titulo_pagina):
                with candado_stats:
                    stats["antibot"] += 1
                return f"[{nombre}] Pantalla anti-bot temporal. Saltando."

        with candado_stats:
            stats["revisados_ok"] += 1
            if requiere_proxy:
                stats["proxy_ok"] += 1
            else:
                stats["gratis_ok"] += 1

        hay_stock = False

        # 1. Regla PrestaShop (The Shop Gamer, TodoConsolas, Videodis)
        if any(t in url for t in ["theshopgamer.com", "todoconsolas.com", "videodis.es"]):
            boton = soup.find("button", {"data-button-action": "add-to-cart"}) or soup.find("button", id="add_to_cart") or soup.find("button", class_=re.compile(r"add-to-cart", re.I))
            bloque_stock = soup.find(id="product-availability") or soup.find(id="availability_statut")
            texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
            clases_boton = " ".join(boton.get("class", [])).lower() if boton else ""
            desactivado = (boton.has_attr("disabled") or "disabled" in clases_boton or elemento_oculto(boton)) if boton else True
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
            desactivado = (boton.has_attr("disabled") or "disabled" in clases_boton or elemento_oculto(boton)) if boton else True
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

        # 5. Regla Amazon España
        elif "amazon.es" in url:
            caja_compra = soup.find("div", id=re.compile(r"desktop_buybox|buybox", re.I)) or soup
            boton_cesta = caja_compra.find(["input", "button"], id=re.compile(r"add-to-cart-button|buy-now-button", re.I))
            bloque_agotado = soup.find("div", id="outOfStock")
            ver_opciones = soup.find(id="buybox-see-all-buying-choices")
            if boton_cesta and not elemento_oculto(boton_cesta) and not bloque_agotado and not ver_opciones:
                hay_stock = True

        # 6. Regla Grandes Superficies, Shopify y Tiendas Especializadas
        elif any(t in url for t in ["elcorteingles.es", "mediamarkt.es", "pccomponentes.com", "coolmod.com", "carrefour.es", "store.nintendo.com", "caseking.es", "mielectro.es", "hiperocio.com", "baba.es"]):
            botones_candidatos = soup.find_all(
                ["button", "a", "input"],
                attrs={"id": re.compile(r"add-cart|add-to-cart|buy-button|pdp-add|btn-comprar", re.I)}
            ) + soup.find_all(
                ["button", "a", "input"],
                class_=re.compile(r"add-to-cart|add-to-basket|buy-button|btn-buy|btn-comprar|js-add-to-cart|c_button--primary|product-form__submit|add-cart", re.I)
            ) + soup.find_all(
                "button",
                attrs={"name": re.compile(r"^add$|add-to-cart", re.I)}
            ) + soup.find_all(
                "button",
                attrs={"data-test": re.compile(r"a2c-Button|add-to-cart", re.I)}
            )
            for b in botones_candidatos:
                if boton_esta_activo(b):
                    hay_stock = True
                    break

        if hay_stock:
            with candado_stats:
                ya_avisado = url in avisados_en_este_turno
                if not ya_avisado:
                    avisados_en_este_turno.add(url)

            if not ya_avisado:
                icono = obtener_icono_categoria(nombre)
                precio_detectado = extraer_precio(soup, respuesta.text)
                hora_es = datetime.now(ZONA_MADRID).strftime("%H:%M:%S")

                url_cesta_amazon = None
                if "amazon.es/dp/" in url:
                    asin = url.split("/dp/")[1].split("/")[0].split("?")[0]
                    url_cesta_amazon = f"https://www.amazon.es/gp/aws/cart/add.html?ASIN.1={asin}&Quantity.1=1"

                mensaje = (
                    f"🚨 <b>¡HAY STOCK CONFIRMADO!</b> 🚨\n\n"
                    f"{icono} <b>{nombre}</b>\n"
                    f"💰 <b>Precio detectado:</b> {precio_detectado}\n"
                    f"🕒 <b>Hora (ES):</b> {hora_es}\n\n"
                    f"🔗 {url}"
                )
                avisar_telegram(
                    mensaje,
                    url_compra=url,
                    url_cesta_directa=url_cesta_amazon,
                    alarma_combate=True
                )
            return f"¡¡¡STOCK REAL CONFIRMADO EN: {nombre}!!!"
        else:
            return f"[{nombre}] Sigue agotado."

    except Exception as e:
        err_texto = str(e).lower()
        if requiere_proxy and any(k in err_texto for k in ["407", "proxy", "connect", "tunnel"]):
            with candado_stats:
                stats["errores_red_proxy"] += 1
        return f"[{nombre}] Error de conexión tras 5 intentos: {e}"

# ================= EJECUCIÓN PRINCIPAL =================
inicio_barrido = time.time()
ahora_madrid = datetime.now(ZONA_MADRID)

if MODO_PRUEBA:
    estado_proxy = "Conectado y listo" if PROXY_URL else "No configurado (modo gratuito activo)"
    print("Enviando mensaje de prueba a Telegram...")
    avisar_telegram(
        f"✅ <b>Bot Switch 2 operativo</b>\n\n"
        f"📡 <b>Estado del Proxy:</b> {estado_proxy}\n"
        f"🛡️ Vigilando {len(PRODUCTOS)} artículos correctamente.",
        url_compra="https://theshopgamer.com"
    )

hora_log = ahora_madrid.strftime("%H:%M:%S")
print(f"\n--- [{hora_log} ES] Ronda 1/1 (Motor Paralelo 4x Activo) ---")

# Intercalamos tiendas distintas para maximizar la velocidad sin golpear el mismo dominio a la vez
resultados_ordenados = [None] * len(PRODUCTOS)
with ThreadPoolExecutor(max_workers=4) as executor:
    futuros = {executor.submit(verificar_articulo, prod): idx for idx, prod in enumerate(PRODUCTOS)}
    for futuro in as_completed(futuros):
        idx = futuros[futuro]
        try:
            resultados_ordenados[idx] = futuro.result()
        except Exception as exc:
            resultados_ordenados[idx] = f"[{PRODUCTOS[idx]['nombre']}] Error inesperado: {exc}"

for linea in resultados_ordenados:
    if linea:
        print(linea)

duracion_seg = int(time.time() - inicio_barrido)
print(f"\n--- Barrido completado en {duracion_seg}s | Verificados: {stats['revisados_ok']}/{len(PRODUCTOS)} (Recuperados en reintento: {stats['reintentos_recuperados']}) ---")

# 1. Alerta automática si el proxy de IPRoyal se queda sin megas (407) o cae al 100%
fallo_critico_proxy = stats["errores_proxy_407"] > 0 or (stats["proxy_ok"] == 0 and stats["errores_red_proxy"] >= 15)
if fallo_critico_proxy and (0 <= ahora_madrid.minute < 15):
    avisar_telegram(
        "⚠️ <b>¡ALERTA DE PROXY IPROYAL!</b> ⚠️\n\n"
        "El proxy no responde o <b>se te han agotado los megas del Giga</b>.\n"
        "Las 19 tiendas gratuitas siguen vigiladas, pero las 23 grandes superficies no pueden comprobarse hasta que revises tu saldo en IPRoyal."
    )

# 2. Informe diario de supervivencia en el turno de las 11:50 AM (ventana 11:45 a 11:59 hora de Madrid)
if ahora_madrid.hour == 11 and (45 <= ahora_madrid.minute <= 59):
    avisar_telegram(
        f"☀️ <b>Parte Diario (11:50): Bot Switch 2 en guardia</b>\n\n"
        f"🛡️ <b>Total tiendas verificadas:</b> {stats['revisados_ok']}/{len(PRODUCTOS)}\n"
        f"🆓 <b>Tiendas sin proxy:</b> {stats['gratis_ok']}/19 operativas\n"
        f"📡 <b>Grandes superficies (Proxy):</b> {stats['proxy_ok']}/23 operativas\n"
        f"🔄 <b>Nodos recuperados al vuelo:</b> {stats['reintentos_recuperados']}\n"
        f"⚡ <b>Tiempo récord de barrido:</b> {duracion_seg} segundos\n\n"
        f"<i>Seguimos vigilando en silencio con Alarma de Combate (x3 + mensaje fijado) activa.</i>"
    )
