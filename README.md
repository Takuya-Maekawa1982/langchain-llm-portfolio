---
title: Bill Extractor AI
emoji: 🧾
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# Bill Extractor AI

This project started from the code in  
**“The Complete LangChain & LLMs Guide” (Packt Publishing)**  
and has been heavily customized into a practical invoice/bill extraction app.

---

## Overview

Bill Extractor AI takes **bills / invoices** (PDF, images, Excel, Word, plain text),  
extracts raw text, and converts it into **structured JSON** using **LangGraph + LLMs**.

The main target is **Japanese invoices**, but the app also supports **English and other languages** as a fallback.

---

## OCR architecture (A / B / C)

The OCR layer is designed as a **three-tier architecture**:

- **A = PaddleOCR v5 (local, Japanese printed text)**
  - Weights stored under `models/japan/v5_mobile/`
  - Fast, local, optimized for Japanese printed invoices

- **B = Vision LLM (API-based, difficult images)**
  - Uses models defined in `utils/models_vision.py`
  - Instantiated via `utils/model_factory_vision.py`
  - Handles handwritten text, tables, low-quality scans, and complex layouts

- **C = EasyOCR (multilingual fallback)**
  - Used when non-Japanese or simple multilingual OCR is needed
  - Lightweight, local, and good enough for “rough” multilingual extraction

This A/B/C design keeps responsibilities clear:

- **A** → Japanese printed text (fast, local, default)  
- **B** → Hard cases (handwritten, tables, noisy images)  
- **C** → Multilingual fallback (English / others)

---

## High-level architecture

- **UI / entrypoint**
  - `app.py` — main entrypoint (Gradio / web UI)

- **Workflow / graph**
  - `extractors/graph.py` — LangGraph definition
  - `extractors/nodes/` — individual nodes (language detection, correction, summarization, validation, etc.)

- **OCR & file handling**
  - `utils/files.py` — core file handling + OCR logic (A/B/C switching)
  - `models/japan/v5_mobile/` — PaddleOCR v5 Japanese model weights

- **LLM configuration**
  - `utils/models_texts.py` — text LLM model list (free-tier focused)
  - `utils/model_factory_text.py` — text LLM factory
  - `utils/models_vision.py` — vision LLM model list
  - `utils/model_factory_vision.py` — vision LLM factory
  - `utils/keys.py` — API key loading

---

## Supported input formats

Currently supported input types:

- **PDF** (bills, invoices, scanned documents)
- **Images** (JPEG, PNG, etc.)
- **Excel** (`.xlsx`)
- **Word** (`.docx`)
- **Plain text** (`.txt`)

All of these are normalized into **raw text**, then passed through the LangGraph pipeline to produce **structured JSON**.

---

## Running the app (current state)

There are multiple ways to run this app; the exact flow may evolve,  
but the current baseline is:

### 1. Install dependencies

```bash
pip install -r requirements.txt
