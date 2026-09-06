import logging
from langchain_core.prompts import ChatPromptTemplate
from .model_factory import ModelFactory

class AgentScheduler:
    """The Multi-Agent Core for Phase 3.
    
    Dynamically assigns a troubleshooting Persona (e.g., DBA, Network Engineer) 
    based on the incident context and orchestrates the inference chain to 
    generate remediation bash commands.

    Attributes:
        logger (logging.Logger): Logger for the scheduler.
        factory (ModelFactory): The factory used to instantiate the LLM/SLM.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.factory = ModelFactory()

    def schedule_and_execute(self, compressed_payload: str, routing_decision: dict, runtime_config: dict = None) -> str:
        """Assigns a persona and invokes the language model to generate a fix.

        Args:
            compressed_payload (str): The optimized incident text from Phase 1.
            routing_decision (dict): The dictionary from Phase 2 containing the model target.
            runtime_config (dict): Dynamic settings like API keys and endpoints.

        Returns:
            str: The raw bash command/script proposed by the model.
        """
        if not compressed_payload:
            return "ERROR: Empty payload received."

        try:
            model_target = routing_decision.get("model_target", "LOCAL_SLM")
            model = self.factory.get_model(model_target, runtime_config=runtime_config)

            # Dynamic Persona Assignment
            payload_lower = compressed_payload.lower()
            if "database" in payload_lower or "sql" in payload_lower:
                persona = "Database Administrator (DBA)"
                focus = "fixing database connections, slow queries, and data integrity."
            elif "network" in payload_lower or "timeout" in payload_lower or "503" in payload_lower:
                persona = "Network Reliability Engineer"
                focus = "resolving network partitions, timeouts, and connectivity issues."
            elif any(k in payload_lower for k in ["python", "def ", "function", "syntax", "code", "script", "program", "class "]):
                persona = "Senior Software & Python Engineer"
                focus = "debugging application code, correcting function calls and syntax, and providing working code solutions."
            else:
                persona = "Site Reliability Engineer (SRE)"
                focus = "diagnosing system crashes, pod failures, and generalized infrastructure issues."

            self.logger.info(f"Assigned Persona: {persona} (Target: {model_target})")

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are an expert {persona}. Your focus is {focus}. "
                           "You will receive an incident log, technical task, or code payload. "
                           "Diagnose the root cause and provide the concrete, working remediation, corrected code, or actionable solution. "
                           "If it is an infrastructure issue, provide the bash remediation commands. "
                           "If it is a programming/code issue, provide the explanation and corrected code. "
                           "Only output 'MANUAL_INTERVENTION_REQUIRED' if physical human intervention (like replacing hardware) is necessary."),
                ("user", "Incident / Task Payload:\n\n{payload}")
            ])

            chain = prompt | model

            self.logger.info("Executing model inference...")
            response = chain.invoke({"payload": compressed_payload})
            
            result = response.content.strip()

            # If model truly requested manual intervention, don't wrap in bash
            if "MANUAL_INTERVENTION_REQUIRED" in result:
                return "MANUAL_INTERVENTION_REQUIRED"

            # Strip markdown code fences if wrapped around the entire response
            if result.startswith("```"):
                lines = result.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                result = "\n".join(lines).strip()

            # Only add shebang for pure bash commands
            if any(result.startswith(cmd) for cmd in ["systemctl", "kubectl", "docker", "apt", "dnf", "yum", "curl", "kill", "psql", "certbot", "nginx", "redis-cli"]):
                result = "#!/bin/bash\n" + result

            return result
            
        except Exception as e:
            self.logger.error(f"Model execution failed in scheduler: {e}")
            return "ERROR: Failed to generate fix."

if __name__ == "__main__":
    pass
