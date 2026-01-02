"""
VVUQ Client SDK

A thin wrapper for the VVUQ Verification API.
This client allows interaction with the VVUQ service without hosting the full verification node.
"""

import os
import requests
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

DEFAULT_API_URL = "http://localhost:8081"  # Default to local, but users will override


class VVUQError(Exception):
    """Base exception for VVUQ SDK errors"""
    pass


class AuthenticationError(VVUQError):
    """Raised when API key is missing or invalid"""
    pass


@dataclass
class ContractReceipt:
    contract_id: str
    success: bool
    message: str


@dataclass
class VerificationResult:
    verdict: str
    verification_time_ms: float
    contract_id: str
    prover_agent_id: str
    errors: List[str]
    compilation_output: Optional[str] = None


class VVUQClient:
    """
    Client for the VVUQ Verification API.
    
    Args:
        api_key (str): Your VVUQ API Key. Defaults to message via VVUQ_API_KEY env var.
        base_url (str): URL of the VVUQ API server. Defaults to localhost.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("VVUQ_API_URL", DEFAULT_API_URL)).rstrip("/")
        self.api_key = api_key or os.getenv("VVUQ_API_KEY")
        
        if not self.api_key:
            raise AuthenticationError(
                "API Key is required. Pass it to constructor or set VVUQ_API_KEY environment variable."
            )
            
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "vvuq-python-sdk/0.1.0"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Internal request helper with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            if e.response is not None:
                try:
                    detail = e.response.json().get("detail", "")
                    if detail:
                        error_msg = f"{e} - {detail}"
                except ValueError:
                    pass
            
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError(error_msg)
            raise VVUQError(error_msg)
        except requests.exceptions.RequestException as e:
            raise VVUQError(f"Connection error: {e}")

    def health(self) -> Dict[str, Any]:
        """Check if the API service is healthy"""
        # Health endpoint might not require auth, but our session sends it anyway
        return self._request("GET", "/health")

    def create_contract(
        self,
        title: str,
        description: str,
        claims: List[Dict[str, Any]],
        issuer_id: str
    ) -> ContractReceipt:
        """
        Create a new verification contract.
        
        Args:
            title: Contract title
            description: Contract description
            claims: List of claim dicts (theorem, allowed_imports, etc.)
            issuer_id: Your agent ID
            
        Returns:
            ContractReceipt object
        """
        payload = {
            "title": title,
            "description": description,
            "claims": claims,
            "issuer_agent_id": issuer_id
        }
        
        data = self._request("POST", "/contracts", json=payload)
        return ContractReceipt(
            contract_id=data["contract_id"],
            success=data["success"],
            message=data["message"]
        )

    def get_contract(self, contract_id: str) -> Dict[str, Any]:
        """Retrieve contract details"""
        return self._request("GET", f"/contracts/{contract_id}")

    def submit_proof(
        self,
        contract_id: str,
        proof_code: str,
        prover_id: str,
        claim_index: int = 0
    ) -> VerificationResult:
        """
        Submit a proof for verification.
        
        Args:
            contract_id: ID of the contract to fulfill
            proof_code: Lean4 source code of the proof
            prover_id: Your agent ID
            claim_index: Index of the claim (default 0)
            
        Returns:
            VerificationResult object
        """
        payload = {
            "contract_id": contract_id,
            "prover_agent_id": prover_id,
            "proof_code": proof_code,
            "proof_claim_index": claim_index
        }
        
        data = self._request("POST", "/proofs/submit", json=payload)
        return VerificationResult(
            verdict=data["verdict"],
            verification_time_ms=data["verification_time_ms"],
            contract_id=data["contract_id"],
            prover_agent_id=data["prover_agent_id"],
            errors=data.get("errors", []),
            compilation_output=data.get("compilation_output")
        )

    def get_history(self, contract_id: str) -> Dict[str, Any]:
        """Get verification history"""
        return self._request("GET", f"/contracts/{contract_id}/verification-history")

    def submit_feedback(
        self,
        title: str,
        description: str,
        feedback_type: str,
        severity: str,
        tool_name: Optional[str] = None,
        reproduction_steps: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        actual_behavior: Optional[str] = None,
        test_criteria: Optional[str] = None,
        submitter_type: str = "person",
        contact_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit feedback, bug reports, or feature requests.
        
        Args:
            title: Brief title
            description: Detailed description
            feedback_type: bug, feature_request, improvement, etc.
            severity: critical, high, medium, low
            tool_name: (Optional) Related tool/endpoint
            reproduction_steps: (Optional) How to reproduce
            expected_behavior: (Optional) What should happen
            actual_behavior: (Optional) What actually happened
            test_criteria: (Optional) How to verify fix
            submitter_type: person, agent, or automated_system
            contact_info: (Optional) Email or contact detail
            
        Returns:
            Dict containing success status and feedback_id
        """
        payload = {
            "title": title,
            "description": description,
            "feedback_type": feedback_type,
            "severity": severity,
            "tool_name": tool_name,
            "reproduction_steps": reproduction_steps,
            "expected_behavior": expected_behavior,
            "actual_behavior": actual_behavior,
            "test_criteria": test_criteria,
            "submitter_type": submitter_type,
            "contact_info": contact_info
        }
        # Filter None values (optional, but clean)
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return self._request("POST", "/feedback/submit", json=payload)
