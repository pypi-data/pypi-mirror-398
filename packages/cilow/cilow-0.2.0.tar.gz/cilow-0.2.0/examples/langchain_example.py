"""
LangChain Integration Examples for Cilow

This file demonstrates how to use Cilow as a memory backend for LangChain.
Cilow provides 26ms semantic search with automatic entity extraction.

Prerequisites:
    pip install cilow[langchain] langchain-openai

Make sure Cilow server is running:
    cargo run --bin cilow-api
"""

import os
from typing import Optional


def example_chat_message_history():
    """
    Example 1: Using CilowChatMessageHistory

    This stores every message in Cilow, tagged by session and role.
    Good for simple chat applications where you want full history.
    """
    from langchain_core.messages import HumanMessage, AIMessage
    from cilow.integrations.langchain import CilowChatMessageHistory

    # Create history for a specific session
    history = CilowChatMessageHistory(
        session_id="example-session-1",
        user_id="user-123",
        base_url="http://localhost:8080",
        # api_key="cilow_xxx"  # Or use JWT token
    )

    # Add messages
    history.add_user_message("What is Python?")
    history.add_ai_message(
        "Python is a high-level programming language known for its "
        "readability and versatility. It's widely used for web development, "
        "data science, AI, and automation."
    )

    history.add_user_message("What are its main features?")
    history.add_ai_message(
        "Key features include: dynamic typing, garbage collection, "
        "extensive standard library, and support for multiple paradigms "
        "(OOP, functional, procedural)."
    )

    # Retrieve all messages
    messages = history.messages
    print(f"Retrieved {len(messages)} messages from Cilow")
    for msg in messages:
        print(f"  {msg.__class__.__name__}: {msg.content[:50]}...")

    return history


def example_semantic_memory():
    """
    Example 2: Using CilowSemanticMemory

    This provides intelligent context retrieval based on semantic similarity.
    Instead of returning all messages, it returns the most relevant ones
    based on the current input.
    """
    from cilow.integrations.langchain import CilowSemanticMemory

    memory = CilowSemanticMemory(
        user_id="user-123",
        base_url="http://localhost:8080",
        memory_key="relevant_context",
        input_key="input",
        top_k=5,  # Return top 5 most relevant memories
        min_relevance=0.3,  # Minimum relevance score
    )

    # Simulate saving some context
    memory.save_context(
        inputs={"input": "I prefer using TypeScript over JavaScript"},
        outputs={"output": "Got it! TypeScript provides static typing benefits."},
    )

    memory.save_context(
        inputs={"input": "My favorite database is PostgreSQL"},
        outputs={"output": "PostgreSQL is excellent for complex queries."},
    )

    memory.save_context(
        inputs={"input": "I'm working on a React project"},
        outputs={"output": "React is great for building user interfaces."},
    )

    # Now query for relevant context
    context = memory.load_memory_variables(
        {"input": "What programming language should I use?"}
    )
    print("\nRelevant context for language question:")
    print(context["relevant_context"])

    context = memory.load_memory_variables(
        {"input": "Which database do you recommend?"}
    )
    print("\nRelevant context for database question:")
    print(context["relevant_context"])

    return memory


def example_conversation_memory():
    """
    Example 3: Using CilowConversationMemory

    This combines recent history with semantic search - perfect for
    conversations that need both immediate context and long-term recall.
    """
    from cilow.integrations.langchain import CilowConversationMemory

    memory = CilowConversationMemory(
        session_id="project-planning-session",
        user_id="user-123",
        base_url="http://localhost:8080",
        recent_k=3,  # Last 3 messages always included
        semantic_k=2,  # Plus 2 semantically relevant older memories
    )

    # Simulate a long conversation
    conversations = [
        ("Let's plan a new web application", "Great! What kind of app?"),
        ("An e-commerce platform", "E-commerce has many components to consider."),
        ("We need user authentication", "I'll note that authentication is required."),
        ("Product catalog is important", "Product catalog with search, got it."),
        ("Shopping cart functionality", "Shopping cart with persistence."),
        ("Now let's discuss the tech stack", "Sure, what are you considering?"),
    ]

    for user_msg, ai_msg in conversations:
        memory.save_context(
            inputs={"input": user_msg},
            outputs={"output": ai_msg},
        )

    # Query combines recent + relevant
    context = memory.load_memory_variables(
        {"input": "What authentication approach should we use?"}
    )
    print("\nCombined context (recent + semantic):")
    print(context["history"])

    return memory


def example_with_langchain_chain():
    """
    Example 4: Full LangChain Integration with ConversationChain

    This shows how to use Cilow memory in a real LangChain conversation chain.
    Requires: pip install langchain-openai
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain.chains import ConversationChain
    except ImportError:
        print("Install langchain-openai for this example: pip install langchain-openai")
        return None

    from cilow.integrations.langchain import CilowSemanticMemory

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable for this example")
        return None

    # Create semantic memory
    memory = CilowSemanticMemory(
        user_id="demo-user",
        session_id="demo-session",
        base_url="http://localhost:8080",
        top_k=5,
    )

    # Create the chain
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = ConversationChain(llm=llm, memory=memory, verbose=True)

    # Have a conversation
    responses = []

    response = chain.invoke({"input": "My name is Alex and I love Python programming."})
    responses.append(response)
    print(f"\nResponse 1: {response['response'][:100]}...")

    response = chain.invoke({"input": "I'm working on a machine learning project."})
    responses.append(response)
    print(f"\nResponse 2: {response['response'][:100]}...")

    response = chain.invoke({"input": "What do you know about me?"})
    responses.append(response)
    print(f"\nResponse 3: {response['response'][:100]}...")

    return responses


def example_async_usage():
    """
    Example 5: Async Usage for Better Performance

    For high-throughput applications, use the async methods directly.
    """
    import asyncio
    from cilow.integrations.langchain import CilowChatMessageHistory
    from langchain_core.messages import HumanMessage, AIMessage

    async def main():
        history = CilowChatMessageHistory(
            session_id="async-session",
            user_id="user-123",
            base_url="http://localhost:8080",
        )

        # Use async methods
        await history.aadd_message(HumanMessage(content="Async message 1"))
        await history.aadd_message(AIMessage(content="Async response 1"))

        messages = await history.aget_messages()
        print(f"\nAsync: Retrieved {len(messages)} messages")

        await history.aclear()
        print("Async: Cleared history")

    asyncio.run(main())


if __name__ == "__main__":
    print("=" * 60)
    print("Cilow LangChain Integration Examples")
    print("=" * 60)

    print("\n--- Example 1: Chat Message History ---")
    try:
        example_chat_message_history()
    except Exception as e:
        print(f"Error (is Cilow server running?): {e}")

    print("\n--- Example 2: Semantic Memory ---")
    try:
        example_semantic_memory()
    except Exception as e:
        print(f"Error (is Cilow server running?): {e}")

    print("\n--- Example 3: Conversation Memory ---")
    try:
        example_conversation_memory()
    except Exception as e:
        print(f"Error (is Cilow server running?): {e}")

    print("\n--- Example 4: Full Chain (requires OpenAI) ---")
    try:
        example_with_langchain_chain()
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Example 5: Async Usage ---")
    try:
        example_async_usage()
    except Exception as e:
        print(f"Error (is Cilow server running?): {e}")

    print("\n" + "=" * 60)
    print("Examples complete!")
