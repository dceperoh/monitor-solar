import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup

def send_telegram_alert(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_ids = os.getenv("TELEGRAM_CHAT_IDS").split(",")
    
    for i, chat_id in enumerate(chat_ids, 1):
        chat_id = chat_id.strip()
        if not chat_id: continue
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            if result.get('ok'):
                print(f"✅ Alerta enviada a destinatario {i}")
            else:
                print(f"❌ Error API Telegram (destinatario {i}): {result.get('description')}")
        except Exception as e:
            print(f"❌ Error de red (destinatario {i}): {e}")

def check_warehouse(warehouse_name):
    url = "https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/"
    target_sku = "TRINANEG18RC.27-500"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(4)
        
        select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        Select(select_element).select_by_visible_text(warehouse_name)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_blocks = soup.find_all('li', class_=lambda x: x and 'product' in x.split())
        
        for block in product_blocks:
            if target_sku in block.get_text():
                return "Añadir al carrito" in block.get_text()
        return False
    except Exception as e:
        print(f"❌ Error verificando {warehouse_name}: {e}")
        return False
    finally:
        if driver: driver.quit()

def check_availability():
    warehouses = ["La Habana - Miramar", "La Habana - Siboney"]
    available_warehouses = []
    
    for warehouse in warehouses:
        print(f"🔍 Verificando {warehouse}...")
        if check_warehouse(warehouse):
            available_warehouses.append(warehouse)
            print(f"  ✅ {warehouse}: DISPONIBLE")
        else:
            print(f"  ⏳ {warehouse}: No disponible")
        time.sleep(2)
    
    if available_warehouses:
        msg = (
            " *¡ALERTA DE DISPONIBILIDAD!*\n\n"
            "Panel Solar Bifacial TRINA SOLAR 500 WP\n"
            "SKU: `TRINANEG18RC.27-500`\n\n"
            "✅ *Disponible en:*\n" + 
            "\n".join([f"  • {w}" for w in available_warehouses]) +
            "\n\n"
            "🔗 [Ver en Tienda Solar](https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/)"
        )
        send_telegram_alert(msg)
    else:
        print(" Producto no disponible en ningún almacén.")

if __name__ == "__main__":
    check_availability()
