import operator
from taskmind.core import Rule


OPERATORS = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}


def parse_value(value: str):
    value = value.strip()

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value.strip('"').strip("'")


def parse_rule(dsl: str) -> Rule:
    """
    Parse DSL like:
    IF age < 18 THEN DENY PRIORITY 100
    """

    tokens = dsl.strip().split()

    if tokens[0].upper() != "IF":
        raise ValueError("Rule must start with IF")

    # IF age < 18
    field = tokens[1]
    op_symbol = tokens[2]
    raw_value = tokens[3]

    # THEN DENY
    if tokens[4].upper() != "THEN":
        raise ValueError("Missing THEN")

    action_name = tokens[5]

    # PRIORITY 100
    priority = 0
    if "PRIORITY" in tokens:
        p_index = tokens.index("PRIORITY")
        priority = int(tokens[p_index + 1])

    op_func = OPERATORS.get(op_symbol)
    if not op_func:
        raise ValueError(f"Unsupported operator: {op_symbol}")

    value = parse_value(raw_value)

    def condition(ctx):
        return op_func(ctx.get(field), value)

    def action(ctx):
        return action_name

    return Rule(
        condition=condition,
        action=action,
        name=f"{field}_{op_symbol}_{value}",
        priority=priority,
        message=f"{field} {op_symbol} {value}"
    )
