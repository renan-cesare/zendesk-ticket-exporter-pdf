# Zendesk Ticket Exporter (PDF)

Automação em Python (Selenium) para **exportação em massa de tickets do Zendesk em PDF**, com **checkpoint**, **retomada segura**, **inventário de execução** e **consolidação de evidências por código/identificador interno**.

> **English (short):** Selenium-based internal automation that navigates Zendesk Agent Workspace and exports ticket print views as PDFs (CDP printToPDF), with checkpointing, retries, and execution inventory.

---

## Principais recursos

* Exportação em PDF via **Chrome DevTools Protocol** (`Page.printToPDF`)
* **Checkpoint automático** (processo pode ser interrompido e retomado)
* Controle de **retries**, falhas e logs
* Inventário completo da execução:

  * `success.csv`
  * `failed.csv`
  * `all_tickets.csv`
  * `summary.json`
* Estrutura de projeto organizada (`src/`, `configs/`, `.env.example`)

---

## Contexto

Em rotinas de **operações, risco, compliance e backoffice**, é comum a necessidade de **coletar evidências** de atendimentos registrados em tickets do Zendesk para:

* auditorias internas
* apuração de incidentes e reclamações
* dossiês de clientes e processos
* histórico operacional e regulatório

A exportação manual desses tickets é lenta, sujeita a erros e difícil de retomar quando o processo é interrompido.

Este projeto automatiza esse fluxo de forma controlada e auditável.

---

## Aviso importante (uso autorizado)

Este repositório é apresentado **exclusivamente como exemplo técnico/portfólio**.

* Utilize **somente em ambientes e contas autorizadas**
* Respeite políticas internas, LGPD e os termos do Zendesk
* **Não publique dados reais**, PDFs exportados, IDs sensíveis ou credenciais

---

## Estrutura do projeto

```text
.
├─ configs/
│  └─ config.example.json
├─ examples/
│  └─ .env.example
├─ src/
│  └─ zendesk_ticket_exporter/
│     ├─ __init__.py
│     ├─ app.py
│     ├─ config.py
│     ├─ exporter.py
│     └─ logging_config.py
├─ main.py
├─ requirements.txt
├─ LICENSE
└─ README.md
```

---

## Requisitos

* Python 3.10+
* Google Chrome instalado
* ChromeDriver compatível com a versão do Chrome
* Acesso ao Zendesk (Agent Workspace)

> Ambientes com SSO ou MFA podem exigir ajustes adicionais no fluxo de login.

---

## Instalação

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Credenciais (.env)

As credenciais **não devem ser versionadas**.

O sistema lê as variáveis de ambiente:

```env
ZENDESK_EMAIL=seu_email@empresa.com
ZENDESK_PASS=sua_senha
```

Há um exemplo em `examples/.env.example`.

---

## Configuração (config.json)

1. Crie seu arquivo local de configuração:

```bash
# Windows
copy configs\config.example.json configs\config.json

# Linux / macOS
cp configs/config.example.json configs/config.json
```

2. Ajuste os campos principais:

* `zendesk.subdomain`
* `paths.excel_codigos`
* `paths.output_dir`
* `paths.chrome_driver_path`

---

## Execução

```bash
python main.py --config configs/config.json
```

O processo:

* salva automaticamente o progresso (checkpoint)
* pode ser interrompido e retomado
* ignora tickets já exportados com sucesso

---

## Checkpoint e retomada

Caso a execução seja interrompida, basta rodar novamente.

Para forçar uma nova execução completa:

```json
"reset_checkpoint": true
```

---

## Saídas geradas

Os arquivos são criados no diretório `output/`:

* PDFs organizados por código/identificador
* `success.csv` – tickets exportados com sucesso
* `failed.csv` – tickets com erro
* `all_tickets.csv` – inventário completo
* `summary.json` – resumo da execução

---

## Sanitização de dados

Este repositório **não contém dados reais**.

* PDFs e arquivos de execução são ignorados pelo Git
* Credenciais são carregadas apenas via variáveis de ambiente

---

## Autor

Renan P. De Cesare
Automação de processos em Python aplicada a rotinas de Operações, Risco, Compliance e Dados.

---

## Licença

MIT
