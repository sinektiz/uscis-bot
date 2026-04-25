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

def obter_status():
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://egov.uscis.gov/",
        "Origin": "https://egov.uscis.gov"
    }

    # 1. Primeiro acesso (gera cookies)
    session.get("https://egov.uscis.gov/", headers=headers)

    data = {
        "appReceiptNum": CASE_NUMBER
    }

    # 2. Agora faz a consulta real
    response = session.post(
        "https://egov.uscis.gov/casestatus/mycasestatus.do",
        headers=headers,
        data=data,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    status_box = soup.find("div", class_="rows text-center")

    if not status_box:
        raise Exception("Não encontrou status")

    return status_box.text.strip()

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
