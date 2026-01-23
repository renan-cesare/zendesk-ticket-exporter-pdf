# Zendesk Ticket Exporter (PDF) — Automação de Evidências por Código

> **English summary:** Internal automation that navigates Zendesk (Agent Workspace) via Selenium, enumerates tickets per advisor/client code, and exports each ticket as PDF using Chrome DevTools Protocol (printToPDF). Includes checkpointing, retries, and execution inventory outputs.

---

## 🎯 Contexto (problema real)

Em rotinas de **operações / risco / compliance**, é comum precisar **coletar evidências** de atendimento registradas em tickets do **Zendesk** para:

- auditorias internas  
- revisões de conduta  
- apurações de reclamações  
- dossiês de atendimento e histórico operacional  

O problema prático é que:

- A exportação manual ticket por ticket é **lenta, repetitiva e sujeita a erro**  
- A base pode conter **centenas ou milhares de tickets** por usuário/código  
- A interface do Zendesk é **dinâmica**, com paginação, virtualização e carregamento assíncrono  
- Se o navegador cair no meio do processo, **todo o trabalho pode ser perdido**  

Este projeto foi construído para **automatizar esse processo de ponta a ponta**, com:

- retomada por checkpoint  
- inventário completo de execução  
- controle de erros e reprocessamento seguro  

---

## ✅ O que o sistema faz

A partir de uma planilha com **códigos internos** (ex.: códigos XP de assessores/usuários), o pipeline:

1. Faz login no Zendesk (Agent Workspace)
2. Abre a área de **People / Clientes**
3. Pesquisa e abre o perfil pelo **código**
4. Acessa a aba **Tickets**
5. Coleta os IDs dos tickets:
   - via paginação quando disponível  
   - com fallbacks quando a UI muda
6. Abre a versão de impressão de cada ticket
7. Exporta cada ticket para **PDF** via Chrome DevTools Protocol (`Page.printToPDF`)
8. Registra:
   - progresso em **checkpoint**
   - sucessos e falhas
   - inventário consolidado da execução

---

## 🧠 Por que isso é um projeto real (e não toy project)

Porque resolve um problema **operacional real**:

- Volume grande de dados
- Interface web instável/dinâmica
- Necessidade de **retomada segura**
- Geração de **evidências formais**
- Controle de qualidade e auditoria do que foi exportado

Este tipo de automação é típico de **ferramentas internas corporativas**.

---

## 📦 Saídas geradas (outputs)

Por padrão, o sistema gera uma pasta `output/` com:

- `output/assessor_<CODIGO>/ticket_<ID>.pdf` → PDFs dos tickets
- `output/checkpoint.json` → controle de progresso (retomada)
- `output/success.csv` → tickets exportados com sucesso
- `output/failed.csv` → tickets que falharam + erro
- `output/all_tickets.csv` → inventário consolidado
- `output/summary.json` → resumo final da execução

---

## ⚙️ Requisitos

- Python 3.10+
- Google Chrome instalado
- ChromeDriver compatível com sua versão do Chrome
- Acesso ao Zendesk (Agent Workspace)

---

## 🧪 Instalação

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
