"""
agents/tool_agent.py — MCP tool calling agent.

Uses MCP in-memory transport: client and server run in the same process,
connected via memory streams. No subprocess is spawned, so this works
cross-platform without any platform-specific event loop configuration.

Architecture:
    run_tool_agent()
        → LLM selects tool + args
        → ThreadPoolExecutor (isolates from Streamlit's event loop)
            → anyio.run()
                → in-memory streams (client ↔ server, same process)
                    → MCP server handles tool call
                    → returns result
"""
import asyncio
import concurrent.futures
import json
import logging
import re
import traceback
from typing import Dict, Any

import anyio
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.llm import get_llm
from tools.mcp_server import app as mcp_app  # MCP server instance, imported directly

# Logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] tool_agent — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tool_agent")

# Prompts
TOOL_SELECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a tool selection assistant. Given the user's query and a list of available tools, decide which tool to call and with what arguments.

Available tools:
{tools_description}

Rules:
1. Only select a tool if the query clearly matches what that tool does.
2. Extract argument values directly from the user's query. Use standard formats: currency codes
   as 3-letter ISO codes (e.g. "USD", "EUR", "INR"), city names as given by the user.
3. If a tool matches the general intent but a REQUIRED argument is missing or ambiguous from the
   query (e.g. "convert currency" with no target currency given), return:
   {{"tool": null, "args": {{}}, "reason": "missing_argument"}}
4. If no tool is appropriate at all, return:
   {{"tool": null, "args": {{}}, "reason": "no_matching_tool"}}
5. If a tool and all required arguments are clear, return:
   {{"tool": "tool_name", "args": {{"arg1": "value1", "arg2": "value2"}}, "reason": "ok"}}

Return ONLY the JSON object. No explanation, no markdown.
"""),
    ("human", "{query}")
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant. Using the tool output below, answer the user's question naturally and clearly.

Rules:
1. If the tool output looks like an error message (mentions "error", "failed", "exception", or
   is empty/null), do not present it as a normal answer — instead tell the user the lookup failed
   and suggest they try again or rephrase.
2. Otherwise, answer directly using only the values present in the tool output — do not invent
   or round numbers that aren't there."""),
    ("human", "Question: {query}\n\nTool used: {tool_name}\nTool input: {tool_input}\nTool output:\n{tool_output}")
])


# MCP in-memory transport

async def _call_mcp_tool(tool_name: str, tool_args: dict) -> str:
    """
    Call an MCP tool using in-memory transport.

    Client and server communicate through anyio memory streams within the same
    process. No subprocess is spawned — works cross-platform without any
    event loop configuration.
    """
    async with create_client_server_memory_streams() as (client_streams, server_streams):
        client_read, client_write = client_streams
        server_read, server_write = server_streams

        async with anyio.create_task_group() as tg:
            # Run the MCP server in a background task
            tg.start_soon(
                mcp_app.run,
                server_read,
                server_write,
                mcp_app.create_initialization_options(),
            )

            # Connect client, call tool, then close
            async with ClientSession(client_read, client_write) as session:
                await session.initialize()
                call_result = await session.call_tool(tool_name, tool_args)

            # Client session closed — cancel the server background task
            tg.cancel_scope.cancel()

    if call_result.content:
        return call_result.content[0].text
    return "No output returned from tool."


def _run_in_thread(coro) -> str:
    """
    Run an async coroutine in a new thread with its own event loop.
    Needed because Streamlit may already have a running loop in the main thread.
    anyio handles cross-platform event loop setup.
    """
    async def _wrapper():
        return await coro
    return anyio.run(_wrapper)


# Main agent

def run_tool_agent(query: str) -> Dict[str, Any]:
    """
    Decide which MCP tool to call, execute it, return a natural language answer.

    Returns dict with: response, tool_name, tool_input, tool_output, error
    """
    tools_description = (
        "1. get_weather(city: str) — Returns current weather for a city (temperature, condition, humidity, wind)\n"
        "2. convert_currency(amount: float, from_currency: str, to_currency: str) — Converts currency using live exchange rates"
    )

    # ── Step 1: LLM picks which tool + args ───────────────────────────────────
    log.debug("Tool selection LLM query: %r", query)
    llm = get_llm(temperature=0.0)
    select_chain = TOOL_SELECT_PROMPT | llm | StrOutputParser()
    selection_raw = select_chain.invoke({
        "tools_description": tools_description,
        "query": query,
    }).strip()
    log.debug("LLM selected: %s", selection_raw)

    match = re.search(r'\{.*\}', selection_raw, re.DOTALL)
    if match:
        selection_raw = match.group(0)

    try:
        selection = json.loads(selection_raw)
    except json.JSONDecodeError as exc:
        log.error("JSON parse failed on tool selection: %s | raw: %s", exc, selection_raw)
        return {
            "response": "I couldn't determine which tool to use for this query. Please try rephrasing.",
            "tool_name": None,
            "tool_input": {},
            "tool_output": None,
            "error": "JSON parse error on tool selection",
        }

    tool_name = selection.get("tool")
    tool_args = selection.get("args", {})
    reason = selection.get("reason", "no_matching_tool")

    if not tool_name:
        if reason == "missing_argument":
            response = (
                "I identified that you want to use a tool, but some required information is missing. "
                "For weather queries, please specify a city name (e.g. 'weather in New York'). "
                "For currency conversions, please provide an amount, a source currency, and a target currency "
                "(e.g. 'convert 100 USD to INR')."
            )
        else:
            response = "I don't have a tool available to answer this question. Try asking about weather or currency rates."

        return {
            "response": response,
            "tool_name": None,
            "tool_input": {},
            "tool_output": None,
            "error": None,
        }

    # ── Step 2: Execute tool via MCP in-memory transport ──────────────────────
    log.debug("Calling tool %r with %s", tool_name, tool_args)
    try:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(_run_in_thread, _call_mcp_tool(tool_name, tool_args))
            tool_output = future.result()
        log.debug("Tool output: %s", tool_output)
    except Exception as e:
        log.error("Tool %r failed - %s: %s", tool_name, type(e).__name__, e)
        log.error("Traceback:\n%s", traceback.format_exc())
        error_detail = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
        return {
            "response": f"The tool '{tool_name}' encountered an error: {error_detail}. This may be due to a network issue or invalid input.",
            "tool_name": tool_name,
            "tool_input": tool_args,
            "tool_output": None,
            "error": error_detail,
        }

    # ── Step 3: Generate natural language answer ───────────────────────────────
    log.debug("Generating answer from tool output")
    answer_chain = ANSWER_PROMPT | llm | StrOutputParser()
    response = answer_chain.invoke({
        "query": query,
        "tool_name": tool_name,
        "tool_input": json.dumps(tool_args),
        "tool_output": tool_output,
    })
    log.debug("Response: %s", response)

    return {
        "response": response,
        "tool_name": tool_name,
        "tool_input": tool_args,
        "tool_output": tool_output,
        "error": None,
    }
