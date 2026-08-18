import json
import logging

class LogRewriter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def rewrite(self, raw_input: str) -> str:
        """
        Takes raw string input (could be JSON or raw text) and normalizes it.
        """
        try:
            data = json.loads(raw_input)
            # Fast-path check: Is it a Datadog alert?
            if self._is_datadog_alert(data):
                return self._parse_datadog(data)
            
            # Fallback for Generic JSON
            return self._parse_generic_json(data)
            
        except json.JSONDecodeError:
            # Fallback for raw text (e.g. trailing Kubernetes pod logs)
            return self._parse_raw_text(raw_input)

    def _is_datadog_alert(self, data: dict) -> bool:
        """Heuristics to detect Datadog webhooks."""
        return 'alert_id' in data or 'event_title' in data or 'event_type' in data

    def _parse_datadog(self, data: dict) -> str:
        """Strict parser for Datadog JSON schema."""
        title = data.get('event_title', 'Unknown Datadog Event')
        status = data.get('alert_transition', 'UNKNOWN_STATUS')
        body = data.get('body', '')
        link = data.get('link', '')
        tags = data.get('tags', '')
        
        normalized = f"DATADOG ALERT: [{status}] {title}\n"
        normalized += f"Tags: {tags}\n"
        normalized += f"Link: {link}\n"
        normalized += f"Details: {body}\n"
        return normalized

    def _parse_generic_json(self, data: dict) -> str:
        """Flattens any unknown JSON into readable text."""
        normalized = "GENERIC JSON ALERT:\n"
        # In the future, we can add logic to strip massive arrays or base64 blobs here
        for k, v in data.items():
            normalized += f"{k}: {v}\n"
        return normalized

    def _parse_raw_text(self, text: str) -> str:
        """Minimal processing for raw text strings."""
        normalized = "RAW LOG TEXT:\n"
        normalized += text.strip()
        return normalized

if __name__ == "__main__":
    # Quick manual test
    rewriter = LogRewriter()
    sample_dd = '{"alert_id": "123", "event_title": "High CPU", "body": "CPU > 90%", "alert_transition": "Triggered"}'
    print(rewriter.rewrite(sample_dd))
