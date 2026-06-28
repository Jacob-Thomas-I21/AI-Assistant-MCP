"""
tools/mcp_server.py — MCP server with two tools: weather and currency.

Run this directly: python tools/mcp_server.py
"""
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("enterprise-tools")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Advertise available tools to any MCP client."""
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for a city. Returns temperature, condition, humidity, and wind speed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. 'London' or 'New York'",
                    }
                },
                "required": ["city"],
            },
        ),
        types.Tool(
            name="convert_currency",
            description="Convert an amount from one currency to another using live exchange rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert",
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code, e.g. 'USD'",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code, e.g. 'INR'",
                    },
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute the requested tool and return results."""
    if name == "get_weather":
        result = await _get_weather(arguments.get("city", ""))
    elif name == "convert_currency":
        result = await _convert_currency(
            arguments.get("amount", 1),
            arguments.get("from_currency", "USD"),
            arguments.get("to_currency", "INR"),
        )
    else:
        result = f"Unknown tool: {name}"

    return [types.TextContent(type="text", text=result)]


async def _get_weather(city: str) -> str:
    """Fetch current weather from wttr.in (free, no API key required)."""
    if not city:
        return "Error: city name is required."
    try:
        url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        current = data["current_condition"][0]
        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", city)
        country = area.get("country", [{}])[0].get("value", "")

        temp_c = current["temp_C"]
        temp_f = current["temp_F"]
        feels_c = current["FeelsLikeC"]
        condition = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind_kmph = current["windspeedKmph"]
        wind_dir = current["winddir16Point"]
        visibility = current["visibility"]

        return (
            f"Weather in {area_name}, {country}:\n"
            f"  Temperature: {temp_c}°C ({temp_f}°F), feels like {feels_c}°C\n"
            f"  Condition: {condition}\n"
            f"  Humidity: {humidity}%\n"
            f"  Wind: {wind_kmph} km/h {wind_dir}\n"
            f"  Visibility: {visibility} km"
        )
    except httpx.HTTPStatusError as e:
        return f"Error fetching weather: HTTP {e.response.status_code}. Check the city name."
    except Exception as e:
        return f"Error fetching weather: {e}"


async def _convert_currency(amount: float, from_cur: str, to_cur: str) -> str:
    """Convert currency using exchangerate-api.com (free tier, no key needed)."""
    from_cur = from_cur.upper().strip()
    to_cur = to_cur.upper().strip()
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_cur}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        rates = data.get("rates", {})
        if to_cur not in rates:
            return f"Error: currency '{to_cur}' not found. Use standard 3-letter codes like USD, EUR, INR, GBP."

        rate = rates[to_cur]
        converted = round(amount * rate, 2)
        date = data.get("date", "unknown")

        return (
            f"Currency Conversion:\n"
            f"  {amount} {from_cur} = {converted} {to_cur}\n"
            f"  Exchange rate: 1 {from_cur} = {rate} {to_cur}\n"
            f"  Rate date: {date}"
        )
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code}. Check the currency code (e.g. USD, EUR, INR)."
    except Exception as e:
        return f"Error converting currency: {e}"


if __name__ == "__main__":
    asyncio.run(stdio_server(app))
