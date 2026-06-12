import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-12-01-preview"
)

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
    ONLY organize and present clearly.
    
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
    HEART SCORE    : [X/10]
    MACE RISK      : [%]
    CONFIDENCE     : [%]
    ════════════════════════════════════════
    
    DIFFERENTIAL DIAGNOSES:
    1. [Diagnosis] - [%]
    2. [Diagnosis] - [%]
    3. [Diagnosis] - [%]
    
    LIFE THREATENING TO RULE OUT:
    - [Diagnosis]
    
    RED FLAGS:
    - [Flag]
    
    ════════════════════════════════════════
    REASONING CHAIN:
    Step 1 → Symptom Analysis  : [Summary]
    Step 2 → Risk Assessment   : [Summary]
    Step 3 → Drug Check        : [Summary]
    Step 4 → Protocol Match    : [Summary]
    ════════════════════════════════════════
    
    DRUG ALERTS:
    🔴 MAJOR    : [Alert]
    🟡 MODERATE : [Alert]
    
    ════════════════════════════════════════
    RECOMMENDED ACTIONS:
    
    IMMEDIATE (0-10 min):
    □ [Action]
    
    URGENT (10-60 min):
    □ [Action]
    
    LABS:
    □ [Lab] - [Reason]
    
    IMAGING:
    □ [Imaging] - [Reason]
    
    SPECIALIST:
    □ [Specialist] - [Urgency]
    
    MONITORING:
    □ [What] - [Frequency]
    ════════════════════════════════════════
    
    SOURCES:
    [1] [Source]
    [2] [Source]
    [3] [Source]
    ════════════════════════════════════════
    
    ⚠️  CLINICAL DECISION SUPPORT ONLY
    ⚠️  NOT A MEDICAL DEVICE
    ⚠️  Final judgment rests with clinician
    ⚠️  Powered by Microsoft Foundry IQ
    ════════════════════════════════════════
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are a clinical report compiler.
                Your ONLY job is organizing agent outputs
                into a clean structured report.
                Never add new medical analysis.
                Never change clinical findings.
                Make it clear, readable, actionable.
                Explainability and transparency are critical."""
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
    # Test with sample outputs from all 4 tools
    result = compile_report(
        patient_code="PT-DEMO-001",
        doctor_code="DR-DEMO-001",
        symptom_analysis="""
        DIFFERENTIAL DIAGNOSES:
        1. Acute Myocardial Infarction - 70%
        2. Unstable Angina - 15%
        3. Aortic Dissection - 5%
        LIFE THREATENING TO RULE OUT: AMI, Aortic Dissection
        RED FLAGS: Crushing chest pain, radiation to left arm
        """,
        risk_assessment="""
        HEART SCORE: 10/10
        RISK LEVEL: HIGH
        MACE PROBABILITY: ≥50%
        TRIAGE: IMMEDIATE ER
        HEMODYNAMIC STATUS: Unstable
        """,
        drug_interactions="""
        MAJOR: Warfarin + Aspirin = Life threatening hemorrhage risk
        MAJOR: Warfarin + Lisinopril = Hyperkalemia risk
        DOSE ADJUSTMENT: Warfarin — monitor INR
        """,
        protocol_match="""
        MATCHED: AHA/ACC 2022 ACS Protocol
        IMMEDIATE: IV access, O2, 12-lead ECG
        LABS: Troponin, CBC, INR, BMP
        IMAGING: Echo, Chest X-Ray
        REFERRAL: Cardiology — Immediate
        """
    )
    print(result["result"])
    print(f"\nSession ID: {result['session_id']}")
    print(f"Status: {result['status']}")