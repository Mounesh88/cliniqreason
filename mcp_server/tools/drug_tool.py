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
    Check medications for interactions and contraindications
    Nothing else
    """

    prompt = f"""
    You are a clinical pharmacist specializing in emergency medicine.
    
    YOUR ONLY JOB:
    Check drug interactions and contraindications.
    DO NOT analyze symptoms.
    DO NOT calculate risk scores.
    DO NOT recommend clinical protocols.
    
    PATIENT DATA:
    ─────────────────────────────
    Age                  : {age}
    Gender               : {gender}
    Medical History      : {history}
    Current Medications  : {current_medications}
    Known Allergies      : {allergies}
    Working Diagnosis    : {diagnosis}
    
    Check and return ONLY this:
    
    CURRENT MEDICATION REVIEW:
    - [Medication] - [Dose check] - [Safe/Caution/Danger]
    
    DRUG-DRUG INTERACTIONS DETECTED:
    Severity: MAJOR
    - [Drug 1] + [Drug 2] = [Interaction] - [Clinical consequence]
    
    Severity: MODERATE
    - [Drug 1] + [Drug 2] = [Interaction] - [Clinical consequence]
    
    Severity: MINOR
    - [Drug 1] + [Drug 2] = [Interaction] - [Clinical consequence]
    
    CONTRAINDICATIONS FOR WORKING DIAGNOSIS:
    - [Drug that must NOT be given and why]
    
    ALLERGY ALERTS:
    - [Cross-reactivity or allergy concern]
    
    DOSE ADJUSTMENTS NEEDED:
    - [Drug requiring adjustment based on age/condition]
    
    SAFE ALTERNATIVES:
    - [Safer option if dangerous interaction exists]
    
    RENAL/HEPATIC CONSIDERATIONS:
    - [Any dose modification needed]
    
    SOURCE:
    [FDA Drug Database / RxNorm / NIH reference]
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
                Patient safety is absolute priority.
                Never miss a life threatening drug interaction."""
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
        diagnosis="Acute Myocardial Infarction",
        age=65,
        gender="Male",
        history="Hypertension, Diabetes Type 2, Previous MI 2020, CABG 2020"
    )
    print("=" * 50)
    print("TOOL 3 — DRUG INTERACTION CHECKER OUTPUT")
    print("=" * 50)
    print(result["result"])
    print("=" * 50)
    print(f"Status: {result['status']}")