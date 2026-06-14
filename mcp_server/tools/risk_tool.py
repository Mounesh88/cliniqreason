import os
from openai import AzureOpenAI
from dotenv import load_dotenv

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

def assess_risk(
    age: int,
    gender: str,
    history: str,
    ecg: str,
    risk_factors: str,
    troponin: str,
    bp: str,
    hr: str,
    o2: str,
    rr: str,
    symptom_diagnoses: str
) -> dict:
    """
    MCP Tool 2 — Risk Assessor
    ONE JOB ONLY:
    Calculate HEART score and assign triage level
    Nothing else
    """

    prompt = f"""
    You are a clinical risk assessment specialist.

    YOUR ONLY JOB:
    Calculate HEART score and assign triage level.
    DO NOT analyze symptoms.
    DO NOT check drugs.
    DO NOT recommend treatments or medications.
    DO NOT reinterpret or change diagnoses from Agent 1.
    Use diagnoses from Agent 1 ONLY as context.

    SAFETY CONSTRAINTS — MUST FOLLOW:
    - Use official HEART components ONLY:
      History, ECG, Age, Risk factors, Troponin.
    - HEART score interpretation:
      0-3  = LOW risk      (typically <3% MACE at 6 weeks)
      4-6  = MODERATE risk (intermediate risk)
      7-10 = HIGH risk     (high short-term risk)
    - If troponin is missing or unclear, say:
      "Troponin data insufficient for accurate HEART scoring."
    - Do NOT reinterpret or change diagnoses from Agent 1.
      Use them only as context.
    - Do NOT recommend medications or treatments.
    - MACE probability must follow HEART score ranges strictly.

    PATIENT DATA:
    ─────────────────────────────
    Age             : {age}
    Gender          : {gender}
    Medical History : {history}
    ECG Findings    : {ecg}
    Risk Factors    : {risk_factors}
    Troponin        : {troponin}

    VITAL SIGNS:
    BP              : {bp}
    HR              : {hr}
    O2 Saturation   : {o2}
    Resp Rate       : {rr}

    DIAGNOSES FROM AGENT 1 (context only):
    {symptom_diagnoses}

    Return ONLY in this exact format:

    HEART SCORE CALCULATION:
    H - History        : [0/1/2] - [reason]
    E - ECG            : [0/1/2] - [reason]
    A - Age            : [0/1/2] - [reason]
    R - Risk Factors   : [0/1/2] - [reason]
    T - Troponin       : [0/1/2 or "Insufficient data"]
    ─────────────────────────
    TOTAL HEART SCORE  : [0-10]

    RISK LEVEL:
    [LOW (0-3) / MODERATE (4-6) / HIGH (7-10)]

    MACE PROBABILITY:
    [Based strictly on HEART score range:
     LOW: typically <3% at 6 weeks
     MODERATE: intermediate risk
     HIGH: high short-term risk]

    TRIAGE DECISION:
    [IMMEDIATE ER / URGENT / OUTPATIENT]

    VITAL SIGNS ASSESSMENT:
    - [Critical finding from vitals]

    HEMODYNAMIC STATUS:
    [Stable / Unstable / Critical]

    DATA QUALITY CHECK:
    - [Flag any missing data affecting score accuracy]

    SOURCE:
    [AHA/ACC Guideline reference or
    "Source: Not explicitly specified" if unsure]
    """

    response = get_azure_client().chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert emergency medicine risk assessor.
                Your ONLY job is HEART score calculation and triage.
                Follow AHA/ACC 2022 Chest Pain Guidelines strictly.
                Use ONLY official HEART components.
                Never recommend medications or treatments.
                Never change Agent 1 diagnoses.
                If troponin data is missing say so clearly.
                MACE probability must match HEART score ranges exactly."""
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )

    return {
        "tool": "risk_assessor",
        "status": "success",
        "result": response.choices[0].message.content
    }

if __name__ == "__main__":
    result = assess_risk(
        age=65,
        gender="Male",
        history="Hypertension, Diabetes, Previous MI 2020, CABG 2020",
        ecg="ST depression in leads V4-V6",
        risk_factors="Hypertension, Diabetes, Ex-smoker, Family history of MI",
        troponin="Elevated — 2.3 ng/mL",
        bp="90/60 mmHg",
        hr="110 bpm",
        o2="94%",
        rr="22 breaths/min",
        symptom_diagnoses="""
        1. Acute coronary syndrome - 85% - suggestive of
        2. Acute aortic dissection - 10% - possible
        3. Pulmonary embolism - 5% - possible
        """
    )
    print("=" * 50)
    print("TOOL 2 — RISK ASSESSOR OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")