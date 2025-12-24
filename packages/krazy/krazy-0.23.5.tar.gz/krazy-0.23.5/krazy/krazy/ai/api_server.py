from fastapi import FastAPI
from pydantic import BaseModel, Field, create_model
from typing import Optional, List, Dict, Any, Literal
from krazy.ai.agent import AIAssistant
from krazy.ai.general import QueryRequest, build_dynamic_schema_recursive
from krazy.ai.tools import Config
from krazy.ai.tools import PostgresQueryTool


def create_api(config: Config, llm_choice:Literal['azure', 'ollama', 'openai-azure']='openai-azure') -> FastAPI:
    app = FastAPI()
    assistant = AIAssistant(verbose=True, config=config, llm_choice=llm_choice)

    @app.post("/invoke")
    def ask_query(payload: QueryRequest):
        try:
            if payload.llm in assistant.llm_options:
                if assistant.llm_choice != payload.llm:
                    assistant.llm = assistant.llm_options[payload.llm]
                    assistant.reinitialize()
            else:
                return {"error": f"LLM '{payload.llm}' not supported. List of suppoerted LLMs: {list(assistant.llm_options.keys())}"}

            if payload.output_schema:
                dynamic_model = build_dynamic_schema_recursive("DynamicModel", dict(payload.output_schema))
                assistant.output_schema = dynamic_model
                assistant.reinitialize()

            if config.postgres_password:
                try:
                    postgres_tool = PostgresQueryTool(conn_params={
                        'host': config.postgres_host, # type: ignore
                        'port': config.postgres_port, 
                        'user': config.postgres_user, 
                        'password': config.postgres_password, 
                        'database': config.postgres_dbname})
                    assistant.tools_list.extend([postgres_tool])
                    assistant.reinitialize()
                except Exception as e:
                    print(f"Error initializing Postgres tool: {e}")

            assistant.invoke(
                prompt=payload.query,
                use_memory=payload.use_memory, # type: ignore
                save_chat_history=payload.save_chat_history # type: ignore
            )

            # if payload.llm == 'ollama':
            #     assistant.llm_options = 'ollama' #type: ignore
            #     assistant.reinitialize()

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
