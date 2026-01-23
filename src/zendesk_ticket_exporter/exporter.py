# -*- coding: utf-8 -*-
import os
import re
import json
import time
import random
import base64
import csv
from pathlib import Path
from dataclasses import dataclass
from getpass import getpass

import pandas as pd
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException


# ===================== Data classes =====================
@dataclass
class ExporterConfig:
    subdomain: str
    excel_codigos: Path
    output_dir: Path
    chrome_driver_path: Path

    headless: bool
    keep_browser_open: bool
    reset_checkpoint: bool

    between_tickets_min_s: float
    between_tickets_max_s: float
    after_print_min_s: float
    after_print_max_s: float

    max_pages: int
    retry_create_driver: int
    max_tickets_per_assessor: int | None


# ===================== Small IO helpers =====================
def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def append_csv_row(path: Path, header: list, row: list):
    ensure_parent(path)
    is_new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(header)
        w.writerow(row)


def save_json(path: Path, obj: dict):
    ensure_parent(path)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def pdf_valido(path: Path) -> bool:
    try:
        b = path.read_bytes()
        if len(b) < 2048:
            return False
        return b.startswith(b"%PDF-")
    except Exception:
        return False


# ===================== Config & env =====================
def get_env_or_prompt(cfg_email: str, cfg_pass: str) -> tuple[str, str]:
    load_dotenv()
    email = (os.getenv("ZENDESK_EMAIL") or cfg_email or "").strip()
    pwd = (os.getenv("ZENDESK_PASS") or cfg_pass or "").strip()

    if not email:
        email = input("E-mail Zendesk: ").strip()
    if not pwd:
        pwd = getpass("Senha Zendesk: ").strip()

    if not email or not pwd:
        raise ValueError("Credenciais ausentes (ZENDESK_EMAIL / ZENDESK_PASS).")

    return email, pwd


def carregar_codigos_xlsx(path: Path) -> list[str]:
    raw = pd.read_excel(path, sheet_name=None)
    df = pd.concat(raw.values(), ignore_index=True) if isinstance(raw, dict) else raw.copy()
    df.columns = df.columns.str.strip().str.lower()

    possiveis = [c for c in df.columns if ("xp" in c and ("cod" in c or "cód" in c)) or c in ("codigo xp", "código xp")]
    if not possiveis:
        raise ValueError(f"Não encontrei coluna de 'Código XP'. Colunas: {list(df.columns)}")

    col = possiveis[0]
    s = df[col].astype(str).fillna("").str.strip()
    s = s[~s.str.lower().isin(["", "nan", "none", "null"])]
    s = s.str.extract(r"([A-Za-z]?\d{3,})", expand=False).dropna().drop_duplicates().str.upper()
    return s.tolist()


