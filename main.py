import os
import requests
from bs4 import BeautifulSoup

def send_telegram_alert(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    # Soporta múltiples IDs separados por coma
    chat_ids = os.getenv("TELEGRAM_CHAT_IDS").split(",") 
    
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id.strip(),
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload)

def check_availability():
    url = "https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/"
    target_sku = "TRINANEG18RC.27-500"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Busca todos los bloques de producto (clase estándar de WooCommerce)
    product_blocks = soup.find_all('li', class_=lambda x: x and 'product' in x.split())
    
    product_found = False
    is_available = False
    
    for block in product_blocks:
        if target_sku in block.get_text():
            product_found = True
            if "Añadir al carrito" in block.get_text():
                is_available = True
            break
            
    if not product_found:
        print("⚠️ Producto no encontrado. La estructura de la web pudo haber cambiado.")
        return

    if is_available:
        msg = (
            "🚨 *¡ALERTA DE DISPONIBILIDAD!*\n\n"
            "El *Panel Solar Bifacial TRINA SOLAR 500 WP*\n"
            "SKU: `TRINANEG18RC.27-500`\n"
            "ya está disponible para comprar.\n\n"
            "🔗 [Ver en Tienda Solar](https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/)"
        )
        send_telegram_alert(msg)
        print("✅ Alerta enviada exitosamente.")
    else:
        # 👇 CAMBIO: Enviar mensaje de estado cada vez que chequee
        msg_test = (
            " *Estado del producto* (Prueba de sistema)\n\n"
            "Panel Solar Bifacial TRINA SOLAR 500 WP\n"
            "SKU: `TRINANEG18RC.27-500`\n\n"
            "⏳ *Aún no disponible* (Próxima disponibilidad)\n\n"
            f"🕐 Chequeo realizado: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}"
        )
        send_telegram_alert(msg_test)
        print("⏳ Producto aún no disponible (Próxima disponibilidad).")

if __name__ == "__main__":
    check_availability()
