import os
import time
import re
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
                print(f"✅ Mensaje enviado a destinatario {i}")
            else:
                print(f"❌ Error API Telegram (destinatario {i}): {result.get('description')}")
        except Exception as e:
            print(f"❌ Error de red (destinatario {i}): {e}")

def check_warehouse(warehouse_name):
    url = "https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/"
    
    # Lista de SKUs específicos a buscar (puedes agregar más)
    target_skus = ["TRINANEG18RC.27-500", "TRINANEG18RC.27-510"]  # Agrega aquí otros SKUs específicos
    
    # Palabra clave para búsqueda genérica (buscamos "510" en el nombre del producto)
    keyword = "510"
    
    # ==========================================
    # SECCIÓN ANTI-BOT
    # ==========================================
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        # ==========================================
        # FIN DE LA SECCIÓN ANTI-BOT
        # ==========================================
        
        driver.get(url)
        time.sleep(4)
        
        select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "select")))
        Select(select_element).select_by_visible_text(warehouse_name)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Buscar todos los bloques de productos
        product_blocks = soup.find_all('li', class_=lambda x: x and 'product' in x.split())
        
        # Lista para almacenar los productos encontrados
        found_products = []
        
        for block in product_blocks:
            block_text = block.get_text()
            product_found = False
            match_type = ""
            
            # PRIMERO: Buscar por SKU específico (prioridad máxima)
            for sku in target_skus:
                if sku in block_text:
                    product_found = True
                    match_type = f"SKU específico: {sku}"
                    break
            
            # SEGUNDO: Si no se encontró por SKU, buscar por palabra clave "510"
            if not product_found:
                # Convertir a minúsculas para búsqueda sin distinción de mayúsculas
                # y buscar "510" en cualquier parte del texto
                if keyword.lower() in block_text.lower():
                    product_found = True
                    match_type = f"Palabra clave '{keyword}' en el nombre"
            
            # Si encontramos el producto, verificar si está disponible
            if product_found:
                # Extraer el nombre del producto para el mensaje
                product_name = "Producto desconocido"
                try:
                    # Intentar encontrar el nombre en el bloque
                    name_tag = block.find('h2', class_=lambda x: x and 'product-title' in x)
                    if name_tag:
                        product_name = name_tag.get_text().strip()
                    else:
                        # Si no hay h2, buscar cualquier texto que contenga el SKU o keyword
                        lines = block_text.split('\n')
                        for line in lines:
                            if any(sku in line for sku in target_skus) or keyword in line:
                                product_name = line.strip()
                                break
                except:
                    pass
                
                # Verificar si tiene "Añadir al carrito" (disponible)
                if "Añadir al carrito" in block_text:
                    found_products.append({
                        'name': product_name,
                        'match_type': match_type,
                        'block': block
                    })
        
        # Si encontramos productos disponibles, retornamos True con los detalles
        if found_products:
            return True, found_products
        
        return False, []
        
    except Exception as e:
        print(f"❌ Error verificando {warehouse_name}: {e}")
        return False, []
    finally:
        if driver: 
            driver.quit()

def check_availability():
    warehouses = ["La Habana - Miramar", "La Habana - Siboney"]
    available_warehouses = {}
    
    for warehouse in warehouses:
        print(f"🔍 Verificando {warehouse}...")
        available, products = check_warehouse(warehouse)
        
        if available:
            available_warehouses[warehouse] = products
            print(f"  ✅ {warehouse}: DISPONIBLE ({len(products)} producto(s) encontrado(s))")
            for product in products:
                print(f"     • {product['name']} ({product['match_type']})")
        else:
            print(f"  ⏳ {warehouse}: No disponible")
        time.sleep(2)
    
    # --- LÓGICA DE MENSAJES MODIFICADA ---
    if available_warehouses:
        # Construir mensaje con todos los productos encontrados
        msg = "🚨🚨🚨 *¡¡¡ALERTA MÁXIMA - ¡¡¡STOCK DISPONIBLE!!!* 🚨🚨\n\n"
        msg += "📦 *Productos encontrados:*\n\n"
        
        for warehouse, products in available_warehouses.items():
            msg += f"🏪 *{warehouse}:*\n"
            for product in products:
                msg += f"  ✅ {product['name']}\n"
                msg += f"     └─ {product['match_type']}\n"
            msg += "\n"
        
        msg += "🏃💨 *¡Corre que se acaban!*\n\n"
        msg += "🔗 [Ir a Tienda Solar](https://tiendasolar.com/categoria-producto/fotovoltaica/paneles-solares/)"
        
        send_telegram_alert(msg)
        print("🚨 ¡Alerta de DISPONIBILIDAD enviada a Telegram!")
        
    else:
        print("⏳ Productos no disponibles. (Modo sigilo: no se envía mensaje a Telegram)")

if __name__ == "__main__":
    check_availability()
