import sys
import os
import time
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mcp_server.tools.symptom_tool import analyze_symptoms
from mcp_server.tools.risk_tool import assess_risk
from mcp_server.tools.drug_tool import check_drug_interactions
from mcp_server.tools.protocol_tool import match_protocol
from mcp_server.tools.report_tool import compile_report

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(stream=open(sys.stdout.fileno(), 
            mode='w', encoding='utf-8', closefd=False)),
        logging.FileHandler("audit/mcp_server.log", encoding='utf-8')
    ]
)
logger = logging.getLogger("CliniqReason")

# Initialize MCP Server
mcp = FastMCP("CliniqReason Medical MCP Server")

@mcp.tool()
def tool_analyze_symptoms(
    chief_complaint: str,
    age: int,
    gender: str,
    onset: str,
    duration: str,
    severity: str,
    character: str,
    radiation: str,
    associated_symptoms: str
) -> str:
    """
    Analyze patient symptoms and return
    ranked differential diagnoses.
    """
    logger.info(f"[TOOL 1] analyze_symptoms called")
    logger.info(f"[TOOL 1] chief_complaint={chief_complaint}")
    logger.info(f"[TOOL 1] age={age} gender={gender}")
    start = time.time()

    try:
        result = analyze_symptoms(
            chief_complaint=chief_complaint,
            age=age,
            gender=gender,
            onset=onset,
            duration=duration,
            severity=severity,
            character=character,
            radiation=radiation,
            associated_symptoms=associated_symptoms
        )
        duration = round(time.time() - start, 2)
        logger.info(f"[TOOL 1] completed in {duration}s ✅")
        return result["result"]

    except Exception as e:
        logger.error(f"[TOOL 1] FAILED: {str(e)}")
        return f"Tool 1 error: {str(e)}"

@mcp.tool()
def tool_assess_risk(
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
) -> str:
    """
    Calculate HEART score and assign triage level.
    """
    logger.info(f"[TOOL 2] assess_risk called")
    logger.info(f"[TOOL 2] age={age} gender={gender}")
    logger.info(f"[TOOL 2] bp={bp} hr={hr} o2={o2}")
    start = time.time()

    try:
        result = assess_risk(
            age=age,
            gender=gender,
            history=history,
            ecg=ecg,
            risk_factors=risk_factors,
            troponin=troponin,
            bp=bp,
            hr=hr,
            o2=o2,
            rr=rr,
            symptom_diagnoses=symptom_diagnoses
        )
        duration = round(time.time() - start, 2)
        logger.info(f"[TOOL 2] completed in {duration}s ✅")
        return result["result"]

    except Exception as e:
        logger.error(f"[TOOL 2] FAILED: {str(e)}")
        return f"Tool 2 error: {str(e)}"

@mcp.tool()
def tool_check_drug_interactions(
    current_medications: str,
    allergies: str,
    diagnosis: str,
    age: int,
    gender: str,
    history: str
) -> str:
    """
    Check medications for dangerous interactions
    and contraindications.
    """
    logger.info(f"[TOOL 3] check_drug_interactions called")
    logger.info(f"[TOOL 3] medications={current_medications}")
    logger.info(f"[TOOL 3] allergies={allergies}")
    start = time.time()

    try:
        result = check_drug_interactions(
            current_medications=current_medications,
            allergies=allergies,
            diagnosis=diagnosis,
            age=age,
            gender=gender,
            history=history
        )
        duration = round(time.time() - start, 2)
        logger.info(f"[TOOL 3] completed in {duration}s ✅")
        return result["result"]

    except Exception as e:
        logger.error(f"[TOOL 3] FAILED: {str(e)}")
        return f"Tool 3 error: {str(e)}"

@mcp.tool()
def tool_match_protocol(
    diagnosis: str,
    risk_level: str,
    triage: str,
    age: int,
    gender: str,
    history: str,
    vitals: str,
    drug_alerts: str
) -> str:
    """
    Match diagnosis to clinical protocol and
    recommend labs, imaging, and actions.
    """
    logger.info(f"[TOOL 4] match_protocol called")
    logger.info(f"[TOOL 4] diagnosis={diagnosis}")
    logger.info(f"[TOOL 4] risk_level={risk_level}")
    start = time.time()

    try:
        result = match_protocol(
            diagnosis=diagnosis,
            risk_level=risk_level,
            triage=triage,
            age=age,
            gender=gender,
            history=history,
            vitals=vitals,
            drug_alerts=drug_alerts
        )
        duration = round(time.time() - start, 2)
        logger.info(f"[TOOL 4] completed in {duration}s ✅")
        return result["result"]

    except Exception as e:
        logger.error(f"[TOOL 4] FAILED: {str(e)}")
        return f"Tool 4 error: {str(e)}"

@mcp.tool()
def tool_compile_report(
    patient_code: str,
    doctor_code: str,
    symptom_analysis: str,
    risk_assessment: str,
    drug_interactions: str,
    protocol_match: str
) -> str:
    """
    Compile all agent outputs into final
    structured clinical report.
    """
    logger.info(f"[TOOL 5] compile_report called")
    logger.info(f"[TOOL 5] patient={patient_code} doctor={doctor_code}")
    start = time.time()

    try:
        result = compile_report(
            patient_code=patient_code,
            doctor_code=doctor_code,
            symptom_analysis=symptom_analysis,
            risk_assessment=risk_assessment,
            drug_interactions=drug_interactions,
            protocol_match=protocol_match
        )
        duration = round(time.time() - start, 2)
        logger.info(f"[TOOL 5] completed in {duration}s ✅")
        return result["result"]

    except Exception as e:
        logger.error(f"[TOOL 5] FAILED: {str(e)}")
        return f"Tool 5 error: {str(e)}"

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("CliniqReason MCP Server starting...")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("Tools registered:")
    logger.info("  [OK] Tool 1 - Symptom Analyzer")
    logger.info("  [OK] Tool 2 - Risk Assessor")
    logger.info("  [OK] Tool 3 - Drug Checker")
    logger.info("  [OK] Tool 4 - Protocol Matcher")
    logger.info("  [OK] Tool 5 - Report Compiler")
    logger.info("=" * 50)
    mcp.run()