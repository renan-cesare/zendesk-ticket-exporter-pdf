# Zendesk Ticket Exporter (PDF) — Automação de Evidências por Código

> **English summary:** Internal automation that navigates Zendesk (Agent Workspace) via Selenium, enumerates tickets per advisor/client code, and exports each ticket as PDF using Chrome DevTools Protocol (printToPDF). Includes checkpointing, retries, and execution inventory outputs.

---

## 🎯 Contexto (problema real)

Em rotinas de **operações / risco / compliance**, é comum precisar **coletar evidências** de atendimento registradas em tickets do **Zendesk** para:

* auditorias internas
* revisões de conduta
* apurações de reclamações
* dossiês de atendimento e histórico operacional

O problema prático é que:

* A exportação manual ticket por ticket é **lenta, repetitiva e sujeita a erro**
* A base pode conter **centenas ou milhares de tickets** por usuário/código
* A interface do Zendesk é **dinâmica**, com paginação, virtualização e carregamento assíncrono
* Se o navegador cair no meio do processo, **todo o trabalho pode ser perdido**

Este projeto foi construído para **automatizar esse processo de ponta a ponta**, com:

* retomada por checkpoint
* inventário completo de execução
* controle de erros e reprocessamento seguro

---

## ✅ O que o sistema faz

A partir de uma planilha com **códigos internos** (ex.: códigos XP de assessores/usuários), o pipeline:

1. Faz login no Zendesk (Agent Workspace)
2. Abre a área de **People / Clientes**
3. Pesquisa e abre o perfil pelo **código**
4. Acessa a aba **Tickets**
5. Coleta os IDs dos tickets:

   * via paginação quando disponível
   * com fallbacks quando a UI muda
6. Abre a versão de impressão de cada ticket
7. Exporta cada ticket para **PDF** via Chrome DevTools Protocol (`Page.printToPDF`)
8. Registra:

   * progresso em **checkpoint**
   * sucessos e falhas
   * inventário consolidado da execução

---

## 🧠 Por que isso é um projeto real (e não toy project)

Porque resolve um problema **operacional real**:

* Volume grande de dados
* Interface web instável/dinâmica
* Necessidade de **retomada segura**
* Geração de **evidências formais**
* Controle de qualidade e auditoria do que foi exportado

Este tipo de automação é típico de **ferramentas internas corporativas**.

---

## 📦 Saídas geradas (outputs)

Por padrão, o sistema gera uma pasta `output/` com:

* `output/assessor_<CODIGO>/ticket_<ID>.pdf` → PDFs dos tickets
* `output/checkpoint.json` → controle de progresso (retomada)
* `output/success.csv` → tickets exportados com sucesso
* `output/failed.csv` → tickets que falharam + erro
* `output/all_tickets.csv` → inventário consolidado
* `output/summary.json` → resumo final da execução

---

## ⚙️ Requisitos

* Python 3.10+
* Google Chrome instalado
* ChromeDriver compatível com sua versão do Chrome
* Acesso ao Zendesk (Agent Workspace)

---

## 🧪 Instalação

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 🗂️ Planilha de entrada (códigos)

O sistema lê uma planilha Excel (`.xlsx`) contendo uma coluna com **Código XP / Código Interno**.

Ele é tolerante quanto ao nome da coluna e tenta localizar algo como:

* `codigo xp`
* `código xp`
* colunas que contenham `xp` e `cod`

> Recomenda-se manter uma coluna clara chamada `Código XP`.

---

## 🔐 Credenciais e segurança

Este projeto **não deve conter credenciais hardcoded**.

As credenciais são lidas via:

* Variáveis de ambiente:

  * `ZENDESK_EMAIL`
  * `ZENDESK_PASS`

Ou via arquivo `.env` local (ignorado pelo git):

```env
ZENDESK_EMAIL=seu_email@empresa.com
ZENDESK_PASS=sua_senha
```

---

## ⚙️ Configuração

1. Crie um arquivo local baseado no exemplo:

```bash
# Windows:
copy configs\config.example.json configs\config.json

# Linux/Mac:
cp configs/config.example.json configs/config.json
```

2. Edite `configs/config.json` e ajuste principalmente:

* `zendesk.subdomain`
* `paths.excel_codigos`
* `paths.output_dir`
* `paths.chrome_driver_path`

---

## ▶️ Como executar

```bash
python main.py --config configs/config.json
```

Durante a execução, o sistema:

* salva progresso automaticamente
* pode ser interrompido e retomado
* pula tickets já exportados

---

## 🧯 Retomada (checkpoint)

* Se o processo cair no meio, basta rodar novamente.
* O arquivo `checkpoint.json` garante que:

  * códigos já finalizados não são reprocessados
  * tickets já exportados são pulados

Se quiser forçar tudo do zero, use a flag:

```json
"reset_checkpoint": true
```

---

## 🧾 Detalhe técnico: como o PDF é gerado

A exportação não usa “print do sistema”.

O processo é:

1. Abre a URL de impressão do ticket
2. Emula mídia de impressão no Chrome
3. Chama `Page.printToPDF` via Chrome DevTools Protocol
4. Salva o binário em disco
5. Valida rapidamente se o PDF é válido

Isso garante **PDF limpo e consistente**.

---

## 🔒 Sanitização de dados

Este repositório:

* Não contém credenciais reais
* Não contém dados reais
* Não contém PDFs gerados

Pastas e arquivos locais ficam fora do git via `.gitignore`:

* `configs/config.json`
* `data/`
* `output/`
* `.env`

A versão real roda apenas em ambiente interno.

---

## 👨‍💻 Autor

Renan P. De Cesare
Automação corporativa em Python aplicada a rotinas de Operações / Risco / Compliance / Dados.

---

## 📄 Licença

MIT
