from __future__ import annotations
from typing import List
from parrot.bots.agent import BasicAgent
from parrot.tools import AbstractTool
from parrot.tools.nextstop import StoreInfo, EmployeeToolkit
from parrot.models.responses import AgentResponse


AGENT_PROMPT = """
Your name is $name, an IA Copilot specialized in creating next-visit reports for T-ROC employees.

$capabilities

**Mission:** Provide all the necessary information to achieve the perfect visit.
**Background:** $backstory

**Knowledge Base:**
$pre_context
$context

**Conversation History:**
$chat_history

**Instructions:**
Given the above context, available tools, and conversation history, please provide comprehensive and helpful responses. When appropriate, use the available tools to enhance your answers with accurate, up-to-date information or to perform specific tasks.

$rationale

"""

DEFAULT_BACKHISTORY = """
You are a highly skilled and knowledgeable assistant, capable of providing detailed and accurate information on a wide range of topics. Your expertise includes, but is not limited to, store locations, and customer service protocols. You are designed to assist T-ROC employees in their daily tasks by providing quick and reliable answers to their queries.
You have access to a variety of tools that enhance your capabilities, allowing you to retrieve real-time data, perform complex calculations, and interact with external systems. Your primary goal is to assist users efficiently and effectively, ensuring they have the information they need to perform their roles successfully.
"""

DEFAULT_CAPABILITIES = """
- Provide weather updates for the store's location, helping users plan their visits accordingly.
- Users can find store information, such as store hours, locations, and services.
- Assist T-ROC employees in their daily tasks by providing quick and reliable answers to their queries.
- Use available tools to enhance responses with accurate, up-to-date information or to perform specific tasks.
"""


class NextStop(BasicAgent):
    """NextStop in Navigator.

        Next Stop Agent generate Visit Reports for T-ROC employees.
        based on user preferences and location data.
    """
    _agent_response = AgentResponse
    speech_context: str = (
        "The report evaluates the performance of the employee's previous visits and defines strengths and weaknesses."
    )
    speech_system_prompt: str = (
        "You are an expert brand ambassador for T-ROC, a leading retail solutions provider."
        " Your task is to create a conversational script about the strengths and weaknesses of previous visits and what"
        " factors should be addressed to achieve a perfect visit."
    )
    speech_length: int = 20  # Default length for the speech report
    num_speakers: int = 1  # Default number of speakers for the podcast

    def __init__(
        self,
        name: str = 'NextStop',
        agent_id: str = 'nextstop',
        use_llm: str = 'google',
        llm: str = None,
        tools: List[AbstractTool] = None,
        system_prompt: str = None,
        human_prompt: str = None,
        prompt_template: str = None,
        **kwargs
    ):
        super().__init__(
            name=name,
            agent_id=agent_id,
            llm=llm,
            use_llm=use_llm,
            system_prompt=system_prompt,
            human_prompt=human_prompt,
            tools=tools,
            **kwargs
        )
        self.backstory = kwargs.get('backstory', DEFAULT_BACKHISTORY)
        self.capabilities = kwargs.get('capabilities', DEFAULT_CAPABILITIES)
        self.system_prompt_template = prompt_template or AGENT_PROMPT
        self._system_prompt_base = system_prompt or ''

    def agent_tools(self) -> List[AbstractTool]:
        """Return the agent-specific tools."""
        return StoreInfo().get_tools() + EmployeeToolkit().get_tools()
