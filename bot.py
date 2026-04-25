import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import requests

# ===== CONFIG =====
CASE_NUMBER = os.getenv("CASE_NUMBER")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PROXY_SERVER = os.getenv("PROXY_SERVER")  # http://brd.superproxy.io:33335
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")


def enviar(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


async def consultar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage"
            ],
            proxy={
                "server": PROXY_SERVER,
                "username": PROXY_USERNAME,
                "password": PROXY_PASSWORD
            }
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            locale="en-US",
            viewport={"width": 1366, "height": 768}
        )

        # stealth: remove webdriver flag
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        print("[LOG] Acessando USCIS...")

        await page.goto("https://egov.uscis.gov/casestatus/mycasestatus.do",
                        wait_until="domcontentloaded",
                        timeout=60000)

        # esperar input aparecer (ou fallback)
        try:
            await page.wait_for_selector("input[name='appReceiptNum']", timeout=15000)
        except:
            # possível bloqueio
            html = await page.content()
            if "blocked" in html.lower():
                raise Exception("Bloqueado pelo site (Cloudflare)")
            else:
                raise Exception("Página carregou mas input não apareceu")

        # digitar protocolo
        await page.fill("input[name='appReceiptNum']", CASE_NUMBER)
        await page.click("input[type='submit']")

        # esperar resultado
        await page.wait_for_selector("h1", timeout=20000)

        titulo = await page.locator("h1").inner_text()
        texto = await page.locator("p").first.inner_text()

        await browser.close()

        return f"{titulo}\n\n{texto}"


async def main():
    agora = datetime.now().strftime("%d/%m %H:%M")

    for tentativa in range(3):
        try:
            print(f"[LOG] Tentativa {tentativa+1}")
            status = await consultar()

            enviar(f"📌 USCIS Status ({agora})\n\n{status}")
            return

        except Exception as e:
            print(f"[ERRO] {e}")
            await asyncio.sleep(5)

    enviar("⚠️ Falha ao consultar USCIS após 3 tentativas")


if __name__ == "__main__":
    asyncio.run(main())
