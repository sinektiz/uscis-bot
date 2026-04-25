import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

CASE_NUMBER = os.getenv("CASE_NUMBER")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def enviar(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def obter_status():
    url = "https://egov.uscis.gov/casestatus/mycasestatus.do"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "appReceiptNum": CASE_NUMBER
    }

    resp = requests.post(url, headers=headers, data=data, timeout=30)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título do status (ex: Case Was Received)
    titulo = soup.find("h1")

    # Texto explicativo
    texto = soup.find("p")

    if not titulo or not texto:
        raise Exception("Não conseguiu localizar o status (possível bloqueio ou mudança no site)")

    return f"{titulo.get_text(strip=True)}\n\n{texto.get_text(strip=True)}"


def main():
    agora = datetime.now().strftime("%d/%m %H:%M")

    try:
        status = obter_status()
        enviar(f"📌 USCIS Status ({agora})\n\n{status}")
    except Exception as e:
        enviar(f"⚠️ Erro ao consultar USCIS:\n{e}")


if __name__ == "__main__":
    main()
