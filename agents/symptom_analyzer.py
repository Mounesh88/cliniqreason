import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version="2024-12-01-preview"
)

def analyze_symptoms(patient_data):
    prompt = f"""
    You are an expert emergency medicine clinical decision support AI.
    Analyze the following comprehensive patient data:
    
    ─── PATIENT DEMOGRAPHICS ───
    Age: {patient_data.get('age')}
    Gender: {patient_data.get('gender')}
    Weight: {patient_data.get('weight', 'Not provided')}
    Pregnancy Status: {patient_data.get('pregnancy', 'N/A')}
    
    ─── CHIEF COMPLAINT ───
    Main Symptom: {patient_data.get('chief_complaint')}
    Onset: {patient_data.get('onset')}
    Duration: {patient_data.get('duration')}
    Severity (1-10): {patient_data.get('severity')}
    Character: {patient_data.get('character')}
    Radiation: {patient_data.get('radiation', 'None')}
    
    ─── ASSOCIATED SYMPTOMS ───
    {patient_data.get('associated_symptoms')}
    
    ─── AGGRAVATING FACTORS ───
    {patient_data.get('aggravating_factors', 'None reported')}
    
    ─── RELIEVING FACTORS ───
    {patient_data.get('relieving_factors', 'None reported')}
    
    ─── VITAL SIGNS ───
    Blood Pressure: {patient_data.get('bp')}
    Heart Rate: {patient_data.get('hr')}
    Temperature: {patient_data.get('temp')}
    O2 Saturation: {patient_data.get('o2')}
    Respiratory Rate: {patient_data.get('rr', 'Not provided')}
    GCS Score: {patient_data.get('gcs', 'Not provided')}
    
    ─── MEDICAL HISTORY ───
    Past Conditions: {patient_data.get('history')}
    Previous Surgeries: {patient_data.get('surgeries', 'None')}
    Family History: {patient_data.get('family_history', 'Not provided')}
    
    ─── SOCIAL HISTORY ───
    Smoking: {patient_data.get('smoking', 'Not provided')}
    Alcohol: {patient_data.get('alcohol', 'Not provided')}
    
    ─── MEDICATIONS & ALLERGIES ───
    Current Medications: {patient_data.get('medications')}
    Allergies: {patient_data.get('allergies', 'NKDA')}
    
    Provide a comprehensive clinical assessment in this exact format:
    
    DIAGNOSES:
    1. [Diagnosis] - [Likelihood %] - [High/Moderate/Low]
    2. [Diagnosis] - [Likelihood %] - [High/Moderate/Low]
    3. [Diagnosis] - [Likelihood %] - [High/Moderate/Low]
    
    RED FLAGS DETECTED:
    - [Red flag with clinical significance]
    
    CONTRAINDICATIONS DETECTED:
    - [What NOT to give this patient and why]
    
    URGENCY INDICATORS:
    - [Time critical finding]
    
    TIME CRITICAL ACTIONS (Next 10 minutes):
    - [Immediate action required]
    
    CLINICAL SCORES:
    - HEART Score: [0-10] - [Risk level]
    - CURB-65: [if applicable]
    - Other relevant scores
    
    MISSING CRITICAL INFORMATION:
    - [What else is urgently needed]
    
    DIAGNOSES TO RULE OUT:
    - [Important differential to exclude]
    
    FOLLOW UP TIMELINE:
    - Reassess in: [timeframe]
    - Specialist referral: [urgency]
    
    CLINICAL SUMMARY:
    [Comprehensive clinical summary]
    
    ⚠️ DISCLAIMER:
    This is a clinical decision support tool only.
    Not a medical device.
    Final diagnosis and treatment decisions rest with the treating clinician.
    """

    response = client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert clinical decision support AI trained in 
                emergency medicine, internal medicine, and general practice. 
                You follow AHA, NIH, WHO and Mayo Clinic guidelines strictly.
                Always be precise, evidence-based and clinically accurate.
                Never guess — flag uncertainty clearly.
                Patient safety is the absolute priority."""
            },
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    # Comprehensive test patient
    test_patient = {
        "age": 65,
        "gender": "Male",
        "weight": "85kg",
        "pregnancy": "N/A",
        "chief_complaint": "Chest pain",
        "onset": "2 hours ago",
        "duration": "Continuous",
        "severity": "8/10",
        "character": "Crushing, pressure-like",
        "radiation": "Left arm and jaw",
        "associated_symptoms": "Shortness of breath, diaphoresis, nausea",
        "aggravating_factors": "Any movement, deep breathing",
        "relieving_factors": "Nothing relieves it",
        "bp": "90/60 mmHg",
        "hr": "110 bpm",
        "temp": "37.2°C",
        "o2": "94%",
        "rr": "22 breaths/min",
        "gcs": "15",
        "history": "Hypertension, Diabetes Type 2, Previous MI 2020",
        "surgeries": "CABG 2020",
        "family_history": "Father died of MI at 60",
        "smoking": "Ex-smoker 20 pack years",
        "alcohol": "Occasional",
        "medications": "Warfarin 5mg, Metformin 500mg, Lisinopril 10mg, Aspirin 81mg",
        "allergies": "Penicillin"
    }

    result = analyze_symptoms(test_patient)
    print(result)