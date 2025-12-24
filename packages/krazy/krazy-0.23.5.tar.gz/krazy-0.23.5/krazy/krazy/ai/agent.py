import chromadb
# from chromadb.utils.embedding_functions import EmbeddingFunction
from chromadb.api.types import EmbeddingFunction
import openai
import os
from crewai import Agent, Task, LLM, Crew, Process
from pathlib import Path
from typing import Dict, List, Optional, Any
from krazy.ai.tools import (
    PDFReaderTool, CSVCustomReaderTool, WebSearchTool, 
    ExcelImportTool, CSVorExcelExportTool,
    WordFileReaderTool, PowerPointFileReaderTool, FolderListFilesTool, Config, PostgresQueryTool
)
from pydantic import BaseModel
from typing import Optional, Union
from krazy.ai.tools import Config
import json
import tiktoken
import fitz
import pandas as pd
import io
import traceback
from krazy.ai.general import credentials

# ✅ Custom Azure OpenAI Embedding Function for ChromaDB
class AzureOpenAIEmbeddingFunction(EmbeddingFunction):
    """
    A custom embedding function that uses Azure OpenAI to generate vector embeddings for input texts.

    Attributes:
        api_key (str): Azure OpenAI API key.
        api_base (str): Azure endpoint base URL.
        api_version (str): Azure OpenAI API version.
        model (str): The model used to generate embeddings (e.g., 'text-embedding-ada-002').

    Methods:
        __call__(input_texts: List[str]) -> List[List[float]]:
            Generates embeddings for a list of input strings.
    """

    def __init__(self, api_key: str, api_base: str, api_version: str, model: str = 'text-embedding-ada-002'):
        if not api_key:
            raise ValueError("Azure OpenAI API key is required.")
        if not api_base:
            raise ValueError("Azure API base endpoint is required.")
        if not api_version:
            raise ValueError("Azure API version is required.")

        self.api_key = api_key
        self.api_base = api_base
        self.api_version = api_version
        self.model = model

    def __call__(self, input_texts: list) -> list:
        """
        Generates embeddings using Azure OpenAI for the given input texts.

        Args:
            input_texts (list): A list of strings for which embeddings are to be generated.

        Returns:
            list: A list of embedding vectors corresponding to the input texts.

        Raises:
            ValueError: If input_texts is not a valid list of strings.
            RuntimeError: If Azure OpenAI fails to return valid embeddings.
        """
        if not isinstance(input_texts, list) or not all(isinstance(t, str) for t in input_texts):
            raise ValueError("input_texts must be a list of strings.")

        try:
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.api_base,
                api_version=self.api_version
            )

            response = client.embeddings.create(
                input=input_texts,
                model=self.model
            )

            return [r.embedding for r in response.data]

        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings via Azure OpenAI: {str(e)}")



