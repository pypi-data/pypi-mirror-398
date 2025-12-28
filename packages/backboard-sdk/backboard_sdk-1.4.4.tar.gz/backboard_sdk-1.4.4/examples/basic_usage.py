#!/usr/bin/env python3
"""
Backboard SDK Basic Usage Example

This example demonstrates the core functionality of the Backboard Python SDK:
- Creating assistants
- Creating threads
- Sending messages
- Uploading documents
- Handling responses

Make sure to set your API key as an environment variable:
export BACKBOARD_API_KEY="your_api_key_here"
"""

import os
import time
from pathlib import Path
import asyncio
from backboard import BackboardClient, ToolDefinition, FunctionDefinition, ToolParameters, ToolParameterProperties

async def main():
    # Get API key from environment
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        print("Please set BACKBOARD_API_KEY environment variable")
        return

    # Initialize client
    print("🚀 Initializing Backboard client...")
    client = BackboardClient(api_key=api_key)

    try:
        # Example 1: Create a simple assistant
        print("\n📝 Creating a simple assistant...")
        assistant = await client.create_assistant(
            name="Documentation Helper",
            description="An AI assistant that helps with documentation and answers questions about uploaded files"
        )
        print(f"✅ Created assistant: {assistant.name} (ID: {assistant.assistant_id})")

        # Example 2: Create an assistant with tools
        print("\n🔧 Creating an assistant with tools...")
        
        # Define a simple tool
        weather_tool = ToolDefinition(
            type="function",
            function=FunctionDefinition(
                name="get_weather",
                description="Get current weather for a location",
                parameters=ToolParameters(
                    type="object",
                    properties={
                        "location": ToolParameterProperties(
                            type="string",
                            description="The city and state, e.g. San Francisco, CA"
                        ),
                        "unit": ToolParameterProperties(
                            type="string",
                            enum=["celsius", "fahrenheit"],
                            description="Temperature unit"
                        )
                    },
                    required=["location"]
                )
            )
        )
        
        tool_assistant = await client.create_assistant(
            name="Weather Assistant",
            description="An AI assistant that can check weather information",
            tools=[weather_tool]
        )
        print(f"✅ Created tool-enabled assistant: {tool_assistant.name}")

        # Example 3: List assistants
        print("\n📋 Listing all assistants...")
        assistants = await client.list_assistants()
        for asst in assistants:
            print(f"  - {asst.name} (ID: {asst.assistant_id})")

        # Example 4: Create a thread
        print(f"\n💬 Creating a thread for assistant '{assistant.name}'...")
        thread = await client.create_thread(assistant.assistant_id)
        print(f"✅ Created thread: {thread.thread_id}")

        # Example 5: Send a simple message
        print("\n📤 Sending a message...")
        response = await client.add_message(
            thread_id=thread.thread_id,
            content="Hello! Can you tell me what you can help me with?"
        )
        print(f"✅ Message sent. Response: {response.latest_message.content[:100]}...")

        # Example 6: Upload a document (create a sample file first)
        print("\n📄 Creating and uploading a sample document...")
        sample_file = Path("sample_document.txt")
        sample_content = """
# Sample Documentation

## Overview
This is a sample document for testing the Backboard SDK.

## Features
- Document processing
- AI-powered conversations
- Persistent memory

## Getting Started
1. Install the SDK
2. Get your API key
3. Start building!
"""
        sample_file.write_text(sample_content)
        
        try:
            document = await client.upload_document_to_assistant(
                assistant_id=assistant.assistant_id,
                file_path=sample_file
            )
            print(f"✅ Uploaded document: {document.filename} (Status: {document.status.value})")
            
            # Wait for document processing
            print("⏳ Waiting for document to be processed...")
            max_wait = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                doc_status = await client.get_document_status(document.document_id)
                print(f"   Document status: {doc_status.status.value}")
                
                if doc_status.status.value == "indexed":
                    print("✅ Document successfully indexed!")
                    break
                elif doc_status.status.value == "failed":
                    print("❌ Document processing failed")
                    break
                    
                time.sleep(2)
            
            # Example 7: Ask a question about the document
            print("\n❓ Asking a question about the uploaded document...")
            doc_response = await client.add_message(
                thread_id=thread.thread_id,
                content="What features are mentioned in the uploaded document?"
            )
            print(f"✅ Response: {doc_response.latest_message.content}")
            
        finally:
            # Clean up sample file
            if sample_file.exists():
                sample_file.unlink()

        # Example 8: Streaming messages
        print("\n🌊 Sending a streaming message...")
        print("Response: ", end="")
        async for chunk in await client.add_message(
            thread_id=thread.thread_id,
            content="Can you explain what an AI assistant is in simple terms?",
            stream=True
        ):
            if chunk.get('type') == 'message_delta':
                content = chunk.get('content', '')
                print(content, end='', flush=True)
        print()  # New line after streaming

        # Example 9: Get thread with all messages
        print("\n📖 Retrieving full thread history...")
        full_thread = await client.get_thread(thread.thread_id)
        print(f"✅ Thread has {len(full_thread.messages)} messages")
        
        for i, message in enumerate(full_thread.messages, 1):
            role = message.role.value.upper()
            content = message.content[:50] + "..." if len(message.content) > 50 else message.content
            print(f"  {i}. [{role}] {content}")

        # Example 10: List documents
        print("\n📚 Listing assistant documents...")
        documents = await client.list_assistant_documents(assistant.assistant_id)
        for doc in documents:
            print(f"  - {doc.filename} (Status: {doc.status.value})")

        print("\n🎉 All examples completed successfully!")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await client.delete_thread(thread.thread_id)
        await client.delete_assistant(assistant.assistant_id)
        await client.delete_assistant(tool_assistant.assistant_id)
        print("✅ Cleanup completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
