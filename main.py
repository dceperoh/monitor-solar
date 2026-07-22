import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup

def send_telegram_alert(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_ids = os.getenv("TELEGRAM_CHAT_IDS").split(",")
    
    success_count = 0
    for i, chat_id in enumerate(chat_ids, 1):
        chat_id = chat_id.strip()
        if not chat_id:
            continue
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            if result.get('ok'):
                print(f"✅ Destinatario {i} ({chat_id}): Enviado")
                success_count += 1
            else:
                print(f"❌ Destinatario {i} ({chat_id}): {result.get('description')}")
        except Exception as e:
            print(f"❌ Destinatario {i} ({chat_id}): Error - {e}")
    
    return success_count > 0

def check_warehouse(warehouse_name):
    """Verifica disponibilidad en un almacén específico"""
    url = "https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/"
    target_sku = "TRINANEG18RC.27-500"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(4)  # Esperar carga inicial
        
        # Buscar y seleccionar el almacén
        try:
            # Esperar a que aparezca el select
            select_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "select"))
            )
            
            select = Select(select_element)
            # Seleccionar por texto visible exacto
            select.select_by_visible_text(warehouse_name)
            
            time.sleep(4)  # Esperar que carguen los productos del almacén
            
        except Exception as e:
            print(f"️ No se pudo seleccionar {warehouse_name}: {e}")
            return False
        
        # Analizar el HTML resultante
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Buscar productos
        product_blocks = soup.find_all('li', class_=lambda x: x and 'product' in x.split())
        
        for block in product_blocks:
            if target_sku in block.get_text():
                if "Añadir al carrito" in block.get_text():
                    return True
                elif "Próxima disponibilidad" in block.get_text():
                    return False
        
        return False
        
    except Exception as e:
        print(f" Error en {warehouse_name}: {e}")
        return False
    finally:
        if driver:
            driver.quit()

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
            "🚨 *¡ALERTA DE DISPONIBILIDAD!*\n\n"
            "Panel Solar Bifacial TRINA SOLAR 500 WP\n"
            "SKU: `TRINANEG18RC.27-500`\n\n"
            "✅ *Disponible en:*\n" + 
            "\n".join([f"  • {w}" for w in available_warehouses]) +
            "\n\n"
            "🔗 [Ver en Tienda Solar](https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/)"
        )
        send_telegram_alert(msg)
        print("✅ Alerta enviada.")
    else:
        print("⏳ Producto no disponible en ningún almacén.")

if __name__ == "__main__":
    check_availability()
