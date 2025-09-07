from google.adk.tools import tool

@tool
async def create_event(ctx) -> str:
    event_data = ctx.session.state.get("parsed_data", {})
    return f"Event created: {event_data}"
