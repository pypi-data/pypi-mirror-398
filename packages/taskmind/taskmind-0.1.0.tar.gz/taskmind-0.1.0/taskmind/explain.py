class Explanation:
    """
    Collects step-by-step evaluation details and produces
    human-readable explanations.
    """

    def __init__(self):
        self.steps = []

    def add_step(self, rule_name, result, priority, message=None):
        self.steps.append({
            "rule": rule_name,
            "result": result,
            "priority": priority,
            "message": message
        })

    def summary(self):
        return self.steps

    def to_text(self):
        """
        Convert explanation steps to human-readable sentences.
        """
        lines = []

        for step in self.steps:
            rule = step["rule"]
            result = step["result"]
            priority = step["priority"]
            message = step["message"]

            if result:
                if message:
                    lines.append(
                        f"Rule '{rule}' matched: {message} (priority {priority})."
                    )
                else:
                    lines.append(
                        f"Rule '{rule}' matched (priority {priority})."
                    )
            else:
                lines.append(
                    f"Rule '{rule}' did not match."
                )

        return lines
