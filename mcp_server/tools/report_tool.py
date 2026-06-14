import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

_azure_client = None

def get_azure_client():
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            api_version="2024-12-01-preview"
        )
    return _azure_client

def compile_report(
    patient_code: str,
    doctor_code: str,
    symptom_analysis: str,
    risk_assessment: str,
    drug_interactions: str,
    protocol_match: str
) -> dict:
    """
    MCP Tool 5 — Report Compiler
    ONE JOB ONLY:
    Compile all agent outputs into
    final structured clinical report
    Nothing else
    """

    session_id = f"CR-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
    timestamp = datetime.now().strftime("%B %d, %Y %H:%M UTC")

    prompt = f"""
    You are a clinical report compiler.

    YOUR ONLY JOB:
    Compile all agent outputs into one
    clean structured clinical report.
    DO NOT add new medical analysis.
    DO NOT change any clinical findings.
    DO NOT smooth over disagreements.
    ONLY organize and present clearly.

    SAFETY CONSTRAINTS — MUST FOLLOW:
    - Do NOT modify, reinterpret, or correct
      any content from Agents 1-4.
      Copy their findings faithfully.
    - If any field is missing from upstream agents, write:
      "[Not provided by upstream agents]"
    - Do NOT invent guideline sources or citations.
      If none provided, write:
      "Sources: Not explicitly provided in upstream outputs."
    - Use EXACTLY these icons for risk:
      🔴 HIGH
      🟡 MODERATE
      🟢 LOW
      Do NOT introduce new icons.
    - Never smooth over conflicts between agents.
      Present them clearly and explicitly.
    - If agents disagree, show both findings.

    INPUTS FROM ALL AGENTS:
    ─────────────────────────────

    AGENT 1 — SYMPTOM ANALYSIS:
    {symptom_analysis}

    AGENT 2 — RISK ASSESSMENT:
    {risk_assessment}

    AGENT 3 — DRUG INTERACTIONS:
    {drug_interactions}

    AGENT 4 — PROTOCOL MATCH:
    {protocol_match}

    Compile into this EXACT format:

    ════════════════════════════════════════
    CLINIQREASON — PATIENT ASSESSMENT
    ════════════════════════════════════════
    Session ID  : {session_id}
    Timestamp   : {timestamp}
    Patient Code: {patient_code}
    Doctor Code : {doctor_code}
    ════════════════════════════════════════

    RISK LEVEL     : [🔴 HIGH / 🟡 MODERATE / 🟢 LOW]
    TRIAGE         : [Decision]
    HEART SCORE    : [X/10 or Not provided]
    MACE RISK      : [Level or Not provided]
    ════════════════════════════════════════

    DIFFERENTIAL DIAGNOSES:
    1. [Diagnosis] - [%] - [suggestive of/possible/less likely]
    2. [Diagnosis] - [%] - [suggestive of/possible/less likely]
    3. [Diagnosis] - [%] - [suggestive of/possible/less likely]

    LIFE THREATENING TO RULE OUT:
    - [Diagnosis or Not provided]

    RED FLAGS:
    - [Flag or Not provided]

    ════════════════════════════════════════
    REASONING CHAIN:
    Step 1 → Symptom Analysis  : [One line summary]
    Step 2 → Risk Assessment   : [One line summary]
    Step 3 → Drug Check        : [One line summary]
    Step 4 → Protocol Match    : [One line summary]
    ════════════════════════════════════════

    DRUG ALERTS:
    🔴 MAJOR    : [Alert or None found]
    🟡 MODERATE : [Alert or None found]

    AGENT CONFLICTS DETECTED:
    - [Any conflict between agents or None detected]

    ════════════════════════════════════════
    RECOMMENDED ACTIONS:

    IMMEDIATE (0-10 min):
    □ [Action or Not provided]

    URGENT (10-60 min):
    □ [Action or Not provided]

    LABS:
    □ [Lab] - [Reason or Not provided]

    IMAGING:
    □ [Imaging] - [Reason or Not provided]

    SPECIALIST:
    □ [Specialist] - [Urgency or Not provided]

    MONITORING:
    □ [What] - [Frequency or Not provided]
    ════════════════════════════════════════

    SOURCES:
    [1] [Source from agents]
    [2] [Source from agents]
    [3] [Source from agents]
    OR: Sources: Not explicitly provided in upstream outputs.
    ════════════════════════════════════════

    ⚠️  CLINICAL DECISION SUPPORT ONLY
    ⚠️  NOT A MEDICAL DEVICE
    ⚠️  Final judgment rests with clinician
    ⚠️  Powered by Microsoft Foundry IQ
    ════════════════════════════════════════
    """

    response = get_azure_client().chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are a clinical report compiler.
                Your ONLY job is organizing agent outputs
                into a clean structured report.
                Never add new medical analysis.
                Never change clinical findings.
                Never smooth over agent conflicts.
                Never invent sources or citations.
                If data is missing say so explicitly.
                Use only approved risk icons.
                Transparency and auditability are critical."""
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    return {
        "tool": "report_compiler",
        "session_id": session_id,
        "status": "success",
        "result": response.choices[0].message.content
    }

if __name__ == "__main__":
    result = compile_report(
        patient_code="PT-DEMO-001",
        doctor_code="DR-DEMO-001",
        symptom_analysis="""
        DIFFERENTIAL DIAGNOSES:
        1. Acute coronary syndrome - 85% - suggestive of
        2. Acute aortic dissection - 10% - possible
        3. Pulmonary embolism - 5% - possible
        LIFE THREATENING TO RULE OUT: AMI, Aortic Dissection
        RED FLAGS: Crushing chest pain, radiation to left arm
        SOURCE: AHA Guidelines, NIH Clinical Standards
        """,
        risk_assessment="""
        HEART SCORE: 10/10
        RISK LEVEL: HIGH
        MACE PROBABILITY: High short-term risk
        TRIAGE: IMMEDIATE ER
        HEMODYNAMIC STATUS: Unstable
        SOURCE: AHA/ACC 2022 Chest Pain Guidelines
        """,
        drug_interactions="""
        MAJOR: Warfarin + Aspirin = Life threatening hemorrhage risk
        MAJOR: Warfarin + Lisinopril = Enhanced anticoagulant effect
        DOSE ADJUSTMENT: Warfarin — monitor INR
        SOURCE: FDA Drug Database / RxNorm / NIH
        """,
        protocol_match="""
        MATCHED: AHA/ACC 2022 ACS Protocol
        IMMEDIATE: IV access, O2, cardiac monitoring, 12-lead ECG
        LABS: Troponin, CBC, INR, BMP, LFT
        IMAGING: ECG, Echo, Chest X-Ray, Coronary Angiography
        REFERRAL: Cardiology — Immediate
        DRUG ALERT CONFLICTS: Warfarin + Aspirin flagged — senior review required
        SOURCE: AHA/ACC 2022 ACS Guidelines
        """
    )
    print(result["result"])
    print(f"\nSession ID: {result['session_id']}")
    print(f"Status: {result['status']}")