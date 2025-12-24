from typing import List, Dict, Set
from openaudit.ai.models import PromptContext, AIResult
from openaudit.ai.protocol import AgentProtocol
from openaudit.core.domain import Severity, Confidence
from openaudit.features.architecture.models import ProjectStructure, ModuleNode

class ThreatModelingAgent(AgentProtocol):
    """
    AI Agent that generates a high-level threat model based on project structure.
    """
    name = "threat-modeling-agent"
    description = "Generates a STRIDE-based threat model for key components."

    def run(self, context: PromptContext) -> AIResult:
        # Not used directly, as this agent needs structure. 
        # We will add a custom run_on_structure method.
        return AIResult(
            analysis="Use run_on_structure instead.",
            risk_score=0.0,
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            is_advisory=True
        )

    def run_on_structure(self, structure: ProjectStructure) -> List[AIResult]:
        from openaudit.ai.engine import AIEngine
        import json
        engine = AIEngine()
        
        if not engine.is_available():
             return []

        # Simplify structure for prompt
        modules_summary = [f"{m.path} (imports: {m.imports})" for m in structure.modules]
        
        system_prompt = "You are a security architect. specific STRIDE threat model based on project structure. Identify key components (Auth, DB, API, etc.) and list specific threats. Return a JSON object with a key 'threats' containing a list of objects with 'component', 'threat', 'risk_score' (0-1), and 'mitigation'."
        user_prompt = f"Project Structure:\n{json.dumps(modules_summary, indent=2)}\n\nGenerate STRIDE threat model."

        results = []
        try:
            response = engine.chat_completion(system_prompt, user_prompt)
            # Naive parse
            if "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                data = json.loads(json_str)
                
                for item in data.get("threats", []):
                    results.append(AIResult(
                        analysis=f"Threat ({item.get('component', 'General')}): {item.get('threat')}",
                        risk_score=item.get("risk_score", 0.7),
                        severity=Severity.HIGH,
                        confidence=Confidence.MEDIUM,
                        suggestion=f"Mitigation: {item.get('mitigation')}",
                        is_advisory=True
                    ))
            else:
                results.append(AIResult(
                    analysis=response[:200] + "...",
                    risk_score=0.5,
                    severity=Severity.MEDIUM,
                    confidence=Confidence.LOW,
                    suggestion="Review full AI analysis.",
                    is_advisory=True
                ))
        except Exception:
            pass
        
        return results

    def _identify_components(self, structure: ProjectStructure) -> Dict[str, str]:
        """
        Heuristic to identify key components from module paths.
        Returns: {component_name: component_type}
        """
        components = {}
        for module in structure.modules:
            path_lower = module.path.lower()
            if "auth" in path_lower or "login" in path_lower or "user" in path_lower:
                components[module.name] = "Authentication"
            elif "db" in path_lower or "database" in path_lower or "sql" in path_lower or "model" in path_lower:
                components[module.name] = "Database"
            elif "api" in path_lower or "route" in path_lower or "controller" in path_lower:
                components[module.name] = "API Gateway"
            elif "payment" in path_lower or "billing" in path_lower:
                 components[module.name] = "Payments"
        
        # Deduplication/Grouping logic could go here (e.g. grouping all auth.* modules)
        # For now, just taking unique identified modules 
        return components

    def _generate_stride_threats(self, component_name: str, component_type: str) -> List[Dict[str, str]]:
        """
        Generates standard STRIDE threats based on component type.
        """
        threats = []
        
        if component_type == "Authentication":
            threats.append({
                "threat": "Spoofing Identity: Attackers may attempt to impersonate users.",
                "mitigation": "Enforce strong MFA and robust session management."
            })
            threats.append({
                "threat": "Information Disclosure: Leakage of user credentials.",
                "mitigation": "Ensure proper hashing (Argon2/bcrypt) and secure logs."
            })
            
        elif component_type == "Database":
             threats.append({
                "threat": "Tampering with Data: SQL Injection or unauthorized modification.",
                "mitigation": "Use parameterized queries/ORM and strict input validation."
            })
             threats.append({
                "threat": "Information Disclosure: Exposure of sensitive records.",
                "mitigation": "Encrypt data at rest and implement strict RBAC."
            })

        elif component_type == "API Gateway":
             threats.append({
                "threat": "Denial of Service: Flooding API resources.",
                "mitigation": "Implement rate limiting and request throttling."
            })
             threats.append({
                "threat": "Tampering: Parameter pollution or replay attacks.",
                "mitigation": "Validate all inputs and use TLS."
            })
             
        elif component_type == "Payments":
             threats.append({
                "threat": "Tampering: Manipulation of transaction amounts.",
                "mitigation": "Validate transaction integrity on server-side and use signing."
            })
        
        return threats
