# MedoraRx 🏥

> **Translating medical knowledge into every language, one life at a time.**

[![Microsoft Foundry](https://img.shields.io/badge/Azure-AI%20Foundry-0078D4?style=flat&logo=microsoft-azure)](https://ai.azure.com)
[![Foundry IQ](https://img.shields.io/badge/Microsoft-Foundry%20IQ-5C2D91?style=flat&logo=microsoft)](https://aka.ms/iq-series)
[![Track](https://img.shields.io/badge/Track-Reasoning%20Agents-FF6B35?style=flat)](https://aka.ms/agentsleague)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

## 🌍 The Problem

**600 million Hindi speakers have almost no access to WHO-grade medical guidelines in their language.**

When a community health worker in rural India needs to understand antimalarial drug dosages, treatment protocols, or disease prevention guidelines — they face a wall of dense English medical text. Mistranslations in medical literature are not just inconvenient. They can be fatal.

MedoraRx was inspired by a real ongoing project: translating a medical literacy book for a nonprofit community health initiative in India. The challenge wasn't just translation — it was *validated* translation. Medical terms like drug names, dosage units, and clinical terminology require verification, not just word-for-word conversion.

---

## 💡 What is MedoraRx?

MedoraRx is an **agentic AI pipeline** built on **Microsoft Azure AI Foundry** that:

1. Ingests any medical PDF document
2. Translates it from English to Hindi using Azure Translator
3. Validates every medical term against a **Foundry IQ** knowledge base
4. Flags ambiguous terms, drug names, and dosage units for human review
5. Presents a side-by-side reviewed translation with confidence scores

The result: a **human-reviewable, medically validated Hindi translation** — not just a raw machine translation.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MedoraRx Pipeline                       │
└─────────────────────────────────────────────────────────────────┘

  📄 PDF Input (WHO Medical Guidelines)
        │
        ▼
  ┌─────────────────┐
  │  Agent 1        │  • Extracts text preserving structure
  │  PDF Parser     │  • Tags headings, paragraphs, sections
  │                 │  • Identifies medical entity candidates
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Agent 2        │  • Azure Translator (English → Hindi)
  │  Translator     │  • Preserves document structure
  │                 │  • Handles medical terminology context
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐      ┌──────────────────────────────┐
  │  Agent 3        │◄────►│  Foundry IQ Knowledge Base   │
  │  Medical        │      │  • 200+ medical terms        │
  │  Reviewer       │      │  • Hindi equivalents         │
  │                 │      │  • Drug names & dosages      │
  └────────┬────────┘      │  • Confidence scores         │
           │               └──────────────────────────────┘
           ▼
  ┌─────────────────┐
  │  Agent 4        │  • Assembles final review JSON
  │  Report Builder │  • Confidence score per paragraph
  │                 │  • Flags sections for human review
  └────────┬────────┘
           │
           ▼
  ┌───────────────────────────────────────────────────────┐
  │                  React Frontend                       │
  │  ┌─────────────┬──────────────┬────────────────────┐  │
  │  │  Original   │   Hindi      │   Review Panel     │  │
  │  │  English    │ Translation  │  ⚠️ Flagged Terms  │  │
  │  │             │              │  ✅ Verified Terms │  │
  │  └─────────────┴──────────────┴────────────────────┘  │
  └───────────────────────────────────────────────────────┘
```

---

## 🔑 Microsoft IQ Integration

MedoraRx uses **Foundry IQ** as its core intelligence layer:

| Component | Role |
|---|---|
| **Foundry IQ Knowledge Base** | Indexes medical terminology with Hindi translations |
| **Agentic Retrieval** | Agent 3 queries KB for every medical term found in translation |
| **Confidence Scoring** | Each term returned with `high / medium / low` confidence |
| **Reasoning Trace** | UI shows *why* each term was flagged — not just *that* it was flagged |

This is not a superficial integration — Foundry IQ is the reason MedoraRx produces *validated* translations rather than raw machine output.

---

## 🤖 Agent Pipeline Detail

### Agent 1 — PDF Parser
- Extracts text from medical PDF preserving structure
- Tags sections: headings, paragraphs, tables, footnotes
- Uses `pypdf2` for extraction and Azure AI Language for entity recognition
- Output: structured JSON with sections and medical entity candidates

### Agent 2 — Translator
- Calls Azure Translator API (English → Hindi)
- Uses few-shot style guidance for medical context consistency
- Preserves document structure through translation
- Output: translated JSON matching input structure

### Agent 3 — Medical Reviewer *(Foundry IQ)*
- For every medical term identified by Agent 1, queries Foundry IQ
- Validates translated term against knowledge base
- Tags each term: `✅ Verified` / `⚠️ Ambiguous` / `❌ No equivalent found`
- Returns reasoning: *"Drug name — verify transliteration with local pharmacopeia"*
- Output: review JSON with confidence scores and flag reasons

### Agent 4 — Report Builder
- Assembles final output combining translation + review results
- Calculates paragraph-level confidence scores
- Identifies sections requiring urgent human review
- Output: final review-ready JSON for frontend rendering

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Agent Orchestration** | Azure AI Foundry Agent Service |
| **IQ Layer** | Microsoft Foundry IQ (Azure AI Search — Basic) |
| **Translation** | Azure Translator (included in AI Foundry resource) |
| **LLM** | GPT-4o (deployed via Azure AI Foundry) |
| **Backend** | Python 3.14, FastAPI |
| **Frontend** | React 18, TypeScript |
| **PDF Processing** | pypdf2 |
| **Dev Tools** | GitHub Copilot, Claude Code |

---

## 🌐 Azure Resources

| Resource | Name | Region |
|---|---|---|
| Resource Group | MedoraRx-rg | East US |
| AI Foundry | medoraRx-foundry | East US |
| Foundry Project | MedoraRx-project | East US |
| GPT-4o Deployment | gpt-4o (2024-11-20) | Global Standard |
| Foundry IQ Search | medorarx-search | West US 2 |
| Knowledge Base | medorarx-kb | — |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Azure subscription with AI Foundry access
- Azure AI Foundry project with GPT-4o deployed
- Foundry IQ knowledge base configured

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Mayur-b/MedoraRx.git
cd MedoraRx

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your Azure credentials

# Start the backend
cd backend
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Upload Knowledge Base
```bash
cd backend
python foundry_iq/setup_knowledge_base.py
```

---

## 📁 Project Structure

```
MedoraRx/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py                        ← FastAPI orchestrator
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   ├── parser_agent.py            ← Agent 1: PDF Parser
│   │   ├── translator_agent.py        ← Agent 2: Translator
│   │   ├── reviewer_agent.py          ← Agent 3: Medical Reviewer
│   │   └── report_builder.py          ← Agent 4: Report Builder
│   ├── foundry_iq/
│   │   └── setup_knowledge_base.py    ← KB indexing script
│   └── tests/
│       ├── test_openai.py
│       └── test_translator.py
├── frontend/
│   └── src/
│       ├── App.tsx
│       └── components/
│           ├── PDFUploader.tsx
│           ├── TranslationViewer.tsx  ← 3-panel side-by-side viewer
│           └── FlaggedTerms.tsx
└── data/
    ├── medical_glossary.json          ← 200 medical terms EN→HI
    └── sample/
        └── who_malaria_guidelines_2025.pdf
```

---

## 🎯 Demo

> Demo video: [Link to be added before submission]

**Demo input:** WHO Guidelines for Malaria (August 2025, 478 pages)
**Demo scope:** Chapter 1 processed end-to-end
**Demo output:** Side-by-side Hindi translation with 47 flagged medical terms

---

## 🌱 Real-World Impact

MedoraRx was inspired by an active nonprofit initiative translating medical literacy books for underserved communities in India. The demo uses WHO's publicly licensed Malaria Guidelines (CC BY-NC-SA 3.0 IGO). The pipeline is language-agnostic and can be extended to any target language supported by Azure Translator.

**Potential reach:**
- 600M+ Hindi speakers
- 500M+ Bengali speakers
- 250M+ Marathi and Telugu speakers
- Any language in Azure Translator's 100+ supported languages

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

Demo data: WHO Guidelines for Malaria © World Health Organization, licensed under CC BY-NC-SA 3.0 IGO.
