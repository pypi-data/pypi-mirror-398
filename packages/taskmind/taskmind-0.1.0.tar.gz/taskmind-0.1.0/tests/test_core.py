from taskmind.core import Rule, RuleEngine


def test_rule_priority_and_explainability():
    engine = RuleEngine()

    engine.add_rule(Rule(
        condition=lambda ctx: ctx["age"] < 18,
        action=lambda ctx: "DENY",
        name="minor_block",
        priority=100
    ))

    engine.add_rule(Rule(
        condition=lambda ctx: ctx["age"] >= 18,
        action=lambda ctx: "ALLOW",
        name="adult_allow",
        priority=10
    ))

    result = engine.run({"age": 16}, explain=True)

    assert result["matched_rules"] == ["minor_block"]
    assert result["actions"] == ["DENY"]
    assert result["conflict"] is False
    assert result["explanation"][0]["rule"] == "minor_block"
