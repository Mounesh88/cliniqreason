import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-12-01-preview"
)

def check_drug_interactions(
    current_medications: str,
    allergies: str,
    diagnosis: str,
    age: int,
    gender: str,
    history: str
) -> dict:
    """
    MCP Tool 3 — Drug Interaction Checker
    ONE JOB ONLY:
    Check medications for interactions
    and contraindications
    Nothing else
    """

    prompt = f"""
    You are a clinical pharmacist specializing in emergency medicine.

    YOUR ONLY JOB:
    Check drug interactions and contraindications.
    DO NOT analyze symptoms.
    DO NOT calculate risk scores.
    DO NOT recommend clinical protocols.
    DO NOT recommend treatment plans or dosing.

    SAFETY CONSTRAINTS — MUST FOLLOW:
    - Never invent medications, interactions, or mechanisms.
      If unsure, say:
      "Insufficient data to determine interaction."
    - If no interactions exist in a category, explicitly write:
      "None found"
    - Do NOT recommend treatment plans or dosing.
    - If allergy relevance is unclear, say:
      "No clear cross-reactivity identified based on provided data."
    - Only flag interactions with known clinical evidence.
    - Never guess or assume interactions without evidence.

    PATIENT DATA:
    ─────────────────────────────
    Age                  : {age}
    Gender               : {gender}
    Medical History      : {history}
    Current Medications  : {current_medications}
    Known Allergies      : {allergies}
    Working Diagnosis    : {diagnosis}

    Return ONLY in this exact format:

    CURRENT MEDICATION REVIEW:
    - [Medication] - [Safe/Caution/Danger]

    DRUG-DRUG INTERACTIONS DETECTED:

    Severity: MAJOR
    - [Drug 1] + [Drug 2] = [Interaction] - [Clinical consequence]
      OR: None found

    Severity: MODERATE
    - [Drug 1] + [Drug 2] = [Interaction] - [Clinical consequence]
      OR: None found

    Severity: MINOR
    - [Drug 1] + [Drug 2] = [Interaction] - [Clinical consequence]
      OR: None found

    CONTRAINDICATIONS FOR WORKING DIAGNOSIS:
    - [Drug that must NOT be given and why]
      OR: None identified

    ALLERGY ALERTS:
    - [Cross-reactivity concern]
      OR: No clear cross-reactivity identified based on provided data

    DOSE ADJUSTMENTS NEEDED:
    - [Drug requiring adjustment and reason]
      OR: None identified

    SAFE ALTERNATIVES:
    - [Safer option if dangerous interaction exists]
      OR: None specifically indicated

    RENAL/HEPATIC CONSIDERATIONS:
    - [Modification needed]
      OR: None identified

    DATA QUALITY CHECK:
    - [Flag any missing medication data]

    SOURCE:
    [FDA Drug Database / RxNorm / NIH reference
    or "Source: Not explicitly specified" if unsure]
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert emergency medicine clinical pharmacist.
                Your ONLY job is drug interaction and contraindication checking.
                Reference FDA Drug Database, RxNorm, and NIH standards.
                Flag ALL major interactions immediately.
                Never invent interactions or mechanisms.
                If unsure say so clearly.
                Never recommend treatments or dosing.
                Patient safety is absolute priority."""
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=800
    )

    return {
        "tool": "drug_checker",
        "status": "success",
        "result": response.choices[0].message.content
    }

if __name__ == "__main__":
    result = check_drug_interactions(
        current_medications="Warfarin 5mg, Metformin 500mg, Lisinopril 10mg, Aspirin 81mg",
        allergies="Penicillin",
        diagnosis="Acute coronary syndrome — suggestive of",
        age=65,
        gender="Male",
        history="Hypertension, Diabetes Type 2, Previous MI 2020, CABG 2020"
    )
    print("=" * 50)
    print("TOOL 3 — DRUG CHECKER OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")