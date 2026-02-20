import asyncio
from agents.orchestrator import AgentOrchestrator

async def main():
    orc = AgentOrchestrator()
    orc.router.llm = orc.router.llm.with_config({"tags": ["router_llm"]})
    
    async for event in orc.workflow.astream_events(
        {"messages": [], "query": "주식 투자란?", "classifications": [], "edu_result": [], "news_result": [], "report_result": [], "value_chain_result": [], "final_answer": "", "image_path": None},
        version="v1"
    ):
        kind = event["event"]
        node = event.get("metadata", {}).get("langgraph_node")
        if kind == "on_chat_model_stream":
            print(f"[{node}] {event['data']['chunk'].content}", end="", flush=True)

asyncio.run(main())
