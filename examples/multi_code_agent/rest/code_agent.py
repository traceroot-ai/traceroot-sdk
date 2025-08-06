from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import traceroot

load_dotenv()

logger = traceroot.get_logger()


class CodeAgent:

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.system_prompt = (
            "You are a Python coding agent. Your job is to write Python code based on "
            "the user's query and plan. IMPORTANT GUIDELINES:\n"
            "1. Write clean, executable Python code\n"
            "2. Include necessary imports\n"
            "3. Make sure the code can be executed in a Python environment\n"
            "4. If the task requires external libraries, use common ones like requests, pandas, numpy, etc.\n"
            "5. Return only the Python code, no explanations unless in comments\n"
            "6. If historical context is provided, learn from previous failures and avoid repeating the same mistakes\n"
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
            "historical_context": historical_context
        })

        # Clean up the response to extract just the code
        code = response.content.strip()

        # Remove markdown fences and code blocks if present
        # This prevents stray ``` lines causing syntax errors
        filtered_lines = [line for line in code.splitlines() if not line.strip().startswith("```")]
        code = "\n".join(filtered_lines)

        logger.info(f"Generated code:\n{code}")
        return code


def create_code_agent():
    return CodeAgent()
