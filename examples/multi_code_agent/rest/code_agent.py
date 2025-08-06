from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import traceroot
import re

load_dotenv()

logger = traceroot.get_logger()


class CodeAgent:

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.system_prompt = (
            "You are a Python coding agent. "
            "Your job is to write Python code based on "
            "the user's query and plan. "
            "IMPORTANT GUIDELINES:\n"
            "1. Write clean, executable Python code\n"
            "2. Include necessary imports\n"
            "3. Ensure code runs in a Python env\n"
            "4. Use common libraries if needed\n"
            "5. Return only code, no explanations unless comments\n"
            "6. Use historical context to avoid repeats\n"
            "Your response should be ONLY the Python code that solves the problem.")
        self.code_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", ("{query}\n\nPlan: {plan}\n\n"
                       "Historical context: {historical_context}\n\n"
                       "Please write Python code to implement this."))
        ])

    @traceroot.trace()
    def generate_code(
        self,
        query: str,
        plan: str,
        historical_context: str = "",
    ) -> str:
        formatted_prompt = self.code_prompt.format(
            query=query, plan=plan, historical_context=historical_context)
        logger.info(f"CODE AGENT prompt:\n{formatted_prompt}")

        chain = self.code_prompt | self.llm
        response = chain.invoke({
            "query": query,
            "plan": plan,
            "historical_context": historical_context,
        })

        # Extract code, cleaning markdown fences if present
        code = response.content.strip()
        # Remove leading markdown fences
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        # Remove trailing markdown fences and any surrounding whitespace
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()
        logger.info(f"Generated code:\n{code}")
        return code

def create_code_agent():
    return CodeAgent()