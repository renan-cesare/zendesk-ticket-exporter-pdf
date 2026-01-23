# Zendesk Ticket Exporter (PDF) — Automação de Evidências por Código

> **English summary:** Internal automation that navigates Zendesk (Agent Workspace) via Selenium, enumerates tickets per advisor/client code, and exports each ticket as PDF using Chrome DevTools Protocol (printToPDF). Includes checkpointing, retries, and execution inventory outputs.

## Contexto (problema real)

Em rotinas de **operações / risco / compliance**, é comum precisar coletar **evidências** (histórico de atendimento) registradas em tickets do **Zendesk** para auditorias e revisões internas.

O problema prático é que:
- exportar tickets manualmente é lento e repetitivo;
- há grande volume de tickets por código/usuário;
- a UI do Zendesk é dinâmica (paginação/virtualização);
- quedas do navegador no meio do processo causam retrabalho.

Este projeto automatiza o processo de ponta a ponta com **retomada por checkpoint** e **inventário completo** do que existia vs. foi exportado.

## O que o sistema faz

A partir de uma planilha com **códigos** (ex.: códigos XP):

1. Faz login no Zendesk (Agent)
2. Abre **People/Clientes**
3. Pesquisa e abre o usuário pelo código
4. Acessa a aba **Tickets**
5. Coleta IDs de tickets (paginação + fallbacks)
6. Exporta cada ticket via tela de impressão para **PDF** (CDP `Page.printToPDF`)
7. Gera:
   - checkpoint (retomada)
   - logs
   - inventário consolidado
   - success/failed

## Saídas geradas (outputs)

Por padrão o pipeline escreve em `output/`:

- `output/assessor_<CODIGO>/ticket_<ID>.pdf`
- `output/checkpoint.json`
- `output/run.log`
- `output/success.csv`
- `output/failed.csv`
- `output/all_tickets.csv`
- `output/summary.json`

## Requisitos

- Python 3.10+
- Google Chrome instalado
- ChromeDriver compatível com sua versão do Chrome
- Acesso ao Zendesk (Agent)

## Instalação

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
