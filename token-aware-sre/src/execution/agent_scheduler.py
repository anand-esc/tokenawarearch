import logging
from langchain_core.prompts import ChatPromptTemplate
from .model_factory import ModelFactory

class AgentScheduler:
    """
    The Multi-Agent Core. Assigns a Persona based on incident context and invokes the model.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.factory = ModelFactory()

    def schedule_and_execute(self, compressed_payload: str, routing_decision: dict) -> str:
        """
        Spins up the right persona and model, and returns the raw proposed fix.
        """
        model_target = routing_decision.get("model_target", "LOCAL_SLM")
        
        # Instantiate the correct model via the factory
        model = self.factory.get_model(model_target)

        # Dynamic Persona Assignment
        if "database" in compressed_payload.lower() or "sql" in compressed_payload.lower():
            persona = "Database Administrator (DBA)"
            focus = "fixing database connections, slow queries, and data integrity."
        elif "network" in compressed_payload.lower() or "timeout" in compressed_payload.lower() or "503" in compressed_payload.lower():
            persona = "Network Reliability Engineer"
            focus = "resolving network partitions, timeouts, and connectivity issues."
        else:
            persona = "Site Reliability Engineer (SRE)"
            focus = "diagnosing system crashes, pod failures, and generalized infrastructure issues."

        self.logger.info(f"Assigned Persona: {persona} (Target: {model_target})")

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are an expert {persona}. Your focus is {focus}. "
                       "You will receive a highly compressed incident payload. "
                       "Diagnose the issue and provide a concrete bash command to remediate it. "
                       "Do not use markdown blocks, just return the raw command to fix it. "
                       "If you cannot fix it, output 'MANUAL_INTERVENTION_REQUIRED'."),
            ("user", "Incident Payload:\n\n{payload}")
        ])

        chain = prompt | model

        try:
            self.logger.info("Executing model inference...")
            response = chain.invoke({"payload": compressed_payload})
            return response.content
        except Exception as e:
            self.logger.error(f"Model execution failed: {e}")
            return "ERROR: Failed to generate fix."

if __name__ == "__main__":
    pass
