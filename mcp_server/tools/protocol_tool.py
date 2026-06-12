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
    DO NOT recommend specific drug names or doses.

    SAFETY CONSTRAINTS — MUST FOLLOW:
    - Do NOT recommend specific drug names or doses.
      Only actions, labs, imaging, referrals, monitoring.
    - If working diagnosis does not clearly match ACS, PE,
      stroke, or sepsis, say:
      "No single standard protocol clearly applies;
      suggest senior clinician review."
    - If any section has no applicable items, write:
      "None specifically recommended based on provided data."
    - Do NOT contradict drug alerts from Agent 3.
      If standard protocol conflicts with drug alert, say:
      "Standard protocol suggests X, but Agent 3 flagged
      a safety concern — senior clinician review required."
    - Never invent guideline names.
      If unsure of source write:
      "Source: Not explicitly specified."

    PATIENT DATA:
    ─────────────────────────────
    Working Diagnosis : {diagnosis}
    Risk Level        : {risk_level}
    Triage Decision   : {triage}
    Age               : {age}
    Gender            : {gender}
    Medical History   : {history}
    Current Vitals    : {vitals}

    DRUG ALERTS FROM AGENT 3:
    {drug_alerts}

    Return ONLY in this exact format:

    MATCHED PROTOCOL:
    [Protocol name and version
    or "No single standard protocol clearly applies"]

    IMMEDIATE ACTIONS (Next 0-10 minutes):
    □ [Specific action — be precise]
    You MUST provide at least 3 immediate actions
    for HIGH or MODERATE risk patients.
    Only write "None specifically recommended"
    if risk level is LOW.

    URGENT ACTIONS (Next 10-60 minutes):
    □ [Action] OR None specifically recommended

    RECOMMENDED LABS:
    □ [Lab test] - [Why needed]
      OR None specifically recommended

    RECOMMENDED IMAGING:
    □ [Imaging] - [Why needed]
      OR None specifically recommended

    SPECIALIST REFERRAL:
    □ [Specialist] - [Urgency]
      OR None specifically recommended

    MONITORING REQUIREMENTS:
    □ [What to monitor] - [Frequency]
      OR None specifically recommended

    TREATMENT TARGETS:
    - [Target with specific value]
      OR None specifically recommended

    DRUG ALERT CONFLICTS:
    - [Any conflict between protocol and Agent 3 alerts]
      OR None identified

    FOLLOW UP TIMELINE:
    - Reassess in: [timeframe]
    - Disposition: [admit/discharge/observe]

    SOURCE:
    [Specific guideline with year
    or "Source: Not explicitly specified"]
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert clinical protocol specialist.
                Your ONLY job is matching diagnosis to protocols.
                Use ONLY latest guidelines:
                - AHA/ACC 2022 ACS Guidelines
                - Surviving Sepsis Campaign 2026
                - AHA 2026 Stroke Guidelines
                - ESC PE Guidelines 2024
                Never recommend drug names or doses.
                Always respect drug alerts from Agent 3.
                If protocol conflicts with drug alert flag it explicitly.
                Never invent guideline names."""
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
        diagnosis="Acute coronary syndrome — suggestive of — 85%",
        risk_level="HIGH — HEART Score 10/10",
        triage="IMMEDIATE ER",
        age=65,
        gender="Male",
        history="Hypertension, Diabetes, Previous MI, CABG",
        vitals="BP 90/60, HR 110, O2 94%, RR 22",
        drug_alerts="""
        MAJOR: Warfarin + Aspirin = Life threatening hemorrhage risk
        MAJOR: Warfarin + Lisinopril = Enhanced anticoagulant effect
        """
    )
    print("=" * 50)
    print("TOOL 4 — PROTOCOL MATCHER OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")