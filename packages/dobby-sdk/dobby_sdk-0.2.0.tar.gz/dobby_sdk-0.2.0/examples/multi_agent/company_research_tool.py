"""Company Research Tool - Agent wrapped as a Tool.

This tool wraps an inner agent that researches companies based on job descriptions.
The inner agent has its own web search capability.
"""

from dataclasses import dataclass
from typing import Annotated, Any

from dobby import AgentExecutor, Injected, OpenAIProvider, Tool
from dobby.common_tools import TavilySearchTool
from dobby.types import TextPart, ToolUseEvent, UserMessagePart


# ANSI colors for nested agent logging
class Colors:
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"
    RESET = "\033[0m"


COMPANY_RESEARCH_PROMPT = """You are a company research expert.

Your task is to find companies matching specific criteria based on a job description.

**CRITICAL: Companies must have presence in the target country**

When searching:
- Find GLOBAL companies that HAVE OFFICES/OPERATIONS in the target country
  - Example for India: Google India, Microsoft India, Amazon India
- Find LOCAL companies headquartered in the target country
  - Example for India: Razorpay, Zerodha, Freshworks, Infosys
- DO NOT include companies that only operate outside the target country
- Extract accurate information: company name, industry, location, size
- Prioritize active, operating companies
- Include startups, scale-ups, and established companies
- Mark companies as competitors if they're in the same specific niche

Use the tavily_search tool to find relevant companies.

Return structured data with:
1. Company name
2. Industry/sector
3. Location (headquarters + offices)
4. Company size (employees)
5. Why they're relevant to the JD
6. Competitor status (yes/no)
"""


@dataclass 
class JDContext:
    """Context containing the job description for research tools."""
    job_description: str


@dataclass
class CompanyResearchTool(Tool):
    """Tool that wraps an agent for company research.
    
    This is a nested agent pattern - the tool itself contains an agent
    with its own tools (web search).
    """
    
    name = "research_companies"
    description = """Research and find companies that match the current job description criteria.
Use this when you need to find similar companies, competitors, or potential employers
based on job requirements, industry, location, and company profile.
The job description is already available in context - just specify target country and number of companies."""
    
    # Configuration
    api_key: str = ""
    azure_endpoint: str = ""
    azure_deployment: str = ""
    tavily_api_key: str = ""
    
    def __post_init__(self):
        """Initialize the inner agent."""
        # Provider for inner agent
        self.provider = OpenAIProvider(
            base_url=self.azure_endpoint,
            azure_deployment_id=self.azure_deployment,
            api_key=self.api_key,
        )
        
        # Inner agent has its own web search
        self.search_tool = TavilySearchTool(api_key=self.tavily_api_key)
        
        self.executor = AgentExecutor(
            provider="azure-openai",
            llm=self.provider,
            tools=[self.search_tool],
        )
    
    async def __call__(
        self,
        ctx: Injected[JDContext],  # JD context injected, hidden from LLM
        target_country: Annotated[str, "Target country for company search"] = "India",
        num_companies: Annotated[int, "Number of companies to find"] = 5,
    ) -> dict[str, Any]:
        """Research companies based on job description from context.
        
        Args:
            ctx: Injected context containing the job description
            target_country: Country where companies should have presence
            num_companies: How many companies to find
            
        Returns:
            Dictionary with research results
        """
        job_description = ctx.job_description
        
        query = f"""Analyze this job description and find {num_companies} relevant companies in {target_country}:

{job_description}

Find companies that:
1. Operate in the same industry/domain
2. Have presence in {target_country}
3. Would likely have similar roles
4. Include both large enterprises and startups

Search for specific company information using web search."""

        messages = [UserMessagePart(parts=[TextPart(text=query)])]
        
        result_text = ""
        
        # Stream with logging
        print(f"{Colors.CYAN}    ┌─ [Nested Agent Starting]{Colors.RESET}")
        
        # Import event types for pattern matching
        from dobby.types import TextDeltaEvent
        
        async for event in self.executor.run_stream(
            messages,
            system_prompt=COMPANY_RESEARCH_PROMPT,
        ):
            match event:
                case TextDeltaEvent(delta=delta):
                    result_text += delta
                    # Stream nested output
                    print(f"{Colors.DIM}{delta}{Colors.RESET}", end="", flush=True)
                case ToolUseEvent(name=name, inputs=inputs):
                    inputs_str = str(inputs)
                    if len(inputs_str) > 80:
                        inputs_str = inputs_str[:80] + "..."
                    print(f"\n{Colors.YELLOW}    │ 🔧 [Inner] {name}{Colors.RESET}")
                    print(f"{Colors.DIM}    │    {inputs_str}{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}    └─ [Nested Agent Complete]{Colors.RESET}")
        
        return {
            "target_country": target_country,
            "num_companies": num_companies,
            "findings": result_text,
        }
