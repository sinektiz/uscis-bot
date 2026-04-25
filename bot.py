import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import time
import random

CASE_NUMBER = os.getenv("CASE_NUMBER")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://egov.uscis.gov/casestatus/mycasestatus.do"
ARQUIVO_STATUS = "status.txt"

from playwright.sync_api import sync_playwright

from playwright.sync_api import sync_playwright

def obter_status():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={
                "server": PROXY_SERVER
            }
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        page = context.new_page()

        page.goto("https://egov.uscis.gov/", timeout=60000)

        page.wait_for_selector("input[name='appReceiptNum']")
        page.fill("input[name='appReceiptNum']", CASE_NUMBER)

        page.click("input[type='submit']")

        page.wait_for_selector(".rows.text-center", timeout=60000)

        status = page.inner_text(".rows.text-center")

        browser.close()

        return status.strip()

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def carregar_status():
    if not os.path.exists(ARQUIVO_STATUS):
        return None
    return open(ARQUIVO_STATUS).read()

def salvar_status(status):
    open(ARQUIVO_STATUS, "w").write(status)

def main():
    agora = datetime.now().strftime("%d/%m %H:%M")

    try:
        status = obter_status()
    except Exception as e:
        enviar_telegram(f"Erro USCIS:\n{e}")
        return

    antigo = carregar_status()

    mensagem = f"📌 Status ({agora})\n\n{status}"

    if antigo and status != antigo:
        mensagem = f"🚨 MUDOU!\n\n{status}"

    enviar_telegram(mensagem)
    salvar_status(status)

if __name__ == "__main__":
    main()
