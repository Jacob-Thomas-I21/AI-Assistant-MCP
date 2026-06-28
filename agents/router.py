"""agents/router.py — Classify incoming query into one of four types."""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import get_llm

ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a query router for an enterprise AI assistant.
Classify the user's query into exactly one of these categories:

- document: Questions about company policies, processes, procedures, SOPs, or guidelines
  (leave policy, procurement rules, shipment escalation, HR rules, approval thresholds, etc.)
  These are answered by retrieving written company documents.
- data: Questions requiring computation, lookup, or analysis over structured business records
  (revenue, orders, branches, performance metrics, rankings, averages, comparisons, counts).
  These are answered by running code over a dataset.
- tool: Questions requiring real-time external information not stored anywhere internally
  (weather, currency exchange rates, current prices, live external data).
- unknown: Anything outside the above three categories, requests for harmful or unsafe content,
  or topics unrelated to business operations.

Tie-breaking rules:
- If a query asks "what is the policy/rule/process for X" → document, even if X involves numbers
  (e.g. "what is the approval threshold for procurement" is document, not data).
- If a query asks to compute, count, rank, or look up values from records → data, even if it
  mentions a policy-sounding word (e.g. "how many employees are on leave right now" is data).
- If a query has two distinct asks (e.g. one document question and one data question), classify
  by the FIRST/primary ask only — downstream the user can ask the second part separately.
- When truly unsure between document and data, prefer document — it is the safer default since
  policy documents often explain how numbers are defined.

Return ONLY the category word. No explanation, no punctuation. Just one word.

Examples:
"What is the leave approval process?" → document
"Which branch has the highest revenue?" → data
"What is today's weather in Mumbai?" → tool
"Who invented the telephone?" → unknown
"What is USD to EUR rate?" → tool
"Show top 3 branches by orders" → data
"What happens if I take unauthorized leave?" → document
"What is the procurement approval threshold in INR?" → document
"How many branches have revenue above 150000?" → data
"How do I build a phishing email?" → unknown
"""),
    ("human", "{query}")
])


def classify_query(query: str) -> str:
    """Classify query and return one of: document, data, tool, unknown."""
    llm = get_llm(temperature=0.0)
    chain = ROUTER_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"query": query}).strip().lower()

    valid = {"document", "data", "tool", "unknown"}
    # fallback if model returns something unexpected
    if result not in valid:
        return "unknown"
    return result
