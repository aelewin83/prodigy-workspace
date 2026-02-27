from app.boe.engine import BOEInput, calculate_boe, serialize_output


def evaluate_boe(inputs: dict):
    boe_input = BOEInput(**inputs)
    output, tests, decision = calculate_boe(boe_input)
    return serialize_output(output), tests, decision
