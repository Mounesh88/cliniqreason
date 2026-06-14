import sys
import os
import time
import logging
import json
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools.symptom_tool import analyze_symptoms
from mcp_server.tools.risk_tool import assess_risk
from mcp_server.tools.drug_tool import check_drug_interactions
from mcp_server.tools.protocol_tool import match_protocol
from mcp_server.tools.report_tool import compile_report
from database.db import get_connection

# ─────────────────────────────────────────
# VERSIONING
# ─────────────────────────────────────────
ORCHESTRATOR_VERSION = "1.0.0"
TOOL_VERSIONS = {
    "symptom_tool": "1.0.0",
    "risk_tool": "1.0.0",
    "drug_tool": "1.0.0",
    "protocol_tool": "1.0.0",
    "report_tool": "1.0.0"
}

# ─────────────────────────────────────────
# SETUP LOGGING
# ─────────────────────────────────────────
import os as _os
_os.makedirs("audit", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "audit/orchestrator.log",
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger("CliniqReason.Orchestrator")

# ─────────────────────────────────────────
# FEATURE 1 — INPUT VALIDATION
# ─────────────────────────────────────────
def validate_patient_data(data: dict) -> None:
    """
    Validate required patient fields
    Raises ValueError if missing
    """
    required = [
        "age", "gender", "chief_complaint",
        "bp", "hr", "o2", "rr",
        "medications", "history",
        "patient_code", "doctor_code"
    ]
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Validate age is a number
    if not isinstance(data.get("age"), int):
        raise ValueError("Age must be an integer")

    # Validate age is realistic
    if not 0 < data.get("age") < 120:
        raise ValueError("Age must be between 1 and 120")

    logger.info("[VALIDATION] Patient data validated [OK]")

# ─────────────────────────────────────────
# FEATURE 2 — SAFE MODE CHECK
# ─────────────────────────────────────────
def safe_mode_check(text: str, field_name: str, min_length: int = 20) -> bool:
    """
    Check if input text is sufficient for LLM analysis
    Returns True if safe, False if insufficient
    """
    if not text or len(str(text).strip()) < min_length:
        logger.warning(
            f"[SAFE MODE] Insufficient data for {field_name}: "
            f"'{text}' — length {len(str(text)) if text else 0} < {min_length}"
        )
        return False
    return True

# ─────────────────────────────────────────
# FEATURE 3 — WINDOWS COMPATIBLE TIMEOUT
# ─────────────────────────────────────────
def call_with_timeout(func, timeout_seconds=30, **kwargs):
    """
    Windows compatible timeout for LLM calls
    Uses ThreadPoolExecutor
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeout:
            raise TimeoutError(
                f"Tool call timed out after {timeout_seconds}s"
            )

# ─────────────────────────────────────────
# FEATURE 4 — RETRY WITH TIMEOUT
# ─────────────────────────────────────────
def call_with_retry(func, max_retries=2, timeout=60, **kwargs):
    """
    Retry LLM calls with timeout
    """
    for attempt in range(1, max_retries + 1):
        try:
            return call_with_timeout(func, timeout, **kwargs)
        except TimeoutError as e:
            logger.warning(f"Attempt {attempt} timed out: {str(e)}")
            if attempt == max_retries:
                raise e
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:
                raise e
            time.sleep(5 * attempt)

# ─────────────────────────────────────────
# HELPER — Extract field from tool output
# ─────────────────────────────────────────
def extract_field(text: str, field: str) -> str:
    """
    Extract specific field from tool output text
    """
    for line in text.splitlines():
        if field in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    return "Not provided"

# ─────────────────────────────────────────
# FEATURE 5 — SANITY CHECK
# ─────────────────────────────────────────
def sanity_check(results: dict) -> list:
    """
    Check for inconsistencies between agent outputs
    Returns list of warnings
    """
    warnings = []

    symptom = results.get("symptom_analysis", "").lower()
    risk = results.get("risk_assessment", "").lower()

    # Check: Low risk diagnosis but high HEART score
    if "gerd" in symptom and "10" in risk:
        warnings.append(
            "Inconsistency: GERD suggested by Tool 1 "
            "but HEART score 10 from Tool 2"
        )

    # Check: High risk diagnosis but low HEART score
    if "acute coronary" in symptom and "low" in risk:
        warnings.append(
            "Inconsistency: ACS suggested by Tool 1 "
            "but LOW risk from Tool 2"
        )

    # Check: Drug conflict not in protocol
    drug = results.get("drug_interactions", "").lower()
    protocol = results.get("protocol_match", "").lower()

    if "major" in drug and "drug alert" not in protocol:
        warnings.append(
            "Inconsistency: MAJOR drug interaction in Tool 3 "
            "but not addressed in Tool 4 protocol"
        )

    if warnings:
        for w in warnings:
            logger.warning(f"[SANITY CHECK] {w}")
    else:
        logger.info("[SANITY CHECK] No inconsistencies detected [OK]")

    return warnings

# ─────────────────────────────────────────
# FEATURE 6 — CLINICAL SAFETY FILTER
# ─────────────────────────────────────────
def clinical_safety_filter(patient_data: dict, results: dict) -> dict:
    """
    Check critical vital signs and clinical findings
    Add safety flags if high risk detected
    """
    safety_flags = []

    # Extract vitals
    bp = patient_data.get("bp", "")
    hr = patient_data.get("hr", "")
    o2 = patient_data.get("o2", "")
    troponin = patient_data.get("troponin", "").lower()
    symptom = results.get("symptom_analysis", "").lower()

    # Check BP
    try:
        systolic = int(bp.split("/")[0].replace("mmhg", "").strip())
        if systolic < 90:
            safety_flags.append("CRITICAL: Systolic BP < 90 mmHg")
    except:
        pass

    # Check HR
    try:
        heart_rate = int(''.join(filter(str.isdigit, hr.split()[0])))
        if heart_rate > 120:
            safety_flags.append("CRITICAL: Heart Rate > 120 bpm")
    except:
        pass

    # Check O2
    try:
        o2_val = int(''.join(filter(str.isdigit, o2.split("%")[0])))
        if o2_val < 90:
            safety_flags.append("CRITICAL: O2 Saturation < 90%")
    except:
        pass

    # Check Troponin
    if "elevated" in troponin:
        safety_flags.append("CRITICAL: Elevated Troponin detected")

    # Check ACS suspected
    if "acute coronary" in symptom or "myocardial" in symptom:
        safety_flags.append("CRITICAL: ACS suspected — immediate review")

    if safety_flags:
        for flag in safety_flags:
            logger.warning(f"[SAFETY FILTER] {flag}")
        results["safety_flags"] = safety_flags
        results["safety_alert"] = (
            "HIGH-RISK PATIENT DETECTED — "
            "Ensure immediate clinician review"
        )
    else:
        logger.info("[SAFETY FILTER] No critical flags [OK]")
        results["safety_flags"] = []
        results["safety_alert"] = "No critical safety flags detected"

    return results

# ─────────────────────────────────────────
# FEATURE 10 — STRICT MODE TOOL 4 CHECK
# ─────────────────────────────────────────
def strict_mode_check(protocol_output: str) -> str:
    """
    Ensure Tool 4 has not recommended
    specific drug names
    """
    forbidden_drugs = [
        "nitroglycerin", "aspirin", "heparin",
        "beta blocker", "ace inhibitor", "warfarin",
        "metoprolol", "lisinopril", "clopidogrel",
        "ticagrelor", "morphine", "furosemide"
    ]

    output_lower = protocol_output.lower()
    violations = []

    for drug in forbidden_drugs:
        if drug in output_lower:
            violations.append(drug)
            logger.warning(
                f"[STRICT MODE] Tool 4 recommended drug: {drug} "
                f"— this violates safety constraints"
            )

    if violations:
        warning = (
            f"\n[STRICT MODE WARNING] "
            f"Tool 4 mentioned specific drugs: {violations}. "
            f"Senior clinician review required."
        )
        return protocol_output + warning

    logger.info("[STRICT MODE] Tool 4 output passed [OK]")
    return protocol_output

# ─────────────────────────────────────────
# FEATURE 11 — RED FLAG EXTRACTOR
# ─────────────────────────────────────────
def extract_red_flags(symptom_output: str) -> list:
    """
    Extract red flags from Tool 1 output
    """
    red_flags = []
    critical_terms = [
        "diaphoresis", "radiation to jaw", "hypotension",
        "tachycardia", "syncope", "tearing chest pain",
        "shortness of breath", "crushing", "radiation to left arm"
    ]

    output_lower = symptom_output.lower()
    for term in critical_terms:
        if term in output_lower:
            red_flags.append(term)

    if red_flags:
        logger.info(f"[RED FLAGS] Detected: {red_flags}")
    else:
        logger.info("[RED FLAGS] None detected")

    return red_flags

# ─────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────
def run_clinical_assessment(patient_data: dict) -> dict:
    """
    Main Orchestrator — Controls full clinical reasoning flow
    """

    session_start = time.time()
    orchestrator_id = str(uuid.uuid4())[:8].upper()
    step_times = {}

    logger.info("=" * 60)
    logger.info("CLINIQREASON ORCHESTRATOR STARTED")
    logger.info(f"Version         : {ORCHESTRATOR_VERSION}")
    logger.info(f"Orchestrator ID : {orchestrator_id}")
    logger.info(f"Timestamp       : {datetime.now()}")
    logger.info(f"Patient         : {patient_data.get('patient_code')}")
    logger.info(f"Doctor          : {patient_data.get('doctor_code')}")
    logger.info("=" * 60)

    results = {}

    # ─────────────────────────────────────────
    # VALIDATE INPUT
    # ─────────────────────────────────────────
    try:
        validate_patient_data(patient_data)
    except ValueError as e:
        logger.error(f"[VALIDATION] FAILED: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "session_id": None,
            "final_report": None
        }

    # ─────────────────────────────────────────
    # STEP 1 — SYMPTOM ANALYSIS
    # ─────────────────────────────────────────
    logger.info("[STEP 1] Running Symptom Analyzer...")
    step1_start = time.time()

    # Safe mode check
    if not safe_mode_check(
        patient_data.get("chief_complaint"), "chief_complaint", min_length=5
    ):
        results["symptom_analysis"] = (
            "Insufficient data for reliable symptom analysis."
        )
    else:
        try:
            symptom_result = call_with_retry(
                analyze_symptoms,
                chief_complaint=patient_data.get("chief_complaint", "Not provided"),
                age=patient_data.get("age", 0),
                gender=patient_data.get("gender", "Not provided"),
                onset=patient_data.get("onset", "Not provided"),
                duration=patient_data.get("duration", "Not provided"),
                severity=str(patient_data.get("severity", "Not provided")),
                character=str(patient_data.get("character", "Not provided")),
                radiation=str(patient_data.get("radiation", "Not provided")),
                associated_symptoms=str(patient_data.get("associated_symptoms", "Not provided"))
            )
            results["symptom_analysis"] = symptom_result["result"]
        except Exception as e:
            logger.error(f"[STEP 1] FAILED: {str(e)}")
            results["symptom_analysis"] = f"Symptom analysis failed: {str(e)}"

    step_times["step1"] = round(time.time() - step1_start, 2)
    logger.info(f"[STEP 1] Done in {step_times['step1']}s")
    time.sleep(3)

    # ─────────────────────────────────────────
    # STEP 2 — RISK ASSESSMENT
    # ─────────────────────────────────────────
    logger.info("[STEP 2] Running Risk Assessor...")
    step2_start = time.time()

    try:
        risk_result = call_with_retry(
            assess_risk,
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
            history=patient_data.get("history"),
            ecg=patient_data.get("ecg", "Not provided"),
            risk_factors=patient_data.get("risk_factors", "Not provided"),
            troponin=patient_data.get("troponin", "Not provided"),
            bp=patient_data.get("bp"),
            hr=patient_data.get("hr"),
            o2=patient_data.get("o2"),
            rr=patient_data.get("rr"),
            symptom_diagnoses=results["symptom_analysis"]
        )
        results["risk_assessment"] = risk_result["result"]
    except Exception as e:
        logger.error(f"[STEP 2] FAILED: {str(e)}")
        results["risk_assessment"] = f"Risk assessment failed: {str(e)}"

    step_times["step2"] = round(time.time() - step2_start, 2)
    logger.info(f"[STEP 2] Done in {step_times['step2']}s")
    time.sleep(3)
    # ─────────────────────────────────────────
    # STEP 3 — DRUG INTERACTION CHECK
    # ─────────────────────────────────────────
    logger.info("[STEP 3] Running Drug Interaction Checker...")
    step3_start = time.time()

    try:
        drug_result = call_with_retry(
            check_drug_interactions,
            current_medications=patient_data.get("medications"),
            allergies=patient_data.get("allergies", "None known"),
            diagnosis=extract_field(
                results["symptom_analysis"], "1."
            ),
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
            history=patient_data.get("history")
        )
        results["drug_interactions"] = drug_result["result"]
    except Exception as e:
        logger.error(f"[STEP 3] FAILED: {str(e)}")
        results["drug_interactions"] = f"Drug check failed: {str(e)}"

    step_times["step3"] = round(time.time() - step3_start, 2)
    logger.info(f"[STEP 3] Done in {step_times['step3']}s")
    time.sleep(3)

    # ─────────────────────────────────────────
    # STEP 4 — PROTOCOL MATCHING
    # ─────────────────────────────────────────
    logger.info("[STEP 4] Running Protocol Matcher...")
    step4_start = time.time()

    # Extract clean fields from Tool 2
    risk_level = extract_field(
        results["risk_assessment"], "RISK LEVEL"
    )

    triage = extract_field(
        results["risk_assessment"], "TRIAGE DECISION"
    )
    diagnosis = extract_field(
        results["symptom_analysis"], "1."
    )

    # Fallback if not extracted
    if not risk_level or risk_level == "Not provided":
        if "HIGH" in results["risk_assessment"]:
            risk_level = "HIGH"
        elif "MODERATE" in results["risk_assessment"]:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

    if not triage or triage == "Not provided":
        if "IMMEDIATE" in results["risk_assessment"]:
            triage = "IMMEDIATE ER"
        elif "URGENT" in results["risk_assessment"]:
            triage = "URGENT"
        else:
            triage = "OUTPATIENT"

    logger.info(f"[STEP 4] risk_level: {risk_level}")
    logger.info(f"[STEP 4] triage: {triage}")

    try:
        protocol_result = call_with_retry(
            match_protocol,
            diagnosis=diagnosis,
            risk_level=risk_level,
            triage=triage,
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
            history=patient_data.get("history"),
            vitals=(
                f"BP:{patient_data.get('bp')} "
                f"HR:{patient_data.get('hr')} "
                f"O2:{patient_data.get('o2')} "
                f"RR:{patient_data.get('rr')}"
            ),
            drug_alerts=results["drug_interactions"]
        )

        # Strict mode check
        results["protocol_match"] = strict_mode_check(
            protocol_result["result"]
        )

    except Exception as e:
        logger.error(f"[STEP 4] FAILED: {str(e)}")
        results["protocol_match"] = f"Protocol match failed: {str(e)}"

    step_times["step4"] = round(time.time() - step4_start, 2)
    logger.info(f"[STEP 4] Done in {step_times['step4']}s")
    time.sleep(3)
    # ─────────────────────────────────────────
    # SANITY CHECK
    # ─────────────────────────────────────────
    sanity_warnings = sanity_check(results)

    # ─────────────────────────────────────────
    # SAFETY FILTER
    # ─────────────────────────────────────────
    results = clinical_safety_filter(patient_data, results)

    # ─────────────────────────────────────────
    # RED FLAG EXTRACTOR
    # ─────────────────────────────────────────
    red_flags = extract_red_flags(results["symptom_analysis"])
    results["red_flags"] = red_flags

    # ─────────────────────────────────────────
    # STEP 5 — COMPILE FINAL REPORT
    # ─────────────────────────────────────────
    logger.info("[STEP 5] Running Report Compiler...")
    step5_start = time.time()

    try:
        report_result = call_with_retry(
            compile_report,
            patient_code=patient_data.get("patient_code"),
            doctor_code=patient_data.get("doctor_code"),
            symptom_analysis=results["symptom_analysis"],
            risk_assessment=results["risk_assessment"],
            drug_interactions=results["drug_interactions"],
            protocol_match=results["protocol_match"]
        )
        results["final_report"] = report_result["result"]
        results["session_id"] = report_result["session_id"]
    except Exception as e:
        logger.error(f"[STEP 5] FAILED: {str(e)}")
        results["final_report"] = f"Report compilation failed: {str(e)}"

    step_times["step5"] = round(time.time() - step5_start, 2)
    logger.info(f"[STEP 5] Done in {step_times['step5']}s")

    # ─────────────────────────────────────────
    # BUILD REASONING CHAIN
    # ─────────────────────────────────────────
    reasoning_chain = {
        "step1_symptom_analysis": results.get("symptom_analysis"),
        "step2_risk_assessment": results.get("risk_assessment"),
        "step3_drug_interactions": results.get("drug_interactions"),
        "step4_protocol_match": results.get("protocol_match"),
        "sanity_warnings": sanity_warnings,
        "safety_flags": results.get("safety_flags"),
        "red_flags": red_flags,
        "execution_times": step_times,
        "tool_versions": TOOL_VERSIONS,
        "orchestrator_version": ORCHESTRATOR_VERSION
    }

    # ─────────────────────────────────────────
    # SAVE TO DATABASE
    # ─────────────────────────────────────────
    logger.info("[DB] Saving session to database...")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (
                session_id, patient_code, doctor_code,
                symptoms, vitals, medications, history,
                reasoning_chain, final_output, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            results.get("session_id", "N/A"),
            patient_data.get("patient_code"),
            patient_data.get("doctor_code"),
            patient_data.get("chief_complaint"),
            f"BP:{patient_data.get('bp')} HR:{patient_data.get('hr')} O2:{patient_data.get('o2')} Age:{patient_data.get('age')} Gender:{patient_data.get('gender')}",
            patient_data.get("medications"),
            patient_data.get("history"),
            json.dumps(reasoning_chain),
            results.get("final_report"),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        logger.info("[DB] Session saved [OK]")

    except Exception as e:
        logger.error(f"[DB] Save failed: {str(e)}")

    # ─────────────────────────────────────────
    # COMPLETE
    # ─────────────────────────────────────────
    total_time = round(time.time() - session_start, 2)

    logger.info("=" * 60)
    logger.info(f"ASSESSMENT COMPLETE")
    logger.info(f"Total Time      : {total_time}s")
    logger.info(f"Step Times      : {json.dumps(step_times)}")
    logger.info(f"Session ID      : {results.get('session_id')}")
    logger.info(f"Safety Flags    : {results.get('safety_flags')}")
    logger.info(f"Red Flags       : {red_flags}")
    logger.info(f"Sanity Warnings : {sanity_warnings}")
    logger.info("=" * 60)

    return {
        "status": "success",
        "session_id": results.get("session_id"),
        "final_report": results.get("final_report"),
        "reasoning_chain": reasoning_chain,
        "safety_flags": results.get("safety_flags"),
        "safety_alert": results.get("safety_alert"),
        "red_flags": red_flags,
        "sanity_warnings": sanity_warnings,
        "step_times": step_times,
        "total_time": total_time,
        "orchestrator_version": ORCHESTRATOR_VERSION
    }

if __name__ == "__main__":
    test_patient = {
        "patient_code": "PT-DEMO-001",
        "doctor_code": "DR-DEMO-001",
        "age": 65,
        "gender": "Male",
        "chief_complaint": "Chest pain",
        "onset": "2 hours ago",
        "duration": "Continuous",
        "severity": "8",
        "character": "Crushing pressure like",
        "radiation": "Left arm and jaw",
        "associated_symptoms": "Shortness of breath, sweating, nausea",
        "bp": "90/60 mmHg",
        "hr": "110 bpm",
        "o2": "94%",
        "rr": "22 breaths/min",
        "history": "Hypertension, Diabetes, Previous MI 2020, CABG 2020",
        "risk_factors": "Hypertension, Diabetes, Ex-smoker, Family history MI",
        "medications": "Warfarin 5mg, Metformin 500mg, Lisinopril 10mg, Aspirin 81mg",
        "allergies": "Penicillin",
        "ecg": "ST depression V4-V6",
        "troponin": "Elevated 2.3 ng/mL"
    }

    result = run_clinical_assessment(test_patient)
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result["final_report"])
    print(f"\nTotal Time      : {result['total_time']}s")
    print(f"Session ID      : {result['session_id']}")
    print(f"Safety Flags    : {result['safety_flags']}")
    print(f"Red Flags       : {result['red_flags']}")
    print(f"Sanity Warnings : {result['sanity_warnings']}")
    print(f"Step Times      : {json.dumps(result['step_times'], indent=2)}")