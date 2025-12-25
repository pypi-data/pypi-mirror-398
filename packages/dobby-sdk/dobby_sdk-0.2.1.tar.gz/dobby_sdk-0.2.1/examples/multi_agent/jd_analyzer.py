#!/usr/bin/env python
"""Multi-Agent JD Analyzer.

Master orchestrator agent that analyzes job descriptions using:
1. Direct web search for general research
2. Company Research Tool (nested agent) for finding relevant companies

Usage:
    export AZURE_OPENAI_API_KEY=...
    export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
    export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
    export TAVILY_API_KEY=tvly-...
    python jd_analyzer.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from dobby import AgentExecutor, OpenAIProvider
from dobby.common_tools import TavilySearchTool
from dobby.types import (
    ReasoningDeltaEvent,
    ReasoningEndEvent,
    ReasoningStartEvent,
    StreamEndEvent,
    StreamStartEvent,
    TextDeltaEvent,
    TextPart,
    ToolResultEvent,
    ToolUseEndEvent,
    ToolUseEvent,
    UserMessagePart,
)

from company_research_tool import CompanyResearchTool, JDContext

load_dotenv()


# ANSI colors for CLI
class Colors:
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


MASTER_AGENT_PROMPT = """You are a Job Description Analyzer and Talent Research Assistant.

Your capabilities:
1. **Web Search (tavily_search)**: For general research about roles, industries, skills, trends
2. **Company Research (research_companies)**: For finding relevant companies that match the JD criteria

When given a job description, you should:
1. First analyze the JD to understand:
   - Required skills and experience
   - Industry/domain
   - Company profile (size, stage, culture)
   - Location requirements
   
2. Use web search for:
   - Understanding the role and market
   - Finding salary benchmarks
   - Researching industry trends
   
3. Use company research tool for:
   - Finding similar companies with matching roles
   - Identifying competitors
   - Discovering potential employers in target locations

