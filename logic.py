# logic.py — LangChain/LangGraph agent logic: supervisor + 3 specialist agents

import os                                      
from dotenv import load_dotenv                 
from langchain_openai import ChatOpenAI        
from langgraph_supervisor import create_supervisor   
from langgraph.prebuilt import create_react_agent    
from langchain.tools import tool               

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()  

# ── Token limits ──────────────────────────────────────────────────────────────
MAX_OUTPUT_TOKENS = 512   
MODEL_NAME        = "gpt-4o-mini"  

# ── Shared LLM instance ───────────────────────────────────────────────────────

llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0,
    max_tokens=MAX_OUTPUT_TOKENS,
    api_key=os.getenv("OPENAI_API_KEY"), 
)


# ── Agent tools ───────────────────────────────────────────────────────────────

@tool
def solve_math(problem: str) -> str:
    """
    Solves a math problem step by step.
    Input: a math question as a string.
    """
    
    response = llm.invoke(
        f"Solve the following math problem step by step, "
        f"showing every calculation clearly:\n\n{problem}"
    )
    return response.content  


@tool
def answer_biology(question: str) -> str:
    """
    Answers a biology question with accurate scientific detail.
    Input: a biology question as a string.
    """
    response = llm.invoke(
        f"Answer the following biology question clearly and accurately. "
        f"Provide scientific detail where relevant:\n\n{question}"
    )
    return response.content


@tool
def answer_history(question: str) -> str:
    """
    Answers a history question with relevant context and dates.
    Input: a history question as a string.
    """
    response = llm.invoke(
        f"Answer the following history question with accurate facts, "
        f"dates, and relevant context:\n\n{question}"
    )
    return response.content


# ── Specialist Agents ─────────────────────────────────────────────────────────


math_agent = create_react_agent(
    model=llm,
    tools=[solve_math],
    name="math_agent",
    prompt=(
        "You are a mathematics expert. "
        "Only answer math-related queries. "
        "Always use the solve_math tool and show every step of the calculation."
    ),
)


biology_agent = create_react_agent(
    model=llm,
    tools=[answer_biology],
    name="biology_agent",
    prompt=(
        "You are a biology expert. "
        "Only answer biology-related queries. "
        "Always use the answer_biology tool."
    ),
)


history_agent = create_react_agent(
    model=llm,
    tools=[answer_history],
    name="history_agent",
    prompt=(
        "You are a history expert. "
        "Only answer history-related queries. "
        "Always use the answer_history tool."
    ),
)


# ── Supervisor ────────────────────────────────────────────────────────────────

supervisor_prompt = (
    "You are the Scholaris supervisor. Your job is to route user queries "
    "to the correct specialist agent based on subject matter.\n\n"
    "Routing rules:\n"
    "- MATH: arithmetic, algebra, calculus, geometry, statistics → math_agent\n"
    "- BIOLOGY: cells, genetics, anatomy, ecology, evolution → biology_agent\n"
    "- HISTORY: historical events, figures, civilisations, dates → history_agent\n"
    "- OUT OF SCOPE: physics, chemistry, computer science, literature, "
    "  or any other subject → respond directly with exactly:\n"
    "  'OUT_OF_SCOPE: This query is outside the supported subjects "
    "  (Math, Biology, History). Please ask a question in one of these areas.'\n\n"
    "Do NOT attempt to answer out-of-scope queries yourself. "
    "Route only to the three agents listed above."
)

workflow = create_supervisor(
    agents=[math_agent, biology_agent, history_agent],
    model=llm,
    prompt=supervisor_prompt,
)

# Compile the graph into a runnable app
app = workflow.compile()


# ── Public entry point ────────────────────────────────────────────────────────

def run_query(query: str) -> dict:
    """
    Runs a user query through the supervisor→agent pipeline.

    Returns a dict with:
        agent   : which agent handled the query (or 'supervisor' for OOS)
        answer  : the final text answer
    """
    
    result = app.invoke({"messages": [{"role": "user", "content": query}]})

   
    messages = result.get("messages", [])
    if not messages:
        return {"agent": "unknown", "answer": "No response generated."}

    last_msg = messages[-1]

    
    answer = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    
    agent_name = "supervisor"
    for msg in reversed(messages):
        name = getattr(msg, "name", None)
        if name and name in ("math_agent", "biology_agent", "history_agent"):
            agent_name = name
            break

    
    if answer.startswith("OUT_OF_SCOPE:"):
        agent_name = "out_of_scope"
        answer = answer.replace("OUT_OF_SCOPE:", "").strip()

    return {"agent": agent_name, "answer": answer}
