from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os


def init_llm(api_key):
    """Initialize the LLM with the provided API key."""
    return ChatOpenAI(model="gpt-4o-mini", api_key=api_key)


def create_prompt():
    """Create the prompt template for email generation."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are a professional email writing assistant. Convert brief bullet points into polished, professional emails.

## OUTPUT FORMAT
Subject: [Clear, specific subject line]

[Appropriate greeting],

[Opening buffer/context],

[Body: Expand notes into 2-3 concise paragraphs],

[Closing with next step or courtesy],

[Professional sign-off]

## RULES
- Transform fragments into complete sentences
- Add polite buffer language
- Maximum 150 words
- No placeholders like [Name]"""),
        ("user", "Notes: {notes}")
    ])


def generate_email_enhanced(notes, tone, recipient_name, sender_name, llm):
    """
    Generate a professional email based on the provided notes and parameters.
    
    Args:
        notes: Bullet points or brief notes for the email content
        tone: The tone style for the email
        recipient_name: Name of the recipient (optional)
        sender_name: Name of the sender (optional)
        llm: Initialized ChatOpenAI instance
    
    Returns:
        Generated email content as string
    """
    try:
        prompt = create_prompt()
        chain = prompt | llm
        
        # Build enhanced prompt
        enhanced_prompt = f"""Notes: {notes}

TONE: Write in a {tone} tone.
RECIPIENT: {recipient_name if recipient_name else "Use appropriate greeting without specific name"}
SENDER: Sign off as {sender_name if sender_name else "use generic professional sign-off"}"""
        
        response = chain.invoke({"notes": enhanced_prompt})
        return response.content
    except Exception as e:
        return f"Error generating email: {str(e)}"