import re
from topaz_agent_kit.utils.logger import Logger
from fastmcp import FastMCP
import pandas as pd

# Example: Load CSV of policies for demonstration
df_policies = pd.read_csv("insurance_plans.csv")  # columns: policy_number, coverage_limit, deductible, plan_type

class InsuranceMCPTools:
    def __init__(self, **kwargs):
        self._logger = Logger("MCP.Insurance")

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(name="insurance_policy_lookup")
        def policy_lookup(policy_number: str) -> dict:
            """Retrieve policy coverage details. [roles: assessor]"""
            self._logger.input("policy_lookup INPUT: policy_number={}", policy_number)
            plan = df_policies[df_policies["policy_number"] == policy_number]
            if plan.empty:
                return {"error": f"No policy found for {policy_number}"}
            result = plan.iloc[0].to_dict()
            self._logger.output("policy_lookup OUTPUT: {}", result)
            return result

        @mcp.tool(name="insurance_actuarial_calculator")
        def actuarial_calculator(claim_type: str, incident_details: dict) -> dict:
            """Compute payout range based on claim type and incident severity. [roles: assessor]"""
            self._logger.input("actuarial_calculator INPUT: claim_type={}", claim_type)
            base = 1000.0 if claim_type.lower() == "auto" else 2000.0
            multiplier = 1.0
            if "total loss" in incident_details.get("description", "").lower():
                multiplier = 1.5
            result = {"min": base, "max": base * multiplier}
            self._logger.output("actuarial_calculator OUTPUT: {}", result)
            return result

        @mcp.tool(name="insurance_severity_classifier")
        def severity_classifier(description: str) -> str:
            """Classify severity: Low, Medium, High. [roles: assessor]"""
            self._logger.input("severity_classifier INPUT: description_len={}", len(description or ""))
            text = description.lower()
            if "total loss" in text:
                result = "High" 
                self._logger.output("severity_classifier OUTPUT: {}", result)
                return result
            if "collision" in text:
                result = "Medium"
                self._logger.output("severity_classifier OUTPUT: {}", result)
                return result
            result = "Low"
            self._logger.output("severity_classifier OUTPUT: {}", result)
            return result

        @mcp.tool(name="insurance_fraud_scoring")
        def fraud_scoring(policy_number: str, claim_details: dict) -> float:
            """Return a fraud risk score (0.0-1.0). [roles: fraud]"""
            self._logger.input("fraud_scoring INPUT: policy_number={}", policy_number)
            # Example: high claim amounts -> higher score
            amount = claim_details.get("amount_requested", 0)
            result = min(1.0, amount / 10000)
            self._logger.output("fraud_scoring OUTPUT: {}", result)
            return result

        @mcp.tool(name="insurance_duplicate_claim_checker")
        def duplicate_claim_checker(policy_number: str, incident_date: str) -> bool:
            """Check for duplicate claims. [roles: fraud]"""
            self._logger.input("duplicate_claim_checker INPUT: policy_number={}, incident_date={}", policy_number, incident_date)
            # Example: check CSV for duplicate policy/date
            duplicates = df_policies[(df_policies["policy_number"] == policy_number) &
                                     (df_policies["incident_date"] == incident_date)]
            result = len(duplicates) > 1
            self._logger.output("duplicate_claim_checker OUTPUT: {}", result)
            return result

        @mcp.tool(name="insurance_anomaly_detector")
        def anomaly_detector(claim_json: dict) -> list:
            """Detect anomalies in claims. [roles: fraud]"""
            self._logger.input("anomaly_detector INPUT: keys={}", list(claim_json.keys()))
            anomalies = []
            if claim_json.get("amount_requested", 0) > 10000:
                anomalies.append("Unusually high claim amount")
            if "collision" not in claim_json.get("description", "").lower():
                anomalies.append("Description does not match claim type")
            self._logger.output("anomaly_detector OUTPUT: {}", anomalies)
            return anomalies
