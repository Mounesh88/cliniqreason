# CliniqReason — Clinical Decision Reasoning Agent

> **Agents League Hackathon 2026** | Microsoft B2B Connect | Challenge 2: Reasoning Agents

---

## 🌐 Live Demo (Azure Deployment)

👉 **[https://cliniqreason-production.up.railway.app](https://cliniqreason-production.up.railway.app)**

```
Doctor ID : DR-DEMO-001
Password  : demo123
```

> ⚠️ Analysis takes ~90 seconds — Microsoft Foundry IQ runs 5 specialized agents sequentially.

---

## 🧪 How to Test (For Judges)

1. Open the **Live Demo** link above
2. Login: `DR-DEMO-001` / `demo123`
3. Click **New Case** in the sidebar
4. Fill patient details OR upload a PDF/Word patient file
5. Click **ANALYZE PATIENT**
6. Wait ~90 seconds for the 5-agent pipeline to complete
7. Click each agent chip to see individual findings
8. Click **View Full Dashboard**
9. Explore all screens:
   - 📊 **Dashboard** — Full clinical assessment with real AI data
   - 👥 **Patients** — Patient history across all sessions
   - 📈 **Reports** — Power BI-style analytics charts
   - 📋 **Protocols** — AHA/ACC matched protocol cards
   - 📖 **Guidelines** — Evidence-based guideline matching
   - 🔍 **Audit Trail** — Complete session log with filters

---

## 🏥 What is CliniqReason?

CliniqReason is an **AI-powered Clinical Decision Reasoning Agent** that assists emergency medicine clinicians in making faster, safer, and more accurate clinical decisions. It uses a **5-agent MCP architecture** powered by **Microsoft Foundry IQ** to analyze patient data through multiple specialized AI agents simultaneously.

> ⚠️ **Not a Medical Device** — Clinical Decision Support Tool Only. Final judgment rests with the treating clinician.

---

## 🎯 Problem Statement

Emergency physicians face:
- **Information overload** — multiple data sources, medications, vitals
- **Time pressure** — critical decisions in minutes
- **Drug interaction risks** — complex polypharmacy
- **Protocol complexity** — constantly updated clinical guidelines

CliniqReason solves this by providing **instant, explainable AI reasoning** across all clinical dimensions simultaneously.

---

## 🤖 Multi-Agent Architecture

```
Patient Data Input
       ↓
┌─────────────────────────────────────────┐
│         CLINIQREASON ORCHESTRATOR        │
│                                          │
│  Agent 1: Symptom Analyzer              │
│  → Differential diagnoses ranked by %   │
│                                          │
│  Agent 2: Risk Assessor                 │
│  → HEART score + triage level           │
│                                          │
│  Agent 3: Drug Interaction Checker      │
│  → MAJOR/MODERATE/MINOR alerts          │
│                                          │
│  Agent 4: Protocol Matcher              │
│  → AHA/ACC guideline matching           │
│                                          │
│  Agent 5: Report Compiler               │
│  → Final structured clinical report     │
│                                          │
│  Cross-Agent Consistency Check          │
│  Safety Filter + Red Flag Extractor     │
└─────────────────────────────────────────┘
       ↓
Clinical Dashboard + Audit Trail
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔬 **5 Specialized Agents** | Each agent focuses on one clinical domain |
| 🧠 **Explainable AI** | Full reasoning chain visible to clinician |
| ⚡ **Real-time Analysis** | Results in ~90 seconds |
| 💊 **Drug Safety** | Detects MAJOR/MODERATE/MINOR interactions |
| 📋 **Protocol Matching** | AHA/ACC 2022 guideline alignment |
| 🔴 **Safety Flags** | Critical alerts for high-risk findings |
| 📊 **Analytics Dashboard** | Power BI-style clinical intelligence |
| 🖨️ **Print Reports** | Professional single-page clinical report |
| 📄 **PDF/Word Upload** | Auto-fill patient data from documents |
| 🔒 **Audit Trail** | Complete HIPAA-aligned session logging |

---

## 🖥️ Application Screens

| Screen | Description |
|---|---|
| Login | Secure clinician authentication with forgot password |
| New Case | Patient data entry + PDF/Word file upload |
| Analyze | Live agent progress with clickable findings per agent |
| Dashboard | Full clinical assessment — risk, diagnoses, drugs, reasoning |
| Patients | All unique patients with session history |
| Reports | Power BI-style charts — risk trends, diagnoses, drug alerts |
| Protocols | AHA/ACC matched protocols + reference cards |
| Guidelines | Evidence-based guidelines matched to current patient |
| Audit Trail | Complete HIPAA-aligned session log with search and filters |

---

## 🚀 Quick Start (Local)

```bash
# Clone repository
git clone https://github.com/Mounesh88/cliniqreason.git
cd cliniqreason

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Run
python main.py
```

Open `http://127.0.0.1:5000`

---

## ⚙️ Environment Variables

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
SECRET_KEY=your-secret-key
DATABASE_NAME=cliniqreason.db
```

---

## 🔑 Demo Credentials & Sample Patient

```
Doctor ID : DR-DEMO-001
Password  : demo123

--- Sample Patient ---
Patient Code : PT-DEMO-001
Age          : 65 years | Male
Complaint    : Chest pain — crushing, radiating to left arm
BP           : 90/60 mmHg | HR: 110 bpm | O2: 94%
Medications  : Warfarin 5mg, Metformin 500mg, Lisinopril 10mg, Aspirin 81mg
ECG          : ST depression V4-V6
Troponin     : Elevated 2.3 ng/mL
History      : Hypertension, Diabetes, Previous MI 2020
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **AI Intelligence** | Microsoft Foundry IQ (Azure OpenAI GPT-4.1-mini) |
| **Agent Framework** | MCP (Model Context Protocol) — 5 specialized agents |
| **Backend** | Python 3.13, Flask 3.1 |
| **Database** | SQLite |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **PDF Processing** | pdfplumber, python-docx |
| **Deployment** | Azure App Service |

---

## 📁 Project Structure

```
cliniqreason/
├── main.py                    # Flask app + all routes
├── agents/
│   └── orchestrator.py        # 5-agent orchestrator with safety checks
├── mcp_server/
│   └── tools/
│       ├── symptom_tool.py    # Agent 1 — Symptom Analyzer
│       ├── risk_tool.py       # Agent 2 — Risk Assessor
│       ├── drug_tool.py       # Agent 3 — Drug Interaction Checker
│       ├── protocol_tool.py   # Agent 4 — Protocol Matcher
│       └── report_tool.py     # Agent 5 — Report Compiler
├── database/
│   └── db.py                  # SQLite database setup
├── ui/
│   ├── templates/             # 9 HTML screens
│   └── static/css/            # Local Tabler icons
└── audit/
    └── orchestrator.log       # Full audit log
```

---

## 🔒 Safety & Compliance

- ✅ **Not a Medical Device** disclaimer on every screen
- ✅ **HIPAA-aligned** audit logging for every session
- ✅ **Senior clinician review** required for all outputs
- ✅ **Strict mode** — Agent 4 blocked from recommending specific drugs
- ✅ **Cross-agent sanity checks** — consistency validation
- ✅ **Safety filter** — Critical vital sign threshold alerts
- ✅ **Red flag extraction** — Auto-detects 9 critical symptom patterns

---

## ⚠️ Known Limitations

- Not a medical device — for decision support only
- Uses synthetic demo data — no real patient records
- No real EHR / HL7 / FHIR integration
- Limited to emergency medicine scenarios
- Analysis takes ~90 seconds per patient
- Not intended for real clinical use without proper validation

---

## 👨‍💻 Developer

**Mounesh Rayalla**
- GitHub: [@Mounesh88](https://github.com/Mounesh88)
- Hackathon: Agents League 2026 — Microsoft B2B Connect
- Track: Challenge 2 — Reasoning Agents (Microsoft Foundry IQ)

---

*⚠️ CliniqReason is a Clinical Decision Support Tool Only — Not a Medical Device — Powered by Microsoft Foundry IQ*