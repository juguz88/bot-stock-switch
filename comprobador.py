import os
import sys
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://theshopgamer.com/es/consolas-switch-2/21472-consola-nintendo-switch-2-edicion-especial-zelda-40-aniversario-version-espanola-garantia-europea-european-warranty-0045496337292.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}

def avisar_telegram(mensaje):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    requests.post(url_api, json=payload, timeout=10)

try:
    respuesta = requests.get(URL, headers=HEADERS, timeout=15)
    if respuesta.status_code != 200:
        print(f"Error HTTP: {respuesta.status_code}")
        sys.exit(0)

    soup = BeautifulSoup(respuesta.text, "html.parser")
    avisar_telegram("🧪 <b>Prueba de conexión:</b> ¡El bot funciona y te notificará aquí!")
    
    bloque_stock = soup.find(id="product-availability")
    texto_stock = bloque_stock.get_text(strip=True).lower() if bloque_stock else ""
    boton_compra = soup.find("button", {"data-button-action": "add-to-cart"})
    texto_completo = soup.get_text().lower()
    
    palabras_agotado = ["agotado", "no disponible", "sin stock", "fuera de stock"]
    esta_agotado = any(p in texto_stock for p in palabras_agotado) or any(p in texto_completo for p in palabras_agotado)
    boton_disponible = boton_compra and not boton_compra.has_attr("disabled")

    if boton_disponible or not esta_agotado:
        print("¡¡¡HAY STOCK DETECTADO!!! Enviando alerta...")
        mensaje = (
            "🚨 <b>¡HAY STOCK DE LA NINTENDO SWITCH 2 ZELDA!</b> 🚨\n\n"
            f"Corre a comprarla aquí:\n{URL}"
        )
        avisar_telegram(mensaje)
    else:
        print("Comprobación terminada: Sigue sin stock.")

except Exception as e:
    print(f"Error durante la comprobación: {e}")
