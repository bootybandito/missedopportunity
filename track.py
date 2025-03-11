import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import logging
import os


URL_FILE = "urls.txt"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

logging.basicConfig(
    filename="stock_check.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def get_urls():
    """Read URLs."""
    if not os.path.exists(URL_FILE):
        logging.error(f"File '{URL_FILE}' not found.")
        print(f"Error: '{URL_FILE}' not found.")
        return []
    
    with open(URL_FILE, "r") as file:
        urls = [line.strip() for line in file.readlines() if line.strip()]
    return urls

def check_stock(url):
    """Check stock URL."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        script_tags = soup.find_all("script", type="application/ld+json")
        stock_status = None
        json_ld_found = False

        for script in script_tags:
            try:
                json_data = json.loads(script.string)
                if json_data.get("@type") == "Product":
                    json_ld_found = True
                    offers = json_data.get("offers", {})
                    availability = offers.get("availability", "")
                    stock_status = "IN STOCK (JSON-LD)" if availability == "https://schema.org/InStock" else "OUT OF STOCK (JSON-LD)"
                    break
            except json.JSONDecodeError:
                continue
        
        if not json_ld_found:
            logging.warning(f"No JSON-LD stock data found for {url}.")
            print(f"Warning: No JSON-LD stock data found for {url}.")
            return
        
        add_to_cart_button = soup.find("button", class_="add-to-cart")
        if add_to_cart_button and "disabled" not in add_to_cart_button.get("class", []):
            stock_status = "IN STOCK (Confirmed by Add to Cart button)" if stock_status == "IN STOCK (JSON-LD)" else "DISCREPANCY: JSON-LD says OUT OF STOCK, but Add to Cart button is active"
        else:
            stock_status = "OUT OF STOCK (Confirmed by missing/disabled Add to Cart button)" if stock_status == "OUT OF STOCK (JSON-LD)" else "DISCREPANCY: JSON-LD says IN STOCK, but Add to Cart button is missing or disabled"

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"{current_time} | {url} | {stock_status}"
        logging.info(message)
        print(message)
    
    except requests.RequestException as e:
        error_message = f"Error fetching {url}: {e}"
        logging.error(error_message)
        print(error_message)

def monitor_stock(interval=300):
    """Continuously monitor."""
    print(f"Starting stock monitoring. Checking every {interval} seconds...")
    while True:
        urls = get_urls()
        if not urls:
            print("No valid URLs found. Exiting.")
            return
        
        for url in urls:
            check_stock(url)
        time.sleep(interval)

if __name__ == "__main__":
    urls = get_urls()
    if urls:
        for url in urls:
            check_stock(url)
    
    # Uncomment below for continuous monitoring (untested)
    # monitor_stock(interval=300)
