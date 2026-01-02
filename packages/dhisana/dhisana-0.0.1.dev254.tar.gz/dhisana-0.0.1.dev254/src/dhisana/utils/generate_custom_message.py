# Import necessary modules
import html as html_lib
import re
from typing import Dict, List, Optional
from pydantic import BaseModel

from dhisana.schemas.sales import CampaignContext, ContentGenerationContext, ConversationContext, Lead, MessageGenerationInstructions, MessageItem, SenderInfo
from dhisana.utils.generate_structured_output_internal import (
    get_structured_output_internal,
    get_structured_output_with_assistant_and_vector_store
)
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# -----------------------------------------------------------------------------
# Custom Message schema
# -----------------------------------------------------------------------------
class CustomMessageCopy(BaseModel):
    subject: str
    body: str
    body_html: Optional[str] = None
 
    model_config = ConfigDict(extra="forbid")


def _html_to_plain_text(html_content: str) -> str:
    """Simple HTML to text conversion to backfill plain body."""
    if not html_content:
        return ""
    # Remove tags and normalize whitespace
    text = re.sub(r"<[^>]+>", " ", html_content)
    text = html_lib.unescape(text)
    # Collapse repeated whitespace/newlines
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join([line for line in lines if line])

# -----------------------------------------------------------------------------
# Utility to Clean Up Context (if needed)
# -----------------------------------------------------------------------------
def cleanup_message_context(message_context: ContentGenerationContext) -> ContentGenerationContext:
    """
    Return a copy of ContentGenerationContext without sensitive or irrelevant fields.
    Modify or remove fields as necessary for your project.
    """
    clone_context = message_context.copy(deep=True)
    # For demonstration, no sensitive fields in new classes by default.
    # Adjust if you want to remove certain fields (like 'sender_bio', etc.).
    if clone_context.external_known_data:
        clone_context.external_known_data.external_openai_vector_store_id = None
    return clone_context

# -----------------------------------------------------------------------------
# Known Framework Variations (fallback if user instructions are not provided)
# -----------------------------------------------------------------------------
FRAMEWORK_VARIATIONS = [
    "Write a summary of the input having key highlights.",
]

