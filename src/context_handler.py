from typing import Any, Dict, List


class ContextHandler:
    def __init__(self) -> None:
        self.original_task: str = ""
        self.history: List[Dict[str, Any]] = []

    def start_new_task(self, original_task: str) -> None:
        """Resets the context for a new task."""
        self.original_task = original_task
        self.history = []

    def add_assistant_action(self, action: Dict[str, Any]) -> None:
        """Adds a successful AI action to the history."""
        self.history.append({"role": "assistant", "action": action})

    def add_system_feedback(self, feedback: str) -> None:
        """Adds system feedback (e.g., an error message) to the history."""
        self.history.append({"role": "system", "feedback": feedback})

    def get_formatted_history(self) -> str:
        """Creates a concise string summary of the task history for the AI."""
        if not self.history:
            return "Ez az első lépés."

        summary = ["Előzmények:"]
        for item in self.history:
            if item["role"] == "assistant":
                action = item["action"]
                summary.append(
                    f"- Asszisztens Lépés: {action.get('command')} "
                    f"{action.get('arguments', '')}"
                )
            elif item["role"] == "system":
                summary.append(f"- Rendszer Visszajelzés: {item['feedback']}")

        return "\n".join(summary)
