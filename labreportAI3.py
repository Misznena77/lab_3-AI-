import json
import operator
import streamlit as st

# Safe operator mappings for dynamic rule evaluation
OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    ">": operator.gt,
    "<": operator.lt,
    "!=": operator.ne,
}


def evaluate_rule_condition(fact_val, op_str, threshold):
  """Evaluates a single condition clause against an applicant's attribute."""
  if op_str in OPERATORS:
    return OPERATORS[op_str](fact_val, threshold)
  return False


def evaluate_scholarship(applicant_facts, rules_list):
  """Evaluates applicant facts against rules sorted by priority (highest priority first)."""
  # Sort rules by priority descending
  sorted_rules = sorted(
      rules_list, key=lambda x: x.get("priority", 0), reverse=True
  )

  for rule in sorted_rules:
    conditions = rule.get("conditions", [])
    all_conditions_satisfied = True

    for field, op_str, threshold in conditions:
      val = applicant_facts.get(field)
      if val is None or not evaluate_rule_condition(val, op_str, threshold):
        all_conditions_satisfied = False
        break

    if all_conditions_satisfied:
      return rule["action"], rule["name"], sorted_rules

  # Fallback response if no explicit rules match
  return (
      {
          "decision": "PENDING_REVIEW",
          "reason": (
              "Does not trigger automated decision rules; pending committee"
              " review."
          ),
      },
      "Default Fallback",
      sorted_rules,
  )


# --- Page Configuration ---
st.set_page_config(
    page_title="Scholarship Advisory Rule Engine", page_icon="🎓", layout="wide"
)

st.title("🎓 University Scholarship Advisory Decision Support Tool")
st.markdown(
    "A transparent, rule-based expert system assisting university academic and"
    " financial aid committees."
)

# --- Sidebar: JSON Rule Configuration ---
st.sidebar.header("⚙️ Rule Engine Configuration")
st.sidebar.markdown(
    "Modify or add custom rules in JSON format below. Priority determines"
    " evaluation order."
)

default_json = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0],
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": (
                "Excellent academic & co-curricular performance, with"
                " acceptable need"
            ),
        },
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1],
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": (
                "Good academic & involvement record with moderate need"
            ),
        },
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [["cgpa", ">=", 2.5], ["family_income", "<=", 4000]],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score",
        },
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [["cgpa", "<", 2.5]],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement",
        },
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [["disciplinary_actions", ">=", 2]],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records",
        },
    },
]

raw_json_input = st.sidebar.text_area(
    "Rule Definition Editor (JSON)",
    value=json.dumps(default_json, indent=4),
    height=450,
)

try:
  active_rules = json.loads(raw_json_input)
except json.JSONDecodeError as err:
  st.sidebar.error(f"❌ Invalid JSON Syntax: {err}")
  active_rules = default_json

# --- Main Layout: Applicant Profile Input Form ---
st.subheader("📝 Applicant Details")

col1, col2 = st.columns(2)

with col1:
  cgpa = st.number_input(
      "Cumulative GPA (CGPA)",
      min_value=0.0,
      max_value=4.0,
      value=3.75,
      step=0.01,
  )
  family_income = st.number_input(
      "Monthly Family Income (MYR)",
      min_value=0.0,
      value=5000.0,
      step=100.0,
  )
  co_curricular_score = st.slider(
      "Co-curricular Involvement Score (0–100)",
      min_value=0,
      max_value=100,
      value=85,
  )

with col2:
  community_service_hours = st.number_input(
      "Community Service Hours", min_value=0, value=25, step=1
  )
  current_semester = st.number_input(
      "Current Semester of Study", min_value=1, max_value=8, value=3, step=1
  )
  disciplinary_actions = st.number_input(
      "Number of Disciplinary Actions", min_value=0, value=0, step=1
  )

# Assemble facts dictionary matching rule schema key names
applicant_facts = {
    "cgpa": cgpa,
    "family_income": family_income,
    "co_curricular_score": co_curricular_score,
    "community_service_hours": community_service_hours,
    "current_semester": current_semester,
    "disciplinary_actions": disciplinary_actions,
}

st.markdown("---")

if st.button("Evaluate Application", type="primary", use_container_width=True):
  action, matched_rule_name, sorted_rules = evaluate_scholarship(
      applicant_facts, active_rules
  )

  decision = action.get("decision", "N/A")
  reason = action.get("reason", "N/A")

  st.subheader("📋 Evaluation Verdict")

  # Color coding output banners based on decisions
  if decision == "AWARD_FULL":
    st.success(f"### Result: {decision}")
  elif decision == "AWARD_PARTIAL":
    st.info(f"### Result: {decision}")
  elif decision == "REVIEW":
    st.warning(f"### Result: {decision}")
  else:
    st.error(f"### Result: {decision}")

  st.write(f"**Triggered Rule:** `{matched_rule_name}`")
  st.write(f"**Justification:** {reason}")

  # Audit trail for transparency
  with st.expander("🔍 Rule Execution Audit Trail"):
    st.markdown(
        "Rules evaluated sequentially by priority rank (highest priority first):"
    )
    for rule in sorted_rules:
      is_trigger = rule["name"] == matched_rule_name
      status = "🟢 MATCHED & FIRED" if is_trigger else "⚪ PASSED OVER"
      st.markdown(
          f"- **{rule['name']}** (Priority: {rule.get('priority', 0)}) —"
          f" {status}"
      )