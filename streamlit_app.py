"""
A Streamlit-based chatbot application that provides multiple AI capabilities:
- General conversation and question answering
- Image generation
- Music generation (with optional lyrics)
- Research paper generation

The application uses various AI services including OpenAI for chat, ElevenLabs for text-to-speech,
Brave for web search, and Hugging Face for media generation. It provides a user-friendly interface
where users can interact with the bot and receive responses including text, images, and audio.

Required Environment Variables:
    - OPENAI_API_KEY: API key for OpenAI services
    - ELEVENLABS_API_KEY: API key for ElevenLabs text-to-speech
    - BRAVE_API_KEY: API key for Brave search

Dependencies:
    - streamlit: For the web interface
    - python-dotenv: For loading environment variables
    - Various custom modules (tts, search, llm, huggingface) for specific functionalities
"""

from dotenv import load_dotenv
load_dotenv()

from tts import text_to_speech_mixed
from search import search_brave
from llm import get_chat_completion, get_research_completion
from supabase_client import get_total_tokens, track_token_usage

import streamlit as st
import io
import os
from huggingface import generate_image, generate_music

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "Welcome to the chatbot! The assistant is able to answer any question,"
    " generate images, generate music, and write research papers!"
)

# Calculate costs from tokens
def calculate_cost(prompt_tokens, completion_tokens):
    # GPT-4o pricing: $2.5/1M prompt tokens, $10/1M completion tokens
    prompt_cost = (prompt_tokens / 1000000) * 2.5
    completion_cost = (completion_tokens / 1000000) * 10
    return prompt_cost + completion_cost

# Add usage stats in the sidebar
with st.sidebar:
    st.header("💰 Usage Stats")
    
    # Get total usage
    prompt_tokens, completion_tokens = get_total_tokens()
    total_tokens = prompt_tokens + completion_tokens
    total_cost = calculate_cost(prompt_tokens, completion_tokens)
    
    # Display stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Cost", f"${total_cost:.2f}")
        st.metric("Prompt Tokens", f"{prompt_tokens:,}")
    with col2:
        st.metric("Total Tokens", f"{total_tokens:,}")
        st.metric("Completion Tokens", f"{completion_tokens:,}")

# Get API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Please set the OPENAI_API_KEY environment variable.", icon="🚨")
elif not os.getenv("ELEVENLABS_API_KEY"):
    st.error("Please set the ELEVENLABS_API_KEY environment variable.", icon="🚨")
elif not os.getenv("BRAVE_API_KEY"):
    st.error("Please set the BRAVE_API_KEY environment variable.", icon="🚨")
else:
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
                print(f"Debug: Displaying media for message {i}")
                media = st.session_state.media[i]
                if media["type"] == "image":
                    st.image(io.BytesIO(media["data"]))
                elif media["type"] == "audio":
                    st.audio(media["data"])
                elif media["type"] == "text":
                    st.markdown(media["data"])

    # Create a chat input field to allow the user to enter a message
    if prompt := st.chat_input("How may I assist you?", disabled=st.session_state.is_processing):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.media.append(None)  # No media for user messages
        disable_input()
        st.rerun()

    if st.session_state.is_processing and len(st.session_state.messages) > 0:
        # Get the last user message
        prompt = st.session_state.messages[-1]["content"]
        
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
            
            stream = get_chat_completion(st.session_state.messages)
            
            for chunk in stream:
                # Handle usage data in the last chunk
                if hasattr(chunk, 'usage') and chunk.usage:
                    # Track token usage
                    track_token_usage(
                        chunk.usage.prompt_tokens,
                        chunk.usage.completion_tokens
                    )

                # Skip empty chunks
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    continue
                    
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
                        print(f"Debug: Executing tool call: {tool_call['name']}")
                        
                        if tool_call["name"] == "generate_image":
                            print(f"Debug: Generating image with prompt: {tool_call['arguments']['prompt']}")
                            result_bytes = generate_image(tool_call["arguments"]["prompt"])
                            
                            # Store media first
                            st.session_state.media.append({"type": "image", "data": result_bytes})
                            # Add a placeholder message for the assistant
                            st.session_state.messages.append({"role": "assistant", "content": "Here is the image you requested:"})
                            
                            enable_input()

                        elif tool_call["name"] == "generate_music":
                            print(f"Debug: Generating music with arguments: {tool_call['arguments']}")
                            result_bytes = generate_music(tool_call["arguments"]["prompt"])
                            if tool_call["arguments"]["has_lyrics"]:
                                lyrics = tool_call["arguments"]["lyrics"]
                                prev_result_bytes = result_bytes
                                try:
                                    result_bytes = text_to_speech_mixed(lyrics, result_bytes)
                                except Exception as e:
                                    st.error(f"Error generating music with lyrics: {str(e)}")
                                    result_bytes = prev_result_bytes
                            
                            # Store media first
                            st.session_state.media.append({"type": "audio", "data": result_bytes})
                            # Add a placeholder message for the assistant
                            st.session_state.messages.append({"role": "assistant", "content": "Here is the music you requested:"})
                            
                            enable_input()

                        elif tool_call["name"] == "generate_research":
                            print(f"Debug: Generating research paper")
                            # Get search results first
                            search_results = search_brave(tool_call["arguments"]["query"])
                            
                            # Exit spinner since we're about to start streaming the paper
                            if spinner:
                                spinner.__exit__(None, None, None)
                            
                            # Stream the research paper generation
                            research_stream = get_research_completion(tool_call["arguments"]["query"], search_results)
                            
                            paper_content = ""
                            for chunk in research_stream:                                    
                                # Handle usage data in the last chunk
                                if hasattr(chunk, 'usage') and chunk.usage:
                                    # Track token usage
                                    track_token_usage(
                                        chunk.usage.prompt_tokens,
                                        chunk.usage.completion_tokens
                                    )

                                # Skip empty chunks
                                if not hasattr(chunk, 'choices') or not chunk.choices:
                                    continue
                                    
                                if chunk.choices[0].delta.content:
                                    paper_content += chunk.choices[0].delta.content
                                    message_placeholder.markdown(paper_content + "▌")
                            
                            # Store the final paper as a regular assistant message
                            message_placeholder.markdown(paper_content)
                            st.session_state.messages.append({"role": "assistant", "content": paper_content})
                            st.session_state.media.append(None)  # No media needed since it's in the message
                            
                            enable_input()

                    except Exception as e:
                        st.error(f"Error executing tool call: {str(e)}")
                
                # Exit the spinner context if it was created
                if spinner:
                    spinner.__exit__(None, None, None)
                
                # Rerun after all tool calls are processed
                st.rerun()

            # Only store text response if there was actual text content
            if full_response.strip():
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.media.append(None)  # No media for text responses

            # Re-enable input after response is complete
            enable_input()
            st.rerun()