# ===================== Selenium driver =====================
def create_driver(chromedriver: Path, profile_dir: Path, headless: bool):
    if not chromedriver.exists():
        raise FileNotFoundError(f"ChromeDriver não encontrado: {chromedriver}")

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1366,900")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    opts.add_argument("--disable-print-preview")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")

    opts.add_argument(f"--user-data-dir={str(profile_dir)}")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-extensions")

    service = Service(executable_path=str(chromedriver))
    drv = webdriver.Chrome(service=service, options=opts)
    drv.implicitly_wait(0)

    # neutraliza window.print
    try:
        drv.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                (function(){
                  const nop = function(){};
                  try { Object.defineProperty(window, 'print', { value: nop, configurable: true }); } catch(e){}
                })();
            """
        })
    except Exception:
        pass

    drv.set_script_timeout(10)
    return drv


def safe_create_driver(cfg: ExporterConfig, out_dir: Path):
    profile_root = out_dir / "chrome_profiles"
    profile_root.mkdir(parents=True, exist_ok=True)
    profile_dir = profile_root / f"profile_{int(time.time()*1000)}"
    profile_dir.mkdir(parents=True, exist_ok=True)

    last = None
    for i in range(cfg.retry_create_driver + 1):
        try:
            return create_driver(cfg.chrome_driver_path, profile_dir, cfg.headless)
        except Exception as e:
            last = e
            time.sleep(1.0)
    raise last


def robust_get(drv, url, retries=5, base_sleep=0.7):
    for attempt in range(1, retries + 1):
        try:
            drv.get(url)
            return True
        except Exception:
            try:
                drv.get("about:blank")
            except Exception:
                pass
            time.sleep(base_sleep * attempt)
    return False


def wait_document_ready(drv, to=22):
    end = time.time() + to
    while time.time() < end:
        try:
            if drv.execute_script("return document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.22)
    return False


# ===================== Zendesk flows =====================
def fazer_login(drv, subdomain: str, email: str, senha: str):
    url_login = f"https://{subdomain}.zendesk.com/auth/v2/login/signin"
    robust_get(drv, url_login)
    time.sleep(1.0)

    email_sel = ["input[name='email']", "#user_email", "input[type='email']"]
    pass_sel = ["input[name='password']", "#user_password", "input[type='password']"]
    btn_sel = ["button[type='submit']", "button[name='commit']", "button[data-testid='sign-in-submit']"]

    email_box = None
    for sel in email_sel:
        try:
            email_box = WebDriverWait(drv, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR, sel)))
            break
        except Exception:
            pass
    if not email_box:
        raise RuntimeError("Campo de e-mail não encontrado (SSO/MFA pode exigir ajuste).")

    email_box.clear()
    email_box.send_keys(email)

    pass_box = None
    for sel in pass_sel:
        try:
            pass_box = WebDriverWait(drv, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR, sel)))
            break
        except Exception:
            pass
    if not pass_box:
        raise RuntimeError("Campo de senha não encontrado (SSO/MFA pode exigir ajuste).")

    pass_box.clear()
    pass_box.send_keys(senha)

    btn = None
    for sel in btn_sel:
        try:
            btn = WebDriverWait(drv, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            break
        except Exception:
            pass
    if not btn:
        raise RuntimeError("Botão de login não encontrado.")

    btn.click()
    time.sleep(2.0)


def abrir_people(drv):
    WebDriverWait(drv, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "nav")))

    def loaded(timeout=6):
        try:
            WebDriverWait(drv, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test-id='customer-lists-search-box']"))
            )
            return True
        except Exception:
            return False

    # tentativa rápida
    try:
        btn_pos = WebDriverWait(drv, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "nav ul:nth-of-type(1) li:nth-of-type(3) button"))
        )
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_pos)
        btn_pos.click()
        if loaded():
            time.sleep(0.8)
            return
    except Exception:
        pass

    # fallback
    for b in drv.find_elements(By.CSS_SELECTOR, "nav button, nav a[role='button'], nav a"):
        try:
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
            time.sleep(0.1)
            b.click()
            if loaded():
                time.sleep(0.8)
                return
        except Exception:
            continue

    raise RuntimeError("Não consegui abrir a tela de clientes (People).")


def find_search_input(drv):
    candidates = [
        (By.CSS_SELECTOR, "input[data-test-id='customer-lists-search-box']"),
        (By.XPATH, "//input[@type='text' and (contains(@placeholder,'Pesquisar') or contains(@placeholder,'Search'))]")
    ]
    for how, sel in candidates:
        try:
            return WebDriverWait(drv, 8).until(EC.element_to_be_clickable((how, sel)))
        except Exception:
            pass
    return None


def clear_input_hard(drv, el):
    try:
        el.click()
        ActionChains(drv).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(Keys.BACK_SPACE).perform()
        time.sleep(0.12)
    except Exception:
        pass
    try:
        drv.execute_script("""
            const el = arguments[0];
            el.value = '';
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
        """, el)
    except Exception:
        pass


def buscar_cliente(drv, termo: str) -> bool:
    campo = find_search_input(drv)
    if not campo:
        raise RuntimeError("Campo 'Pesquisar clientes' não encontrado.")
    clear_input_hard(drv, campo)
    campo.send_keys(termo)
    campo.send_keys(Keys.ENTER)

    end = time.time() + 10
    while time.time() < end:
        rows = drv.find_elements(By.XPATH, "//table//tbody//tr")
        if rows:
            return True
        vacios = drv.find_elements(By.XPATH, "//*[contains(.,'Nenhum') or contains(.,'No results') or contains(.,'sem resultados')]")
        if any(v.is_displayed() for v in vacios):
            return False
        time.sleep(0.2)
    return True


def abrir_primeiro_cliente(drv) -> bool:
    try:
        WebDriverWait(drv, 15).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))
    except TimeoutException:
        return False

    selectors = [
        (By.CSS_SELECTOR, "td[data-test-id='customer-row-cell-name'] a[href*='/users/']"),
        (By.XPATH, "//a[contains(@href,'/agent/users/')]")
    ]
    for how, sel in selectors:
        try:
            link = WebDriverWait(drv, 6).until(EC.element_to_be_clickable((how, sel)))
            drv.execute_script("arguments[0].click();", link)
            WebDriverWait(drv, 10).until(EC.url_contains("/agent/users/"))
            return True
        except Exception:
            pass
    return False


def abrir_aba_tickets(drv):
    candidates = [
        (By.XPATH, "//a[contains(.,'Tickets')]"),
        (By.XPATH, "//button[contains(.,'Tickets')]"),
        (By.XPATH, "//a[contains(.,'Solicitações') or contains(.,'Requests')]"),
        (By.XPATH, "//button[contains(.,'Solicitações') or contains(.,'Requests')]")
    ]
    for how, sel in candidates:
        try:
            el = WebDriverWait(drv, 6).until(EC.element_to_be_clickable((how, sel)))
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()
            time.sleep(0.6)
            return
        except Exception:
            continue


# ===================== Ticket collection =====================
def get_rows_xpath():
    return "//table//tbody//tr"


def coletar_tickets_visiveis(drv, ids: set[int]):
    rows = drv.find_elements(By.XPATH, get_rows_xpath())
    for r in rows:
        try:
            if not r.is_displayed():
                continue
            tid = None
            links = r.find_elements(By.XPATH, ".//a[contains(@href,'/tickets/')]")
            for a in links:
                href = a.get_attribute("href") or ""
                m = re.search(r"/tickets/(\d+)", href)
                if m:
                    tid = int(m.group(1))
                    break
            if tid is not None:
                ids.add(tid)
        except Exception:
            pass


def get_pagination_ul(drv):
    uls = drv.find_elements(By.XPATH, "//table//tfoot//ul | //tfoot//ul[descendant::li]")
    for ul in uls:
        try:
            if ul.is_displayed():
                return ul
        except Exception:
            pass
    return None


def paginator_controls(ul):
    items = ul.find_elements(By.XPATH, "./li")
    nums = []
    first = prev = nextb = last = None

    for li in items:
        if not li.is_displayed():
            continue
        txt = (li.text or "").strip()
        cls = li.get_attribute("class") or ""
        try:
            el = li.find_element(By.XPATH, ".//a|.//button")
        except Exception:
            el = li

        if txt in ("«", "<<"):
            first = el
        elif txt in ("‹", "<"):
            prev = el
        elif txt in ("›", ">"):
            nextb = el
        elif txt in ("»", ">>"):
            last = el
        elif re.fullmatch(r"\d+", txt):
            n = int(txt)
            is_act = "active" in cls or "current" in cls or ((li.get_attribute("aria-current") or "") == "page")
            nums.append((n, el, is_act))

    current = None
    for n, _, act in nums:
        if act:
            current = n
            break

    return {"first": first, "prev": prev, "next": nextb, "last": last, "nums": nums, "current": current}


def click_and_wait(drv, el, timeout=15):
    before = ""
    try:
        row = drv.find_element(By.XPATH, get_rows_xpath())
        before = (row.text or "")[:80]
    except Exception:
        pass

    try:
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.05)
        drv.execute_script("arguments[0].click();", el)
    except Exception:
        return False

    end = time.time() + timeout
    while time.time() < end:
        after = ""
        try:
            row = drv.find_element(By.XPATH, get_rows_xpath())
            after = (row.text or "")[:80]
        except Exception:
            pass
        if after and after != before:
            return True
        time.sleep(0.2)
    return False


def goto_first_and_get_total_pages(drv):
    ul = get_pagination_ul(drv)
    if not ul:
        return 1

    ctl = paginator_controls(ul)
    if ctl["last"]:
        click_and_wait(drv, ctl["last"])
        time.sleep(0.2)
        ul = get_pagination_ul(drv)
        ctl = paginator_controls(ul)

    total = max([n for (n, _, _) in ctl["nums"]], default=1)

    if ctl["first"]:
        click_and_wait(drv, ctl["first"])
    else:
        for n, el, _ in ctl["nums"]:
            if n == 1:
                click_and_wait(drv, el)
                break

    return max(total, 1)


def coletar_ids_tickets(drv, limite: int | None, max_pages: int):
    ids = set()
    total_pages = goto_first_and_get_total_pages(drv)

    page = 1
    while page <= total_pages and page <= max_pages:
        if limite and len(ids) >= limite:
            break

        coletar_tickets_visiveis(drv, ids)

        if page == total_pages:
            break

        ul = get_pagination_ul(drv)
        if not ul:
            break
        ctl = paginator_controls(ul)
        nxt = ctl.get("next")
        if not nxt:
            break

        click_and_wait(drv, nxt)
        page += 1

    out = sorted(ids)
    return out[:limite] if limite else out


# ===================== PDF export =====================
def ticket_print_url(subdomain: str, ticket_id: int) -> str:
    return f"https://{subdomain}.zendesk.com/tickets/{ticket_id}/print"


def ticket_view_url(subdomain: str, ticket_id: int) -> str:
    return f"https://{subdomain}.zendesk.com/agent/tickets/{ticket_id}"


def fechar_abas_extras(drv, manter=1):
    try:
        handles = drv.window_handles
        while len(handles) > manter:
            drv.switch_to.window(handles[-1])
            drv.close()
            time.sleep(0.2)
            handles = drv.window_handles
        drv.switch_to.window(handles[0])
    except Exception:
        pass


def salvar_ticket_pdf(drv, subdomain: str, ticket_id: int, pasta: Path, after_print: tuple[float, float]):
    pasta.mkdir(parents=True, exist_ok=True)
    out = pasta / f"ticket_{ticket_id}.pdf"
    if out.exists() and out.stat().st_size > 1024 and pdf_valido(out):
        return out

    fechar_abas_extras(drv, manter=1)

    old = drv.window_handles[:]
    drv.execute_script("window.open('about:blank','_blank');")
    time.sleep(0.4)
    for h in drv.window_handles:
        if h not in old:
            drv.switch_to.window(h)
            break

    try:
        drv.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": True})
    except Exception:
        pass

    if not robust_get(drv, ticket_print_url(subdomain, ticket_id), retries=2):
        robust_get(drv, ticket_view_url(subdomain, ticket_id), retries=3)
        robust_get(drv, ticket_print_url(subdomain, ticket_id), retries=3)

    wait_document_ready(drv, to=22)
    time.sleep(0.2)

    try:
        drv.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": "print"})
    except Exception:
        pass

    pdf = drv.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,
        "landscape": False,
        "paperWidth": 8.27,
        "paperHeight": 11.69,
        "preferCSSPageSize": True,
        "scale": 1.0
    })
    out.write_bytes(base64.b64decode(pdf["data"]))

    try:
        drv.close()
        drv.switch_to.window(old[0])
    except Exception:
        pass

    time.sleep(random.uniform(*after_print))
    if not pdf_valido(out):
        raise RuntimeError(f"PDF inválido: {out}")
    return out


# ===================== Checkpoint =====================
def load_checkpoint(path: Path, reset: bool) -> dict:
    if reset:
        return {}
    return load_json(path)


def save_checkpoint(path: Path, done_assessors: set, processed_tickets: set):
    save_json(path, {
        "done_assessors": sorted(done_assessors),
        "processed_tickets": sorted(processed_tickets)
    })


# ===================== Orchestrator =====================
def export_all(cfg: ExporterConfig, cfg_auth: dict):
    out_dir = cfg.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = out_dir / "checkpoint.json"
    successcsv = out_dir / "success.csv"
    failcsv = out_dir / "failed.csv"
    inventorycsv = out_dir / "all_tickets.csv"
    summaryjson = out_dir / "summary.json"

    email, pwd = get_env_or_prompt(cfg_auth.get("email", ""), cfg_auth.get("password", ""))

    done_assessors = set(load_checkpoint(checkpoint_path, cfg.reset_checkpoint).get("done_assessors", []))
    processed_tickets = set(load_checkpoint(checkpoint_path, cfg.reset_checkpoint).get("processed_tickets", []))

    codigos = carregar_codigos_xlsx(cfg.excel_codigos)
    if not codigos:
        print("Nenhum código encontrado na planilha.")
        return

    drv = safe_create_driver(cfg, out_dir)

    expected_map: dict[str, set[int]] = {}

    try:
        fazer_login(drv, cfg.subdomain, email, pwd)

        for cod in codigos:
            if cod in done_assessors:
                continue

            try:
                abrir_people(drv)
                if not buscar_cliente(drv, cod):
                    done_assessors.add(cod)
                    save_checkpoint(checkpoint_path, done_assessors, processed_tickets)
                    continue

                if not abrir_primeiro_cliente(drv):
                    append_csv_row(failcsv, ["assessor", "ticket_id", "erro"], [cod, -1, "Não abriu perfil"])
                    done_assessors.add(cod)
                    save_checkpoint(checkpoint_path, done_assessors, processed_tickets)
                    continue

                abrir_aba_tickets(drv)

                ids = coletar_ids_tickets(drv, limite=cfg.max_tickets_per_assessor, max_pages=cfg.max_pages)
                expected_map[cod] = set(ids)

                pasta = out_dir / f"assessor_{cod}"

                for tid in ids:
                    if tid in processed_tickets:
                        continue

                    try:
                        p = salvar_ticket_pdf(
                            drv, cfg.subdomain, tid, pasta,
                            after_print=(cfg.after_print_min_s, cfg.after_print_max_s)
                        )
                        processed_tickets.add(tid)

                        append_csv_row(successcsv, ["assessor", "ticket_id", "arquivo", "bytes"],
                                       [cod, tid, str(p), p.stat().st_size])
                        append_csv_row(inventorycsv, ["assessor", "ticket_id", "arquivo", "bytes", "status"],
                                       [cod, tid, str(p), p.stat().st_size, "baixado_agora"])

                        if (len(processed_tickets) % 10) == 0:
                            save_checkpoint(checkpoint_path, done_assessors, processed_tickets)

                        time.sleep(random.uniform(cfg.between_tickets_min_s, cfg.between_tickets_max_s))

                    except InvalidSessionIdException:
                        try:
                            drv.quit()
                        except Exception:
                            pass
                        drv = safe_create_driver(cfg, out_dir)
                        fazer_login(drv, cfg.subdomain, email, pwd)

                    except Exception as e:
                        append_csv_row(failcsv, ["assessor", "ticket_id", "erro"], [cod, tid, str(e)[:1000]])
                        time.sleep(0.8)

                done_assessors.add(cod)
                save_checkpoint(checkpoint_path, done_assessors, processed_tickets)

            except Exception as e:
                append_csv_row(failcsv, ["assessor", "ticket_id", "erro"], [cod, -1, str(e)[:1000]])
                done_assessors.add(cod)
                save_checkpoint(checkpoint_path, done_assessors, processed_tickets)
                continue

        summary = {
            "total_assessors": len(codigos),
            "total_expected_tickets": sum(len(v) for v in expected_map.values()),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_json(summaryjson, summary)

        print("[OK] Concluído.")
        if cfg.keep_browser_open:
            input("Pressione Enter para fechar o navegador...")

    finally:
        try:
            drv.quit()
        except Exception:
            pass
