from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool



def create_tools(service, calendar_id):
    """Create tools for the agent"""
    
    @tool
    def check_availability(start_time: str, end_time: str) -> list:
        """Check available time slots between given start and end times. 
        Input MUST be in RFC3339 format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM). 
        Example: '2025-07-07T10:00:00Z'"""
        from utils import check_availability as check_avail
        return check_avail(service, calendar_id, start_time, end_time)
    
    @tool
    def book_appointment(summary: str, start_time: str, end_time: str) -> str:
        """Book an appointment with event title and time slot. 
        Input MUST be in RFC3339 format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM). 
        Example: '2025-07-07T10:00:00Z'"""
        from utils import book_appointment as book_appt
        result = book_appt(service, calendar_id, summary, start_time, end_time)
        return str(result) if result is not None else "No result"
    
    return [check_availability, book_appointment]

def create_booking_agent(tools):
    """Create the booking agent executor"""
    prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You're an intelligent appointment booking assistant for TailorTalk. "
        "Help users schedule appointments on Google Calendar. "
        "CONTEXT: You're in the middle of a conversation with the user. "
        "Follow these steps:\n"
        "1. Review the conversation history to maintain context.\n"
        "2. Understand the current request in context and gather necessary details (date, time, duration, and title).\n"
        "3. If booking details were previously discussed, use them to avoid redundancy.\n"
        "4. Only ask for missing information to streamline the process.\n"
        "5. Check availability for the requested time slot using tools.\n"
        "6. Suggest available time slots if the requested time is not available.\n"
        "7. When all details are available, confirm with the user before booking:\n"
        "   - Example: 'I have the following details: Meeting on YYYY-MM-DD from HH:MM to HH:MM, titled 'Meeting Title'. Shall I proceed with booking?'\n"
        "8. Book the appointment when confirmed and provide a success message:\n"
        "   - Example: 'Your meeting titled 'Meeting Title' has been successfully booked for YYYY-MM-DD from HH:MM to HH:MM.'\n"
        "9. If booking fails, provide a clear error message and offer to retry or choose a different time.\n"
        "CRITICAL: Always use RFC3339 format for dates (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM).\n"
        "   - Example: '2025-07-07T10:00:00Z' or '2025-07-07T10:00:00+05:30'.\n"
        "IMPORTANT: Maintain context between messages. If the user says 'yes' to a previous proposal, book that exact appointment."
    )),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])


    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8
    )