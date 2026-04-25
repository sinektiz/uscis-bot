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
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"appReceiptNum": CASE_NUMBER}

    for tentativa in range(1, 6):
        try:
            response = requests.post(URL, data=data, headers=headers, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            status_box = soup.find("div", class_="rows text-center")

            if not status_box:
                raise Exception("Erro HTML")

            status = status_box.text.strip()

            if len(status) < 20:
                raise Exception("Status inválido")

            return status

        except Exception as e:
            if tentativa == 5:
                raise e

            time.sleep(2 ** tentativa + random.random())

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
