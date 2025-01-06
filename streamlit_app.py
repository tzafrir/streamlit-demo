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


    # Create a session state variable to store the chat messages and media
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "media" not in st.session_state:
        st.session_state.media = []
    if "input_disabled" not in st.session_state:
        st.session_state.input_disabled = False
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

    def disable_input():
        st.session_state.is_processing = True
        st.session_state.input_disabled = True

    def enable_input():
        st.session_state.is_processing = False
        st.session_state.input_disabled = False

    # Display the existing chat messages and media via `st.chat_message`
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If there's media associated with this message, display it
            if i < len(st.session_state.media) and st.session_state.media[i]:
                media = st.session_state.media[i]
                if media["type"] == "image":
                    st.image(io.BytesIO(media["data"]))
                elif media["type"] == "audio":
                    st.audio(media["data"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("How may I assist you?", disabled=st.session_state.is_processing):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.media.append(None)  # No media for user messages
        disable_input()
        st.rerun()

    if st.session_state.is_processing and len(st.session_state.messages) > 0:
        # Get the last user message
        prompt = st.session_state.messages[-1]["content"]
            
        system_message = {
            "role": "system",
            "content": """You are a helpful assistant that is able to respond to user questions,
            generate images, generate music, and write essays.
            
            You are able to use the following tools to help you answer the user's question:
            - generate_image: Generate an image (create an expansive prompt based on the user's request, only when the user is actively asking for it in the very last message)
            - generate_music: Generate music (create an expansive prompt based on the user's request, only when the user is actively asking for it in the very last message)
            
            When asked to write an essay, write a well-structured essay with a clear thesis,
            supporting arguments, and a conclusion, on the requested topic.
            
            In ambiguous cases, ask the user for clarification.
            
            Note: The user may make many requests, for text or for media or for essays.
            Only generate media if the user is actively asking for it.
            
            For example, if the user asked for an image, received the image, then said "nice",
            there is no need to generate another image.
            """
            
        }
        
        print(f"messages: {st.session_state.messages}")

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
            message_placeholder = st.empty()
            spinner_placeholder = st.empty()
            spinner = None
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Handle tool calls
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    if not receiving_tool_calls:
                        receiving_tool_calls = True
                        # Show spinner when first detecting tool calls
                        spinner = st.spinner("Generating media, this may take a while...")
                        spinner.__enter__()
                    
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
                            print(f"Generating image with prompt: {tool_call['arguments']['prompt']}")
                            result_bytes = generate_image(tool_call["arguments"]["prompt"])
                            
                            # Store media first
                            st.session_state.media.append({"type": "image", "data": result_bytes})
                            # Add a placeholder message for the assistant
                            st.session_state.messages.append({"role": "assistant", "content": "Here is the image you requested:"})
                            
                            # No need to try displaying here since it will be shown in the message history
                            enable_input()
                            st.rerun()

                        elif tool_call["name"] == "generate_music":
                            print(f"Generating music with prompt: {tool_call['arguments']['prompt']}")
                            result_bytes = generate_music(tool_call["arguments"]["prompt"])
                            
                            # Store media first
                            st.session_state.media.append({"type": "audio", "data": result_bytes})
                            # Add a placeholder message for the assistant
                            st.session_state.messages.append({"role": "assistant", "content": "Here is the music you requested:"})
                            
                            enable_input()
                            st.rerun()

                    except Exception as e:
                        st.error(f"Error executing tool call: {str(e)}")
                
                # Exit the spinner context if it was created
                if spinner:
                    spinner.__exit__(None, None, None)
            
            # Only store text response if there was actual text content
            if full_response.strip():
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.media.append(None)  # No media for text responses

            # Re-enable input after response is complete
            enable_input()
            st.rerun()
