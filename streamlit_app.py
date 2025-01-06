from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import io
from openai import OpenAI
import os
from huggingface import generate_image, generate_music

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "Welcome to the chatbot! The assistant is able to answer any question,"
    " generate images, generate music, and write essays!"
)

# Get API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Please set the OPENAI_API_KEY environment variable.", icon="🚨")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)


    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        system_message = {
            "role": "system",
            "content": """You are a helpful assistant that is able to respond to user questions,
            generate images, generate music, and write essays.
            
            You are able to use the following tools to help you answer the user's question:
            - generate_image: Generate an image (create an expansive prompt based on the user's request)
            - generate_music: Generate music (create an expansive prompt based on the user's request)
            
            When asked to write an essay, write a well-structured essay with a clear thesis,
            supporting arguments, and a conclusion, on the requested topic.
            
            In ambiguous cases, ask the user for clarification.
            """
            
        }

        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[system_message] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "generate_image",
                        "description": "Generate an image",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The description of the image to generate"
                                }
                            },
                            "required": ["prompt"]
                        }
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_music",
                        "description": "Generate music",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The description of the music to generate"
                                }
                            },
                            "required": ["prompt"]
                        }
                    },
                },
            ],
            stream=True,
        )
        
        # Stream the response to the chat and handle function calls
        full_response = ""
        accumulated_tool_calls = []
        current_tool_call = None
        current_tool_args = ""
        receiving_tool_calls = False
        
        with st.chat_message("assistant"):
            with st.spinner("    Generating, this may take a while..."):
                message_placeholder = st.empty()
                
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    
                    # Handle tool calls
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        if not receiving_tool_calls:
                            receiving_tool_calls = True
                        
                        tool_call = delta.tool_calls[0]
                        
                        # Start of new tool call
                        if tool_call.index is not None and current_tool_call is None:
                            current_tool_call = {
                                "name": tool_call.function.name,
                                "arguments": ""
                            }
                        
                        # Accumulate tool call arguments
                        if tool_call.function and tool_call.function.arguments:
                            current_tool_args += tool_call.function.arguments
                            
                        # If we have a complete tool call, add it to accumulated calls
                        if current_tool_call and current_tool_args:
                            try:
                                import json
                                args = json.loads(current_tool_args)
                                accumulated_tool_calls.append({
                                    "name": current_tool_call["name"],
                                    "arguments": args
                                })
                                current_tool_call = None
                                current_tool_args = ""
                            except json.JSONDecodeError:
                                # Continue accumulating if JSON is incomplete
                                pass
                    
                    # Handle regular content
                    if delta.content:
                        full_response += delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                # After streaming loop, execute accumulated tool calls
                if accumulated_tool_calls:
                    for tool_call in accumulated_tool_calls:
                        try:
                            if tool_call["name"] == "generate_image":
                                result_bytes = generate_image(tool_call["arguments"]["prompt"])
                                print(result_bytes[0:200])
                                message_placeholder.image(io.BytesIO(result_bytes))
                            elif tool_call["name"] == "generate_music":
                                result_bytes = generate_music(tool_call["arguments"]["prompt"])
                                message_placeholder.audio(result_bytes)
                        except Exception as e:
                            st.error(f"Error executing tool call: {str(e)}")
                
                # Display final message without cursor
                if full_response:
                    message_placeholder.markdown(full_response)
            
            # Store the complete response in session state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
