import asyncio
import os

from timbal import Agent

# os.environ.pop("ANTHROPIC_API_KEY", None)
# os.environ["TIMBAL_APP_ID"] = "172"
os.environ["TIMBAL_LOG_EVENTS"] = "START,OUTPUT,DELTA"


def get_datetime():
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


agent = Agent(
    name="test-proxies",
    model="anthropic/claude-haiku-4-5",  # type: ignore
    tools=[get_datetime],  # type: ignore
    model_params={"max_tokens": 2048},  # type: ignore
)


async def main():
    await agent(prompt="how are you?", max_tokens=128).collect()


if __name__ == "__main__":
    asyncio.run(main())
