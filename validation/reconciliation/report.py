"""Human-readable break summary."""


def format_summary(summary: dict, pay_period: str) -> str:
    total = sum(summary.values())
    lines = [f"Reconciliation report — pay period {pay_period}",
             f"  total records compared : {total}"]
    for bt in ("matched", "value_mismatch", "missing_left", "missing_right"):
        lines.append(f"  {bt:<15}: {summary.get(bt, 0)}")
    breaks = total - summary.get("matched", 0)
    lines.append(f"  -> {breaks} break(s) detected")
    return "\n".join(lines)