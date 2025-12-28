from taskmind.dsl import parse_rule
from taskmind.core import RuleEngine


def test_dsl_rule():
    engine = RuleEngine()

    rule = parse_rule("IF age < 18 THEN DENY PRIORITY 100")
    engine.add_rule(rule)

    result = engine.run({"age": 16}, explain=True)

    assert result["actions"] == ["DENY"]
    assert result["conflict"] is False
