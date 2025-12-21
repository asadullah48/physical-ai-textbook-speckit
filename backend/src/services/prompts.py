"""Prompt templates for educational Q&A with RAG context."""

from typing import Optional


RAG_SYSTEM_PROMPT = """You are an AI teaching assistant for a Physical AI & Humanoid Robotics textbook.

Your role is to help students understand concepts from the textbook content. You should:
1. Provide clear, educational explanations suitable for university students
2. Reference specific chapters and sections when citing information
3. Use examples from the textbook when available
4. Acknowledge when a topic is not covered in the provided context

Guidelines:
- Be concise but thorough
- Use technical terminology appropriately with explanations
- Encourage deeper learning by suggesting related topics in the textbook
- If the question is unclear, ask for clarification"""


RAG_CONTEXT_TEMPLATE = """## Retrieved Context from Textbook

{context}

---

Based on the above context from the Physical AI textbook, answer the following question.
If the information is not in the context, clearly state that the topic is not covered in the available materials."""


SELECTION_CONTEXT_TEMPLATE = """## Selected Text

The student has highlighted the following text and is asking about it:

> {selected_text}

From: {chapter_reference}

---

Please explain or answer questions about this specific selection."""


def build_rag_prompt(
    query: str,
    context_chunks: list[dict],
    selected_text: Optional[str] = None,
    chapter_id: Optional[str] = None,
) -> list[dict]:
    """Build a complete RAG prompt for the Gemini model.

    Args:
        query: The user's question.
        context_chunks: List of retrieved context chunks with text, module_id, chapter_id, section_title.
        selected_text: Optional text the user selected for context.
        chapter_id: Optional chapter reference for selected text.

    Returns:
        List of message dictionaries for the Gemini chat API.
    """
    messages = []

    # System message
    messages.append({
        "role": "user",
        "parts": [RAG_SYSTEM_PROMPT],
    })
    messages.append({
        "role": "model",
        "parts": ["I understand. I'm ready to help students learn about Physical AI and Humanoid Robotics based on the textbook content you provide."],
    })

    # Build context section
    context_parts = []

    # Add retrieved chunks
    if context_chunks:
        context_text = ""
        for i, chunk in enumerate(context_chunks, 1):
            source = f"[{chunk.get('module_id', 'Unknown')} / {chunk.get('chapter_id', 'Unknown')} / {chunk.get('section_title', 'Section')}]"
            context_text += f"\n### Source {i}: {source}\n\n{chunk.get('text', '')}\n"

        context_parts.append(RAG_CONTEXT_TEMPLATE.format(context=context_text))

    # Add selection context if provided
    if selected_text:
        chapter_ref = chapter_id if chapter_id else "Selected content"
        context_parts.append(
            SELECTION_CONTEXT_TEMPLATE.format(
                selected_text=selected_text,
                chapter_reference=chapter_ref,
            )
        )

    # Combine context and question
    user_content = "\n\n".join(context_parts) if context_parts else ""
    user_content += f"\n\n## Question\n\n{query}"

    messages.append({
        "role": "user",
        "parts": [user_content],
    })

    return messages


def build_followup_prompt(
    query: str,
    chat_history: list[dict],
    context_chunks: Optional[list[dict]] = None,
) -> list[dict]:
    """Build a follow-up prompt with chat history.

    Args:
        query: The user's follow-up question.
        chat_history: Previous messages in the conversation.
        context_chunks: Optional new context for the follow-up.

    Returns:
        List of message dictionaries for the Gemini chat API.
    """
    messages = []

    # System message
    messages.append({
        "role": "user",
        "parts": [RAG_SYSTEM_PROMPT],
    })
    messages.append({
        "role": "model",
        "parts": ["I understand. I'm ready to continue helping with questions about Physical AI and Humanoid Robotics."],
    })

    # Add chat history
    for msg in chat_history:
        role = "user" if msg.get("role") == "user" else "model"
        messages.append({
            "role": role,
            "parts": [msg.get("content", "")],
        })

    # Build new query with optional context
    user_content = ""
    if context_chunks:
        context_text = ""
        for i, chunk in enumerate(context_chunks, 1):
            source = f"[{chunk.get('module_id', 'Unknown')} / {chunk.get('chapter_id', 'Unknown')}]"
            context_text += f"\n### Additional Context {i}: {source}\n\n{chunk.get('text', '')}\n"

        user_content = f"## Additional Context\n\n{context_text}\n\n---\n\n"

    user_content += f"## Follow-up Question\n\n{query}"

    messages.append({
        "role": "user",
        "parts": [user_content],
    })

    return messages


NO_CONTEXT_RESPONSE = """I don't have specific information about that topic in my current context from the Physical AI textbook.

This could mean:
1. The topic isn't covered in the textbook chapters I have access to
2. The question might need to be rephrased to match the textbook content
3. You might want to browse the relevant module directly

Would you like me to suggest related topics from the textbook that I can help with?"""