# -----------------------------------------------------------------------------
# Core function to generate a custom message copy
# -----------------------------------------------------------------------------
async def generate_custom_message_copy(
    message_context: ContentGenerationContext,
    message_instructions: MessageGenerationInstructions,
    variation_text: str,
    tool_config: Optional[List[Dict]] = None,
) -> dict:
    """
    Generate a personalized custom message using the provided context and instructions.

    Steps:
      1. Build a prompt referencing 6 main info:
          (a) Lead Info
          (b) Sender Info
          (c) Campaign Info
          (d) Messaging Instructions
          (e) Additional Data (vector store) if any
          (f) Current Conversation Context
      2. Generate an initial draft with or without vector store usage.
      3. Optionally refine if a vector store was used and user instructions were not provided.
      4. Return the final subject & body.
    """
    cleaned_context = cleanup_message_context(message_context)

    # Check if user provided custom instructions
    user_custom_instructions = (message_instructions.instructions_to_generate_message or "").strip()
    use_custom_instructions = bool(user_custom_instructions)

    # Decide final instructions: user-provided or fallback variation
    if use_custom_instructions:
        selected_instructions = user_custom_instructions
    else:
        selected_instructions = variation_text

    # Pull out fields or fallback to empty if None
    lead_data = cleaned_context.lead_info or Lead()
    sender_data = cleaned_context.sender_info or SenderInfo()
    campaign_data = cleaned_context.campaign_context or CampaignContext()
    conversation_data = cleaned_context.current_conversation_context or ConversationContext()

    html_note = (
        f"\n        Provide the HTML body using this guidance/template when possible:\n        {message_instructions.html_template}"
        if getattr(message_instructions, "html_template", None)
        else ""
    )
    
    important_requirements = """
        IMPORTANT REQUIREMENTS:
        - Output must be JSON with "subject", "body", and "body_html" fields.
        - "body_html" should be clean HTML suitable for the message (no external assets), inline styles welcome.
        - "body" must be the plain-text equivalent of "body_html".
        - Keep it concise and relevant. No placeholders or extra instructions.
        - Do not include PII or internal references, guids or content identifiers in the message.
        - Use conversational names for company/person placeholders when provided.
        - Do Not Make up information. Use the information provided in the context and instructions only.
        - Do Not use em dash in the generated output.
        - Follow the user instructions carefully regarding format, tone, and structure.
    """
    
    if not getattr(message_instructions, "allow_html", False):
        important_requirements = """
        IMPORTANT REQUIREMENTS:
        - Output must be JSON with "subject" and "body" fields only.
        - In the subject or body DO NOT include any HTML tags like <a>, <b>, <i>, etc.
        - The body and subject should be in plain text.
        - If there is a link provided use it as is. Don't wrap it in any HTML tags.
        - Keep it concise and relevant. No placeholders or extra instructions.
        - Do not include PII or internal references, guids or content identifiers in the message.
        - Use conversational name for company name if used.
        - Do Not Make up information. Use the information provided in the context and instructions only.
        - Make sure the body text is well-formatted and that newline and carriage-return characters are correctly present and preserved in the message body.
        - Do Not use em dash in the generated output.
        - Follow the user instructions carefully regarding format, tone, and structure.
    """

    # Construct the consolidated prompt
    initial_prompt = f"""
        Hi AI Assistant,

        Below is the context in 6 main sections. Use it to craft a concise, professional message:

        1) Lead Information:
        {lead_data.dict()}

        2) Sender Information:
        Full Name: {sender_data.sender_full_name or ''}
        First Name: {sender_data.sender_first_name or ''}
        Last Name: {sender_data.sender_last_name or ''}
        Bio: {sender_data.sender_bio or ''}

        3) Campaign Information:
        Product Name: {campaign_data.product_name or ''}
        Value Proposition: {campaign_data.value_prop or ''}
        Call To Action: {campaign_data.call_to_action or ''}
        Pain Points: {campaign_data.pain_points or []}
        Proof Points: {campaign_data.proof_points or []}
        Triage Guidelines (Email): {campaign_data.email_triage_guidelines or ''}
        Triage Guidelines (LinkedIn): {campaign_data.linkedin_triage_guidelines or ''}

        4) Messaging Instructions (template/framework):
        {selected_instructions}{html_note}

        5) External Data / Vector Store:
        (I will be provided with file_search tool if present.)

        6) Current Conversation Context:
        Email Thread: {conversation_data.current_email_thread or ''}
        LinkedIn Thread: {conversation_data.current_linkedin_thread or ''}

        {important_requirements}
    """

    # Check if a vector store is available
    vector_store_id = (message_context.external_known_data.external_openai_vector_store_id
                       if message_context.external_known_data else None)

    initial_response = None
    initial_status = ""

    # Generate initial draft
    if vector_store_id:
        initial_response, initial_status = await get_structured_output_with_assistant_and_vector_store(
            prompt=initial_prompt,
            response_format=CustomMessageCopy,
            vector_store_id=vector_store_id,
            model="gpt-5.1-chat",
            tool_config=tool_config,
            use_cache=message_context.message_instructions.use_cache if message_context.message_instructions else True
        )
    else:
        # Otherwise, generate the initial draft internally
        initial_response, initial_status = await get_structured_output_internal(
            prompt=initial_prompt,
            response_format=CustomMessageCopy,
            model="gpt-5.1-chat",
            tool_config=tool_config,
            use_cache=message_context.message_instructions.use_cache if message_context.message_instructions else True
        )

    if initial_status != "SUCCESS":
        raise Exception("Error: Could not generate initial draft for the custom message.")
    
    plain_body = initial_response.body
    html_body = getattr(initial_response, "body_html", None)
    if not plain_body and html_body:
        plain_body = _html_to_plain_text(html_body)

    response_item = MessageItem(
        message_id="",  # or some real ID if you have it
        thread_id="",
        sender_name=message_context.sender_info.sender_full_name or "",
        sender_email=message_context.sender_info.sender_email or "",
        receiver_name=message_context.lead_info.full_name or "",
        receiver_email=message_context.lead_info.email or "",
        iso_datetime=datetime.utcnow().isoformat(),
        subject="",
        body=plain_body,
        html_body=html_body if getattr(message_instructions, "allow_html", False) else None,
    )
    return response_item.model_dump()

# -----------------------------------------------------------------------------
# Primary function to generate multiple variations
# -----------------------------------------------------------------------------
async def generate_custom_message(
    generation_context: ContentGenerationContext,
    number_of_variations: int = 3,
    tool_config: Optional[List[Dict]] = None
) -> List[dict]:
    """
    Generates multiple custom message variations based on the given context and instructions.

    Parameters:
        - generation_context: The consolidated context for message generation.
        - number_of_variations: How many message variations to produce.
        - tool_config: Optional tool configuration for the LLM calls.

    Returns:
        A list of dictionaries, each containing:
          {
            "subject": "string",
            "body": "string"
          }
    """
    message_variations = []
    message_instructions = generation_context.message_instructions 
    user_instructions_exist = bool(
        (message_instructions.instructions_to_generate_message or "").strip()
    )

    for i in range(number_of_variations):
        try:
            # If user provided instructions, use them for each variation
            # (skip the internal frameworks).
            if user_instructions_exist:
                variation_text = message_instructions.instructions_to_generate_message or ""
            else:
                # Otherwise, pick from known frameworks (circular indexing)
                variation_text = FRAMEWORK_VARIATIONS[i % len(FRAMEWORK_VARIATIONS)]

            message_copy = await generate_custom_message_copy(
                message_context=generation_context,
                message_instructions=message_instructions,
                variation_text=variation_text,
                tool_config=tool_config
            )
            message_variations.append(message_copy)

        except Exception as e:
            raise e
    return message_variations
