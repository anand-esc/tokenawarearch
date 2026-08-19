import json
import logging

class LogRewriter:
    """Normalizes various incident log formats into a standardized text representation.
    
    This class handles raw strings, generic JSON, and specific vendor schemas 
    (e.g., Datadog) to ensure downstream components receive structured text.
    
    Attributes:
        logger (logging.Logger): Logger for the rewriter.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def rewrite(self, raw_input: str) -> str:
        """Takes raw string input and normalizes it based on its format.

        Args:
            raw_input (str): The raw incident payload (JSON string or raw text).

        Returns:
            str: The normalized, flattened text representation.
        """
        if not raw_input:
            return ""
            
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
        except Exception as e:
            self.logger.error(f"Unexpected error in rewrite: {e}")
            return self._parse_raw_text(raw_input)

    def _is_datadog_alert(self, data: dict) -> bool:
        """Determines if the JSON payload matches the Datadog webhook schema.

        Args:
            data (dict): The parsed JSON dictionary.

        Returns:
            bool: True if it appears to be a Datadog alert, False otherwise.
        """
        return 'alert_id' in data or 'event_title' in data or 'event_type' in data

    def _parse_datadog(self, data: dict) -> str:
        """Parses a Datadog webhook payload into a readable summary string.

        Args:
            data (dict): The Datadog JSON dictionary.

        Returns:
            str: A formatted string containing the critical Datadog fields.
        """
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
        """Flattens a generic JSON dictionary into a readable key-value string.

        Args:
            data (dict): The generic JSON dictionary.

        Returns:
            str: A flattened text representation of the JSON data.
        """
        normalized = "GENERIC JSON ALERT:\n"
        # In the future, we can add logic to strip massive arrays or base64 blobs here
        try:
            for k, v in data.items():
                normalized += f"{k}: {v}\n"
        except Exception:
            normalized += str(data)
        return normalized

    def _parse_raw_text(self, text: str) -> str:
        """Returns the raw text with a standardized prefix.

        Args:
            text (str): The raw text string.

        Returns:
            str: The stripped raw text with a prefix.
        """
        normalized = "RAW LOG TEXT:\n"
        normalized += text.strip()
        return normalized

if __name__ == "__main__":
    # Quick manual test
    rewriter = LogRewriter()
    sample_dd = '{"alert_id": "123", "event_title": "High CPU", "body": "CPU > 90%", "alert_transition": "Triggered"}'
    print(rewriter.rewrite(sample_dd))
