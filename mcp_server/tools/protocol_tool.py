import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-12-01-preview"
)

def match_protocol(
    diagnosis: str,
    risk_level: str,
    triage: str,
    age: int,
    gender: str,
    history: str,
    vitals: str,
    drug_alerts: str
) -> dict:
    """
    MCP Tool 4 — Protocol Matcher
    ONE JOB ONLY:
    Match diagnosis to clinical protocol
    Recommend labs, imaging, actions
    Nothing else
    """

    prompt = f"""
    You are a clinical protocol specialist.
    
    YOUR ONLY JOB:
    Match working diagnosis to clinical protocol.
    Recommend specific labs, imaging, and actions.
    DO NOT analyze symptoms.
    DO NOT calculate risk scores.
    DO NOT check drug interactions.
    
    PATIENT DATA:
    ─────────────────────────────
    Working Diagnosis : {diagnosis}
    Risk Level        : {risk_level}
    Triage Decision   : {triage}
    Age               : {age}
    Gender            : {gender}
    Medical History   : {history}
    Current Vitals    : {vitals}
    Drug Alerts       : {drug_alerts}
    
    Match to protocol and return ONLY this:
    
    MATCHED PROTOCOL:
    [Protocol name and version]
    
    IMMEDIATE ACTIONS (Next 0-10 minutes):
    □ [Action 1]
    □ [Action 2]
    □ [Action 3]
    
    URGENT ACTIONS (Next 10-60 minutes):
    □ [Action 1]
    □ [Action 2]
    
    RECOMMENDED LABS:
    □ [Lab test] - [Why needed]
    □ [Lab test] - [Why needed]
    
    RECOMMENDED IMAGING:
    □ [Imaging] - [Why needed]
    □ [Imaging] - [Why needed]
    
    SPECIALIST REFERRAL:
    □ [Specialist] - [Urgency level]
    
    MONITORING REQUIREMENTS:
    □ [What to monitor] - [Frequency]
    
    TREATMENT TARGETS:
    - [Target 1 with specific value]
    - [Target 2 with specific value]
    
    FOLLOW UP TIMELINE:
    - Reassess in: [timeframe]
    - Disposition: [admit/discharge/observe]
    
    SOURCE:
    [Specific guideline with year]
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert clinical protocol specialist.
                Your ONLY job is matching diagnosis to clinical protocols.
                Use ONLY the latest guidelines:
                - AHA/ACC 2022 ACS Guidelines
                - Surviving Sepsis Campaign 2026
                - AHA 2026 Stroke Guidelines
                - ESC PE Guidelines 2024
                Be specific with actions, labs, imaging.
                Time-critical actions must be precise."""
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    return {
        "tool": "protocol_matcher",
        "status": "success",
        "result": response.choices[0].message.content
    }

if __name__ == "__main__":
    result = match_protocol(
        diagnosis="Acute Myocardial Infarction — High likelihood 70%",
        risk_level="HIGH — HEART Score 10",
        triage="IMMEDIATE ER",
        age=65,
        gender="Male",
        history="Hypertension, Diabetes, Previous MI, CABG",
        vitals="BP 90/60, HR 110, O2 94%, RR 22",
        drug_alerts="MAJOR: Warfarin + Aspirin bleeding risk"
    )
    print("=" * 50)
    print("TOOL 4 — PROTOCOL MATCHER OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")