# ✅ AI Assistant Class with ChromaDB-Based Memory
class AIAssistant:
    def __init__(self,
                 config: Config,
                 db_path="DBs/chroma_memory",
                 embedding_model: str = 'text-embedding-ada-002',
                 output_schema: Optional[BaseModel] = None,
                 llm_choice:str = 'openai-azure',
                 verbose=True):

        # ✅ Ensure ChromaDB path exists and init memory client
        project_dir = Path(__file__).parent
        absolute_db_path = project_dir.joinpath(db_path)
        os.makedirs(absolute_db_path, exist_ok=True)

        self.config = config

        self.memory_client = chromadb.PersistentClient(path=str(absolute_db_path))
        self.memory_collection = self.memory_client.get_or_create_collection(
            name="assistant_memory",
            embedding_function=AzureOpenAIEmbeddingFunction(
                api_key=config.api_key, # type: ignore
                api_base=self.config.endpoint, # type: ignore
                api_version=self.config.deployment_name, # type: ignore
                model=embedding_model
            )
        )

        # output schema
        self.output_schema = output_schema

        # output variables
        self.response_full = None
        self.response = None
        self.response_json = None
        self.response_dict = None
        self.response_pydantic = None
        self.verbose = verbose

        # ✅ Tools
        self.tools_list = []
        self.pdf_reader_tool = PDFReaderTool()
        self.csv_reader_tool = CSVCustomReaderTool()
        self.web_search_tool = WebSearchTool()
        self.excel_import_tool = ExcelImportTool()
        self.csv_export_tool = CSVorExcelExportTool()
        self.word_reader_tool = WordFileReaderTool()
        self.powerpoint_reader_tool = PowerPointFileReaderTool()
        self.folder_list_files_tool = FolderListFilesTool()
        self.postgres_query_tool = None
        self.web_search_tavliy_tool = None

        self.tools_list.extend([
                self.pdf_reader_tool, self.csv_reader_tool, self.web_search_tool,
                self.excel_import_tool, self.csv_export_tool,
                self.word_reader_tool, self.powerpoint_reader_tool, self.folder_list_files_tool
            ])

        self.llm_options = {'azure': LLM( # using azure open ai api
            model=f"azure/{self.config.model}",
            api_key=self.config.api_key,
            api_base=self.config.endpoint,
            api_version=self.config.deployment_name,
            temperature=0
        ), 'ollama': LLM(
            model='ollama/deepseek-r1:7b',
            base_url='http://localhost:11434',
            temperature=0
        ), 'openai-azure': LLM( # open ai model with azure deployment without using azure open ai api
            base_url=f'{self.config.endpoint}',
            model=f"openai/{self.config.model}",
            api_key=self.config.api_key,
            temperature=0
        )}

        # ✅ LLM Setup
        self.llm_choice = llm_choice
        self.llm = self.llm_options[self.llm_choice]

        # initialize crew
        self.reinitialize()

    def reinitialize(self):
            # ✅ LLM
            self.llm = self.llm_options[self.llm_choice]

            # ✅ Agent
            self.agent = None
            self.agent_generator()

            # ✅ Task
            self.task = None
            self.task_generator()

            # ✅ Crew
            self.crew = None
            self.crew_generator()

    def agent_generator(self):
        self.agent = Agent(
            role="AI Assistant",
            goal="Answer user queries using data and long-term memory if provided.",
            backstory="You are a knowledgeable assistant with memory capabilities.",
            llm=self.llm,
            verbose=self.verbose,
            tools = self.tools_list
        )

    def task_generator(self):
        self.task = Task(
            description= "{query}",
            expected_output = "A response to question based on given information.",
            agent = self.agent,
            output_json=self.output_schema # type: ignore
        )
    
    def crew_generator(self):
        self.crew = Crew(
            name="AI_Memory_Crew",
            agents=[self.agent], # type: ignore
            tasks=[self.task], # type: ignore
            process=Process.sequential
        )

    def read_pdf(self, file_path: str, password: str) -> str:
        pdf_text = ""

        try:
            # Open the PDF file
            pdf_file = fitz.open(file_path)

            # Check if the file is encrypted
            if pdf_file.needs_pass:
                if not pdf_file.authenticate(password):
                    raise ValueError("Invalid password provided for the PDF file.")
            
            # Extract text from each page
            for page in pdf_file:
                pdf_text += page.get_text() # type: ignore

            pdf_file.close()
            return pdf_text

        except Exception as e:
            raise RuntimeError(f"Error reading PDF: {str(e)}")


    def prompt_generator(self, query, data, memory):
        if query:
            prompt = str(query)
        else:
            prompt = f'Answer this question:\n Question:{query}.'
        
        if data:
            prompt += f"\nUse this data to answer the question:\nData: {str(data)}."

        if memory != None:
            prompt += f"\\Use this context:\nContext: {str(memory)}."

        return prompt

    def store_memory(self, user_input, agent_response):
        self.memory_collection.add(
            ids=[str(len(self.memory_collection.get()["ids"]))],
            documents=[f"User: {user_input}\nAssistant: {agent_response}"]
        )

    def retrieve_memory(self, query, top_k=5):
        results = self.memory_collection.query(query_texts=[query], n_results=top_k)
        return "\n".join(results["documents"][0]) if results["documents"] else "No relevant memories found."

    def extract_json_from_text(self) -> Union[dict, list, None]:
        """
        Attempts to extract the first valid JSON object or array from a string.

        Args:
            text (str): A string that may contain JSON.

        Returns:
            dict | list | None: Parsed JSON object or array if found, otherwise None.
        """
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(self.response): #type: ignore
            if self.response[idx] in ('{', '['):  # JSON must start with object or array # type: ignore
                try:
                    result, end_idx = decoder.raw_decode(self.response[idx:]) # type: ignore
                    return result
                except json.JSONDecodeError:
                    pass
            idx += 1
        return None
    
    def tokens_count(self, text, encoding_name="cl100k_base"):
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    

    def chunk_text(self, text, chunk_size=1000, encoding_name="cl100k_base"):
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)

        chunks = []
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

        return chunks

    def invoke(self, prompt, data=None, use_memory=False, save_chat_history=False, response_format="text"):
        if use_memory:
            retrieved_memories = self.retrieve_memory(prompt)
        else:
            retrieved_memories = None

        generated_prompt = self.prompt_generator(query=prompt, data=None, memory=retrieved_memories)

        self.response_full = self.crew.kickoff(inputs={"query": generated_prompt}) #type: ignore

        if "content_filter" in str(self.response_full):
            return "⚠️ Your request was blocked due to content policy violations. Please rephrase and try again."

        try:
            self.response = self.response_full.raw
        except Exception as e:
            self.response = f"Error: {e}"

        if save_chat_history:
            self.store_memory(prompt, self.response)

        try:
            if self.output_schema:
                self.response_pydantic = self.output_schema.model_validate_json(self.response)
                self.response_dict = self.response_pydantic.model_dump()
                self.response_json = self.response_pydantic.model_dump_json()
            else:
                try:
                    self.response_json = self.extract_json_from_text()
                    self.response_dict = json.loads(self.response_json) # type: ignore
                except:
                    self.response_json = None
                    self.response_dict = None

        except Exception as e:
            try:
                # fallback to json exractor
                extracted_val = self.extract_json_from_text()
                if isinstance(extracted_val, dict):
                    self.response_dict = extracted_val
                    self.response_json = json.dumps(extracted_val)
            except Exception as e:
                self.response_dict = None
                self.response_json = None
                print(f"Error in output schema validation: {e}")
            
        try:
            if response_format == "json" and self.response_json is not None:
                return self.response_json
            elif response_format == "dict":
                return self.response_dict
            elif response_format == "pydantic":
                return self.response_pydantic
            elif response_format == 'text':
                return self.response
            else:
                return self.response
        except Exception as e:
            return f"Error: {e}"

    def invoke_extract_big_pdf(
        self,
        prompt: str,
        file_path: str,
        chunk_size: int = 500,
        chunks_to_process: int = 2,
        chunk_start: int = 0,
        password: str = None # type: ignore
    ) -> Dict[str, Union[List[Union[dict, str]], str]]:
        """
        Extracts structured or textual responses from a large PDF file by splitting it into manageable text chunks,
        invoking an LLM-based agent on each chunk, and aggregating the outputs. If no structured (dict) response is 
        returned, a follow-up summarization is performed on the raw responses.

        Args:
            prompt (str): Instruction or question for the AI to answer.
            file_path (str): Absolute or relative path to the target PDF file.
            chunk_size (int, optional): Number of tokens per chunk (default is 500).
            chunks_to_process (int, optional): Maximum number of chunks to process (default is 2).
            chunk_start (int, optional): Starting chunk index for partial processing (default is 0).
            password (str, optional): Password for encrypted PDF files.

        Returns:
            Dict[str, Union[List[Union[dict, str]], str]]: A dictionary where the key is the file path, and the value
            is either a list of structured responses (dictionaries or strings), or a summarized response string
            generated from all chunks if none produced structured output.
        """

        # Read and chunk PDF
        pdf_text = self.read_pdf(file_path=file_path, password=password)
        chunks = self.chunk_text(pdf_text, chunk_size=chunk_size)

        # Bound the chunk range
        total_chunks = len(chunks)
        if chunk_start >= total_chunks:
            raise ValueError("chunk_start is beyond the total number of chunks.")
        
        end_index = min(chunk_start + chunks_to_process, total_chunks)

        all_responses = []
        for i in range(chunk_start, end_index):
            full_prompt = f'{prompt}\n\nContent to be used to answer user question:\n{chunks[i]}'
            print(f'Processing chunk {i + 1}/{total_chunks}, Prompt length: {len(full_prompt)}')

            try:
                self.invoke(prompt=full_prompt, data=None, use_memory=False, save_chat_history=False)
                if self.response_dict is not None:
                    all_responses.append(self.response_dict)
                else:
                    all_responses.append(self.response)

            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                all_responses.append([{"error": str(e), 'chunk': chunks[i]}])

        if any(isinstance(item, dict) for item in all_responses):
            final_response = all_responses
        else:
            final_response = self.invoke(prompt=f'Process these previous AI assistant responses based on user question. \\User question: {prompt}. \n Prvious AI assistant responses: {all_responses}')

        return {'file_path':file_path, 'response': final_response, 'text_extracted': pdf_text}

    
    def clean_data(self, prompt: str, df: pd.DataFrame, max_attempts: int = 3) -> pd.DataFrame:
        """
        Executes data cleaning operations on a DataFrame using iterative LLM code generation and correction.

        Args:
            prompt (str): Instruction to clean or transform the data.
            df (pd.DataFrame): The input DataFrame to be cleaned.
            max_attempts (int): Number of retry attempts if generated code fails.

        Returns:
            pd.DataFrame: The cleaned DataFrame.

        Raises:
            RuntimeError: If cleaning fails after max_attempts.
        """
        # Sample data for LLM context
        sample_data = df.head(10).to_csv(index=False)
        error_message = None

        self.output_schema = None
        self.reinitialize()

        previous_code = None

        for attempt in range(1, max_attempts + 1):
            try:

                # Construct LLM prompt
                if attempt == 1:
                    instruction = (
                        f"You are a Python data analyst. A user wants to clean a pandas DataFrame using the instruction: '{prompt}'.\n"
                        f"Here is the sample data:\n{sample_data}\n\n"
                        f"Generate Python code that modifies a DataFrame called `df`. "
                        f"Only return the code snippet. Use `errors='coerce'` for datetime conversions. "
                        f"Do not include explanations or print statements."
                    )
                else:
                    instruction = (
                        f"Previous code that was run and gave error is : {previous_code}\n\n"
                        f"The previous code raised this error:\n{error_message}\n\n"
                        f"Please correct it while continuing to satisfy this original instruction: '{prompt}'.\n"
                        f"Here is the sample data again:\n{sample_data}\n\n"
                        f"Return corrected Python code that modifies a DataFrame `df` safely and robustly."
                    )

                # Ask the agent for updated code
                python_code = self.invoke(prompt=instruction, use_memory=False, save_chat_history=False)
                previous_code = python_code

                if self.verbose:
                    print(f"\n--- Attempt {attempt} ---\nGenerated Python Code:\n{python_code}")

                # Try executing the code
                local_vars = {'df': df.copy()}
                exec(python_code, {"pd": pd}, local_vars)

                # Return modified DataFrame if successful
                if 'df' in local_vars and isinstance(local_vars['df'], pd.DataFrame):
                    return local_vars['df']
                else:
                    raise RuntimeError("Code execution did not return a valid DataFrame.")

            except Exception as e:
                error_message = traceback.format_exc()
                if self.verbose:
                    print(f"⚠️ Error in attempt {attempt}: {e}\n{error_message}")

        # Final failure after all attempts
        raise RuntimeError(f"Data cleaning failed after {max_attempts} attempts. Last error:\n{error_message}")

def assistant_initialize(credentials_dict:Optional[dict]=None, llm_choice:str='azure') -> AIAssistant:
    '''
    Initializes the AI Assistant with ChromaDB memory and PostgreSQL query tool.'''
    
    if credentials_dict is None:
        [credentials_dict, postgres_params] = credentials()
    else:
        postgres_params = {
            'dbname': credentials_dict['postgres_dbname'],
            'host': credentials_dict['postgres_host'],
            'password': credentials_dict['postgres_password'],
            'port': credentials_dict['postgres_port'],
            'user': credentials_dict['postgres_user']
        }

    config = Config(credentials_dict)
    assistant = AIAssistant(config, db_path='DBs/chroma_memory', verbose=True,llm_choice=llm_choice)

    postgres_tool = PostgresQueryTool(postgres_params)
    assistant.tools_list.append(postgres_tool)
    assistant.reinitialize()
    return assistant