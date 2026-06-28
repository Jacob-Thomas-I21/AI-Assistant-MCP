"""
agents/data_agent.py — Structured data Q&A via LLM-generated pandas code.
"""
import io
import traceback
from typing import Dict, Any

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import get_llm
from config import CSV_PATH

CODE_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a data analyst assistant. Generate Python pandas code to answer the user's question about a DataFrame called `df`.

DataFrame schema:
{schema}

Sample rows (first 3):
{sample}

Rules:
1. Write ONLY the pandas code — no explanation, no markdown, no ```python blocks.
2. Store the final result in a variable called `result`.
3. `result` should be a scalar, list, or small DataFrame — something that can be printed.
4. Use only pandas operations on `df`. Do not import anything, do not access the filesystem or
   network, and do not use dunder attributes (e.g. `__class__`, `__import__`). pandas is already
   imported as `pd`.
5. Only reference columns that appear in the schema above. If the question refers to a column
   that doesn't exist, set `result = "Column not found: <best guess>"` instead of guessing.
6. If no rows match the question's criteria, set `result` to a clear string such as
   "No matching rows found." rather than letting an exception occur.
7. Keep the code simple, correct, and a single short script (no function definitions needed).

Example:
User: Which branch has highest revenue?
Code: result = df.loc[df['Revenue'].idxmax(), 'Branch']
"""),
    ("human", "{query}")
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful data analyst. Given a user question and a computed data result, write a clear, concise natural language answer.

Rules:
1. Use ONLY the numbers and values present in the computed result — never add, infer, or round
   numbers that aren't there.
2. If the result indicates no matching rows or a missing column, say so plainly and suggest the
   user rephrase or check the field name.
3. State the answer directly first, then add at most one sentence of context if helpful."""),
    ("human", "Question: {query}\n\nComputed result:\n{result}\n\nPandas code used:\n{code}")
])




def _get_schema_and_sample(df: pd.DataFrame) -> tuple:
    schema_buf = io.StringIO()
    df.info(buf=schema_buf)
    schema = schema_buf.getvalue()
    sample = df.head(3).to_string(index=False)
    return schema, sample


def run_data_agent(query: str) -> Dict[str, Any]:
    """
    Generate and execute pandas code to answer a structured data question.

    Returns dict with: response, code, result_value, error
    """
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        return {
            "response": f"Could not load the data file: {e}",
            "code": "",
            "result_value": None,
            "error": str(e),
        }

    schema, sample = _get_schema_and_sample(df)

    llm = get_llm(temperature=0.0)
    code_chain = CODE_GEN_PROMPT | llm | StrOutputParser()
    code = code_chain.invoke({
        "schema": schema,
        "sample": sample,
        "query": query,
    }).strip()

    # execute in a restricted scope — only pandas and the dataframe
    local_scope = {"pd": pd, "df": df.copy()}
    try:
        exec(code, {"__builtins__": {}}, local_scope)  # no builtins for safety
        result_value = local_scope.get("result", "No result variable found.")
    except Exception:
        err = traceback.format_exc(limit=3)
        return {
            "response": f"I generated code to answer your question but it encountered an error. This can happen with complex queries. Please try rephrasing.\n\nError: {err}",
            "code": code,
            "result_value": None,
            "error": err,
        }

    if isinstance(result_value, pd.DataFrame):
        result_str = result_value.to_string(index=False)
    else:
        result_str = str(result_value)

    answer_chain = ANSWER_PROMPT | llm | StrOutputParser()
    response = answer_chain.invoke({
        "query": query,
        "result": result_str,
        "code": code,
    })

    return {
        "response": response,
        "code": code,
        "result_value": result_str,
        "error": None,
    }
