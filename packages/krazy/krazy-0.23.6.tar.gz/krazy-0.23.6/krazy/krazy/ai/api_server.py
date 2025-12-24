from fastapi import FastAPI
from pydantic import BaseModel, Field, create_model
from typing import Optional, List, Dict, Any, Literal
from krazy.ai.agent import AIAssistant
from krazy.ai.general import QueryRequest, build_dynamic_schema_recursive
from krazy.ai.tools import Config
from krazy.ai.tools import PostgresQueryTool

def create_api(assistant: AIAssistant) -> FastAPI:
    app = FastAPI()

    @app.post("/invoke")
    def ask_query(payload: QueryRequest):
        try:
            if payload.output_schema:
                dynamic_model = build_dynamic_schema_recursive("DynamicModel", dict(payload.output_schema))
                assistant.output_schema = dynamic_model
                assistant.reinitialize()

            assistant.invoke(
                prompt=payload.query,
                use_memory=payload.use_memory, # type: ignore
                save_chat_history=payload.save_chat_history # type: ignore
            )

            if assistant.response_json is not None:
                return assistant.response_json
            else:
                return assistant.response
        except Exception as e:
            return {"error": str(e)}

    @app.get("/memory")
    def get_memory(query: str):
        try:
            memory = assistant.retrieve_memory(query)
            return {"query": query, "memory": memory}
        except Exception as e:
            return {"error": str(e)}
        
    @app.get("/sample_payload")
    def get_sample_payload():
        sample_payload = {
            "query": "What is the capital of France?",
            "use_memory": True,
            "save_chat_history": True,
            "llm": "azure or ollama",
            "schema": {
                'hint': 'use function extract_dynamic_schema from module general'
            }
        }
        return sample_payload

    return app

# Example usage:
# uvicorn agent_api:app --port 8000 --reload