Provide comprehensive analysis with actionable insights.
"""


def print_header():
    """Print CLI header."""
    print(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}   🎯 Multi-Agent JD Analyzer{Colors.RESET}")
    print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.DIM}Master Agent + Company Research Agent (nested){Colors.RESET}")
    print(f"{Colors.DIM}Commands:{Colors.RESET}")
    print(f"{Colors.DIM}  'jd'    - Load job description from PDF file{Colors.RESET}")
    print(f"{Colors.DIM}  'clear' - Reset chat history{Colors.RESET}")
    print(f"{Colors.DIM}  'quit'  - Exit{Colors.RESET}\n")


def read_pdf_file(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"{Colors.RED}Error: pypdf not installed. Run: pip install pypdf{Colors.RESET}")
        return ""
    
    path = file_path.strip().strip("'\"")  # Remove quotes if present
    
    if not os.path.exists(path):
        print(f"{Colors.RED}Error: File not found: {path}{Colors.RESET}")
        return ""
    
    try:
        reader = PdfReader(path)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n".join(text_parts)
        print(f"{Colors.GREEN}✓ PDF loaded: {len(reader.pages)} pages, {len(full_text)} chars{Colors.RESET}")
        return full_text
        
    except Exception as e:
        print(f"{Colors.RED}Error reading PDF: {e}{Colors.RESET}")
        return ""


async def stream_agent_response(
    executor: AgentExecutor, 
    messages: list, 
    system_prompt: str,
    context: JDContext | None = None,
):
    """Stream agent response with colored output."""
    
    async for event in executor.run_stream(
        messages,
        system_prompt=system_prompt,
        reasoning_effort="low",
        context=context,
    ):
        match event:
            case StreamStartEvent(model=model):
                print(f"\n{Colors.DIM}[Model: {model}]{Colors.RESET}\n")

            case TextDeltaEvent(delta=delta):
                print(delta, end="", flush=True)

            case ReasoningStartEvent():
                print(f"\n{Colors.BLUE}💭 Reasoning:{Colors.RESET} ", end="")

            case ReasoningDeltaEvent(delta=delta):
                print(f"{Colors.DIM}{delta}{Colors.RESET}", end="", flush=True)

            case ReasoningEndEvent():
                print("\n")

            case ToolUseEvent(name=name, inputs=inputs):
                if name == "research_companies":
                    print(f"\n{Colors.MAGENTA}{'─' * 40}{Colors.RESET}")
                    print(f"{Colors.MAGENTA}🔍 NESTED AGENT: {name}{Colors.RESET}")
                    print(f"{Colors.DIM}   Country: {inputs.get('target_country', 'N/A')}{Colors.RESET}")
                    print(f"{Colors.MAGENTA}{'─' * 40}{Colors.RESET}\n")
                else:
                    print(
                        f"\n{Colors.YELLOW}🔧 Tool Call:{Colors.RESET} "
                        f"{Colors.BOLD}{name}{Colors.RESET}"
                    )
                    # Truncate long inputs
                    inputs_str = str(inputs)
                    if len(inputs_str) > 100:
                        inputs_str = inputs_str[:100] + "..."
                    print(f"{Colors.DIM}   Inputs: {inputs_str}{Colors.RESET}\n")

            case ToolResultEvent(name=name, result=result):
                output = str(result)
                if len(output) > 300:
                    output = output[:300] + "..."
                
                if name == "research_companies":
                    print(f"{Colors.MAGENTA}{'─' * 40}{Colors.RESET}")
                    print(f"{Colors.GREEN}✓ Nested Agent Complete{Colors.RESET}")
                    print(f"{Colors.DIM}{output}{Colors.RESET}")
                    print(f"{Colors.MAGENTA}{'─' * 40}{Colors.RESET}\n")
                else:
                    print(f"{Colors.GREEN}✓ Tool Result ({name}):{Colors.RESET}")
                    print(f"{Colors.DIM}   {output}{Colors.RESET}\n")

            case ToolUseEndEvent():
                pass

            case StreamEndEvent(usage=usage):
                if usage:
                    print(f"\n{Colors.DIM}[Tokens: {usage.total_tokens}]{Colors.RESET}")


async def chat_loop():
    """Interactive chat loop with the multi-agent system."""
    
    # Get API keys
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not all([azure_key, azure_endpoint, tavily_key]):
        print(f"{Colors.RED}Error: Missing environment variables{Colors.RESET}")
        print("Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, TAVILY_API_KEY")
        sys.exit(1)
    
    provider = OpenAIProvider(
        base_url=azure_endpoint,
        azure_deployment_id=azure_deployment,
        api_key=azure_key,
    )
    
    search_tool = TavilySearchTool(api_key=tavily_key)
    
    company_research_tool = CompanyResearchTool(
        api_key=azure_key,
        azure_endpoint=azure_endpoint,
        azure_deployment=azure_deployment,
        tavily_api_key=tavily_key,
    )
    
    # Create master executor with both tools
    executor = AgentExecutor(
        provider="azure-openai",
        llm=provider,
        tools=[search_tool, company_research_tool],
    )
    
    print_header()
    
    # Conversation history and JD context
    messages: list = []
    current_jd: str | None = None
    
    while True:
        try:
            # Get user input
            print(f"{Colors.CYAN}{'─' * 60}{Colors.RESET}")
            user_input = input(f"{Colors.BOLD}You:{Colors.RESET} ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print(f"\n{Colors.DIM}Goodbye!{Colors.RESET}\n")
                break
            
            if user_input.lower() == "clear":
                messages = []
                current_jd = None
                print(f"{Colors.DIM}Chat history and JD cleared.{Colors.RESET}\n")
                continue
            
            # Handle PDF file input
            if user_input.lower() == "jd":
                file_path = input(f"{Colors.YELLOW}Enter PDF file path:{Colors.RESET} ").strip()
                if not file_path:
                    print(f"{Colors.DIM}No path entered.{Colors.RESET}\n")
                    continue
                jd_text = read_pdf_file(file_path)
                if not jd_text:
                    continue
                current_jd = jd_text  # Store for context injection
                user_input = f"Please analyze this job description and find relevant companies:\n\n{jd_text}"
                print()
            
            # Add user message
            messages.append(UserMessagePart(parts=[TextPart(text=user_input)]))
            
            print(f"\n{Colors.BOLD}Assistant:{Colors.RESET}")
            
            jd_context = JDContext(job_description=current_jd) if current_jd else None
            
            await stream_agent_response(executor, messages, MASTER_AGENT_PROMPT, jd_context)
            
            print()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.DIM}Interrupted. Goodbye!{Colors.RESET}\n")
            break
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.RESET}\n")


def main():
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
