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

def analyze_symptoms(
    chief_complaint: str,
    age: int,
    gender: str,
    onset: str,
    duration: str,
    severity: str,
    character: str,
    radiation: str,
    associated_symptoms: str
) -> dict:
    """
    MCP Tool 1 — Symptom Analyzer
    ONE JOB ONLY:
    Map symptoms to ranked differential diagnoses
    Nothing else
    """

    prompt = f"""
    You are a clinical symptom analyzer.

    YOUR ONLY JOB:
    Analyze symptoms and return ranked differential diagnoses.
    DO NOT assess risk.
    DO NOT check drugs.
    DO NOT recommend actions.
    DO NOT calculate scores.

    SAFETY CONSTRAINTS — MUST FOLLOW:
    - Do NOT state any diagnosis as confirmed.
      Only likelihood-based differentials.
    - Likelihood percentages must be between 0% and 100%.
    - If symptom data is insufficient, say:
      "Insufficient data for reliable differential diagnosis."
    - Do NOT invent guideline names. If unsure of source, write:
      "Source: Not explicitly specified."
    - Never present a diagnosis as definitive.
      Always use language like:
      "consistent with", "suggestive of", "possible", "likely"

    PATIENT SYMPTOMS:
    ─────────────────────────────
    Chief Complaint : {chief_complaint}
    Age             : {age}
    Gender          : {gender}
    Onset           : {onset}
    Duration        : {duration}
    Severity        : {severity}/10
    Character       : {character}
    Radiation       : {radiation}
    Associated      : {associated_symptoms}

    Return ONLY in this exact format:

    DIFFERENTIAL DIAGNOSES:
    1. [Diagnosis] - [likelihood %] - suggestive of
    2. [Diagnosis] - [likelihood %] - possible
    3. [Diagnosis] - [likelihood %] - possible
    4. [Diagnosis] - [likelihood %] - less likely
    5. [Diagnosis] - [likelihood %] - less likely

    LIFE THREATENING TO RULE OUT URGENTLY:
    - [Diagnosis that must never be missed]
    - [Diagnosis that must never be missed]

    SYMPTOM PATTERNS DETECTED:
    - [Clinical pattern observed]

    ATYPICAL FEATURES:
    - [Anything unusual about presentation]

    DATA QUALITY CHECK:
    - [Flag any missing or insufficient symptom data]

    SOURCE:
    [Clinical guideline this is based on,
    or "Source: Not explicitly specified" if unsure]
    """

    response = get_azure_client().chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert clinical symptom analyzer.
                Your ONLY job is differential diagnosis ranking.
                Base all responses on:
                - AHA Guidelines
                - NIH Clinical Standards
                - Mayo Clinic Protocols
                - NHAMCS real world data
                Be precise. Be evidence based.
                Never miss life threatening diagnoses.
                Never confirm a diagnosis — only suggest likelihood.
                If data is insufficient, say so clearly.
                Never invent guideline names or sources."""
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )

    return {
        "tool": "symptom_analyzer",
        "status": "success",
        "result": response.choices[0].message.content
    }

if __name__ == "__main__":
    result = analyze_symptoms(
        chief_complaint="Chest pain",
        age=65,
        gender="Male",
        onset="2 hours ago",
        duration="Continuous",
        severity="8",
        character="Crushing pressure like",
        radiation="Left arm and jaw",
        associated_symptoms="Shortness of breath, sweating, nausea"
    )
    print("=" * 50)
    print("TOOL 1 — SYMPTOM ANALYZER OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")