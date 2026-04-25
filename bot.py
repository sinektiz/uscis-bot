import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# =========================
# CONFIG
# =========================
CASE_NUMBER = os.getenv("CASE_NUMBER")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PROXY_SERVER = os.getenv("PROXY_SERVER")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

ARQUIVO_STATUS = "status.txt"


# =========================
# LOG
# =========================
def log(msg):
    print(f"[LOG] {msg}", flush=True)


# =========================
# TELEGRAM
# =========================
def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=20)

        log(f"Telegram status: {resp.status_code}")

    except Exception as e:
        log(f"Erro Telegram: {e}")


# =========================
# SCRAPING
# =========================
def obter_status():
    for tentativa in range(3):
        try:
            log(f"Tentativa {tentativa+1}")

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={
                        "server": PROXY_SERVER,
                        "username": PROXY_USERNAME,
                        "password": PROXY_PASSWORD,
                    },
                    args=[
                        "--ignore-certificate-errors",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )

                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                    ignore_https_errors=True,
                    viewport={"width": 1366, "height": 768}
                )

                page = context.new_page()

                log("Abrindo USCIS...")

                page.goto(
                    "https://egov.uscis.gov/casestatus/mycasestatus.do",
                    timeout=60000,
                    wait_until="domcontentloaded"
                )

                # espera carregar JS
                page.wait_for_load_state("networkidle")

                time.sleep(5)  # delay humano

                # DEBUG: salva HTML
                html = page.content()
                log(f"HTML length: {len(html)}")

                if "#receipt_number" not in html:
                    raise Exception("Página carregada sem formulário (possível bloqueio)")

                page.wait_for_selector("#receipt_number", timeout=60000)

                log("Digitando protocolo...")
                page.fill("#receipt_number", CASE_NUMBER)

                page.click("#caseStatusSearchBtn")

                page.wait_for_load_state("networkidle")

                page.wait_for_selector(".rows.text-center", timeout=60000)

                status = page.inner_text(".rows.text-center")

                browser.close()

                if not status or len(status) < 20:
                    raise Exception("Status inválido")

                log("Status capturado com sucesso")
                return status.strip()

        except Exception as e:
            log(f"Erro tentativa {tentativa+1}: {e}")
            time.sleep(10)

    raise Exception("Falha após 3 tentativas")


# =========================
# STORAGE
# =========================
def carregar_status():
    if not os.path.exists(ARQUIVO_STATUS):
        return None
    try:
        with open(ARQUIVO_STATUS, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None


def salvar_status(status):
    try:
        with open(ARQUIVO_STATUS, "w", encoding="utf-8") as f:
            f.write(status)
    except Exception as e:
        log(f"Erro ao salvar status: {e}")


# =========================
# MAIN
# =========================
def main():
    log("=== INICIANDO BOT ===")

    if not CASE_NUMBER or not TELEGRAM_TOKEN or not CHAT_ID:
        log("Variáveis obrigatórias não definidas")
        return

    agora = datetime.now().strftime("%d/%m %H:%M")

    try:
        status_atual = obter_status()
    except Exception as e:
        enviar(f"⚠️ Erro ao consultar USCIS:\n{e}")
        return

    status_antigo = carregar_status()

    mensagem = f"📌 USCIS Status ({agora})\n\n{status_atual}"

    if status_antigo and status_atual != status_antigo:
        mensagem = f"🚨 STATUS MUDOU! ({agora})\n\n{status_atual}"

    enviar(mensagem)
    salvar_status(status_atual)

    log("=== FINALIZADO ===")


if __name__ == "__main__":
    main()
