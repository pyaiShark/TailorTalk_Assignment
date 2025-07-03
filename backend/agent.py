from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from datetime import datetime, timedelta
import re

def create_tools(service, calendar_id):
    """Create tools for the agent with enhanced error handling"""
    
    @tool
    def check_availability(start_time: str, end_time: str) -> list:
        """Check available time slots between given start and end times. 
        Input MUST be in RFC3339 format (YYYY-MM-DDTHH:MM:SSZ). 
        Example: '2025-07-07T10:00:00Z'"""
        from utils import check_availability as check_avail
        try:
            return check_avail(service, calendar_id, start_time, end_time)
        except Exception as e:
            return f"Availability check failed: {str(e)}"
    
    @tool
    def book_appointment(summary: str, start_time: str, end_time: str) -> str:
        """Book an appointment with event title and time slot. 
        Input MUST be in RFC3339 format (YYYY-MM-DDTHH:MM:SSZ). 
        Example: '2025-07-07T10:00:00Z'"""
        from utils import book_appointment as book_appt
        try:
            result = book_appt(service, calendar_id, summary, start_time, end_time)
            return "Booking successful!" if result else "Booking failed"
        except Exception as e:
            return f"Booking error: {str(e)}"
    
    return [check_availability, book_appointment]

def create_booking_agent(tools):
    """Create the booking agent executor with enhanced date handling"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You're TailorTalk's appointment assistant. Core mission: Book meetings seamlessly with minimal friction. "
            "CRITICAL RULES:\n"
            "1. DATE HANDLING\n"
            "   • Convert ALL dates to RFC3339 format BEFORE tool use (YYYY-MM-DDTHH:MM:SSZ)\n"
            "   • For partial dates ('3 Jul'):\n"
            "       - Use 2025 as default year\n"
            "       - Format as '2025-07-03'\n"
            "   • When checking availability:\n"
            "       start_time = DATE + 'T00:00:00Z'\n"
            "       end_time = DATE + 'T23:59:59Z'\n"
            "2. AVAILABILITY WORKFLOW\n"
            "   • When user requests slots for a date:\n"
            "       a. Convert to RFC3339 day range (00:00-23:59)\n"
            "       b. Use check_availability tool\n"
            "   • If no slots:\n"
            "       a. AUTOMATICALLY check next 3 days\n"
            "       b. Present alternatives if available\n"
            "3. TOOL CALL PRECISION\n"
            "   • ALWAYS use UTC timestamps (end with 'Z')\n"
            "   • Example: '2025-07-04T00:00:00Z'\n"
            "4. RESPONSE FORMAT\n"
            "   • Available slots: List in 12-hour format\n"
            "   • No slots: Show alternatives immediately\n"
            "5. CONTEXT TRACKING\n"
            "   • Remember previously checked dates\n"
            "   • Never recheck failed dates\n"
            "6. BOOKING CONFIRMATION\n"
            "   • Use exact format: 'Book [Title] on [Month] [Day] at [Time]?'"
        )),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad")
    ])

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        convert_system_message_to_human=True
    )
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
        early_stopping_method="generate"
    )
