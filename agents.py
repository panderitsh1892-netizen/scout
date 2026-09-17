import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url

load_dotenv()


def extract_text(content) -> str:
    """Extract plain text from LLM response whether it is a string or structured block list."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and 'text' in block:
                parts.append(block['text'])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def get_llm():
    """
    Initialize the LLM. Supports Google Gemini (free) or OpenAI based on available keys.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if openai_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
    elif google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-flash-lite-latest",
            google_api_key=google_key,
            temperature=0
        )
    else:
        raise ValueError(
            "No API key found. Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file."
        )


llm = get_llm()


# ── 1st agent: Search Agent ──
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )


# ── 2nd agent: Reader Agent ──
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )


# ── Writer Chain ──
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ── Critic Chain ──
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
