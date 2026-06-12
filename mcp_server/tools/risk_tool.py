import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-12-01-preview"
)

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
    DO NOT recommend treatments.
    
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
    
    TOP DIAGNOSES FROM SYMPTOM ANALYSIS:
    {symptom_diagnoses}
    
    Calculate and return ONLY this:
    
    HEART SCORE CALCULATION:
    H - History        : [0/1/2] - [reason]
    E - ECG            : [0/1/2] - [reason]
    A - Age            : [0/1/2] - [reason]
    R - Risk Factors   : [0/1/2] - [reason]
    T - Troponin       : [0/1/2] - [reason]
    ─────────────────────────
    TOTAL HEART SCORE  : [0-10]
    
    RISK LEVEL:
    [LOW (0-3) / MODERATE (4-6) / HIGH (7-10)]
    
    MACE PROBABILITY:
    [% risk of major adverse cardiac event in 6 weeks]
    
    TRIAGE DECISION:
    [IMMEDIATE ER / URGENT / OUTPATIENT]
    
    VITAL SIGNS ASSESSMENT:
    - [Critical finding from vitals]
    
    HEMODYNAMIC STATUS:
    [Stable / Unstable / Critical]
    
    SOURCE:
    [AHA/ACC Guideline reference]
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert emergency medicine risk assessor.
                Your ONLY job is HEART score calculation and triage.
                Follow AHA/ACC 2022 Chest Pain Guidelines strictly.
                Be precise with scoring.
                Patient safety is absolute priority."""
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
        symptom_diagnoses="1. Acute MI 70% 2. Unstable Angina 15% 3. Aortic Dissection 5%"
    )
    print("=" * 50)
    print("TOOL 2 — RISK ASSESSOR OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")