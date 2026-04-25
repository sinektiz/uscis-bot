import requests
import os
from datetime import datetime

CASE_NUMBER = os.getenv("CASE_NUMBER")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def enviar(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def obter_status():
    url = "https://egov.uscis.gov/casestatus/mycasestatus.do"

    resp = requests.post(url, data={
        "appReceiptNum": CASE_NUMBER
    }, headers={
        "User-Agent": "Mozilla/5.0"
    })

    html = resp.text

    # captura simples do status
    import re
    match = re.search(r'<div class="rows text-center">(.*?)</div>', html, re.S)

    if not match:
        raise Exception("Status não encontrado")

    return match.group(1).strip()


def main():
    agora = datetime.now().strftime("%d/%m %H:%M")

    try:
        status = obter_status()
        enviar(f"📌 USCIS Status ({agora})\n\n{status}")
    except Exception as e:
        enviar(f"⚠️ Erro:\n{e}")


if __name__ == "__main__":
    main()
