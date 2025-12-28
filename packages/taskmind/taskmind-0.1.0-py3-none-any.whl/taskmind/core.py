from taskmind.explain import Explanation


class Rule:
    """
    Represents a single business rule.
    """

    def __init__(self, condition, action, name=None, priority=0, message=None):
        self.condition = condition
        self.action = action
        self.name = name or action.__name__
        self.priority = priority
        self.message = message  # human-readable message

    def evaluate(self, context):
        return self.condition(context)


class RuleEngine:
    """
    Executes rules with priority, conflict detection, and explainability.
    """

    def __init__(self):
        self.rules = []

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def run(self, context, explain=False, stop_on_first=False):
        explanation = Explanation() if explain else None
        matched_rules = []
        actions = []

        # Sort rules by priority (high → low)
        sorted_rules = sorted(
            self.rules,
            key=lambda r: r.priority,
            reverse=True
        )

        for rule in sorted_rules:
            result = rule.evaluate(context)

            if explain:
                explanation.add_step(
                rule_name=rule.name,
                result=result,
                priority=rule.priority,
                message=rule.message
    )


            if result:
                matched_rules.append(rule.name)
                action_result = rule.action(context)
                actions.append(action_result)

                if stop_on_first:
                    break

        # Conflict detection
        conflict = len(set(actions)) > 1

        return {
            "matched_rules": matched_rules,
            "actions": actions,
            "conflict": conflict,
            "explanation": explanation.summary() if explain else None
        }
