from dotenv import load_dotenv

from tts import text_to_speech_mixed
from search import search_brave
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
    " generate images, generate music, and write research papers!"
)

# Get API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Please set the OPENAI_API_KEY environment variable.", icon="🚨")
elif not os.getenv("ELEVENLABS_API_KEY"):
    st.error("Please set the ELEVENLABS_API_KEY environment variable.", icon="🚨")
elif not os.getenv("BRAVE_API_KEY"):
    st.error("Please set the BRAVE_API_KEY environment variable.", icon="🚨")
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
    # print(f"Debug: Number of messages: {len(st.session_state.messages)}")
    # print(f"Debug: Number of media items: {len(st.session_state.media)}")
    for i, message in enumerate(st.session_state.messages):
        # print(f"Debug: Processing message {i}")
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
            
        def generate_research(query):
            # Get search results from Brave
            search_results = search_brave(query)
            
            # Create research prompt with RAG context
            system_message = f"""You are a professional research paper writer. Your task is to write a well-structured, 
            academic research paper based on the following web search results:

            <rag context>
            {search_results}
            </rag context>

            Write a clear, concise, and professional research paper that:
            1. Has a clear thesis statement and research objective
            2. Synthesizes information from the search results
            3. Includes proper citations and references to sources
            4. Is organized with clear sections (Introduction, Methods, Results, Discussion)
            5. Maintains an academic tone while being accessible to readers
            6. Concludes with key findings and implications

            Format the paper in markdown with proper headings and sections."""

            # Generate research paper using OpenAI
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Write a research paper about: {query}"}
                ]
            )
            
            return response.choices[0].message.content

        system_message = {
            "role": "system",
            "content": """You are a helpful assistant that is able to respond to user questions,
            generate images, generate music, and write research papers.
            
            You are able to use the following tools to help you answer the user's question:
            - generate_image: Generate an image (create an expansive prompt based on the user's request)
            - generate_music: Generate music (create an expansive prompt based on the user's request)
            - generate_research: Generate a research paper (uses web search data to create an academic paper)
            
            When asked to write a research paper:
            1. Use the generate_research function to create a well-researched academic paper
            2. The paper will be based on web search results and formatted in markdown
            3. The paper will include proper citations and maintain academic standards
            
            Music can be generated with or without lyrics. If the user is requesting for background music,
            then the music should be generated without lyrics. If the user is requesting for a song,
            then the music should be generated with lyrics. Use your best judgement to determine if the user is asking for a song or background music,
            and ask the user for clarification if you are not sure.
            
            When the user asks you to create a song, it should be generated as music unless the user
            explicitly asks for written lyrics or text output.
            
            When writing lyrics, write only words that should be pronounced out loud, and never write titles such as "chorus" or "verse".
            It is forbidden to write "Chorus" as part of the lyrics.

            
            In ambiguous cases, ask the user for clarification.
            
            Note: The user may make many requests, for text or for media or for research paper.
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
                                    "description": "The description of the music backing track to generate"
                                },
                                "has_lyrics": {
                                    "type": "boolean",
                                    "description": "Whether the music has lyrics"
                                },
                                "lyrics": {
                                    "type": "string",
                                    "description": "The pure lyrics of the song, without titles such as 'verse' or 'chorus' (empty string if no lyrics are requested)"
                                }
                            },
                            "required": ["prompt", "has_lyrics", "lyrics"]
                        }
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_research",
                        "description": "Generate a research paper based on web search data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The research topic or question to investigate"
                                }
                            },
                            "required": ["query"]
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
                        print(f"Debug: Executing tool call: {tool_call['name']}")
                        print(f"Debug: Current messages length: {len(st.session_state.messages)}")
                        print(f"Debug: Current media length: {len(st.session_state.media)}")
                        
                        if tool_call["name"] == "generate_image":
                            print(f"Debug: Generating image with prompt: {tool_call['arguments']['prompt']}")
                            result_bytes = generate_image(tool_call["arguments"]["prompt"])
                            
                            print("Debug: Before appending new image")
                            print(f"Debug: Messages length: {len(st.session_state.messages)}")
                            print(f"Debug: Media length: {len(st.session_state.media)}")
                            
                            # Store media first
                            st.session_state.media.append({"type": "image", "data": result_bytes})
                            # Add a placeholder message for the assistant
                            st.session_state.messages.append({"role": "assistant", "content": "Here is the image you requested:"})
                            
                            print("Debug: After appending new image")
                            print(f"Debug: Messages length: {len(st.session_state.messages)}")
                            print(f"Debug: Media length: {len(st.session_state.media)}")
                            
                            enable_input()

                        elif tool_call["name"] == "generate_music":
                            print(f"Debug: Generating music")
                            result_bytes = generate_music(tool_call["arguments"]["prompt"])
                            if tool_call["arguments"]["has_lyrics"]:
                                lyrics = tool_call["arguments"]["lyrics"]
                                prev_result_bytes = result_bytes
                                try:
                                    result_bytes = text_to_speech_mixed(lyrics, result_bytes)
                                except Exception as e:
                                    st.error(f"Error generating music with lyrics: {str(e)}")
                                    result_bytes = prev_result_bytes
                            
                            print("Debug: Before appending new audio")
                            print(f"Debug: Messages length: {len(st.session_state.messages)}")
                            print(f"Debug: Media length: {len(st.session_state.media)}")
                            
                            # Store media first
                            st.session_state.media.append({"type": "audio", "data": result_bytes})
                            # Add a placeholder message for the assistant
                            st.session_state.messages.append({"role": "assistant", "content": "Here is the music you requested:"})
                            
                            print("Debug: After appending new audio")
                            print(f"Debug: Messages length: {len(st.session_state.messages)}")
                            print(f"Debug: Media length: {len(st.session_state.media)}")
                            
                            enable_input()

                        elif tool_call["name"] == "generate_research":
                            print(f"Debug: Generating research paper")
                            # Get search results first
                            search_results = search_brave(tool_call["arguments"]["query"])
                            
                            # Create research prompt with RAG context
                            research_system_message = f"""You are a professional research paper writer. Your task is to write a well-structured, 
                            academic research paper based on the following web search results:

                            <rag context>
                            {search_results}
                            </rag context>

                            Write a clear, concise, and professional research paper that:
                            1. Has a clear thesis statement and research objective
                            2. Synthesizes information from the search results
                            3. Includes proper citations and references to sources
                            4. Is organized with clear sections (Introduction, Methods, Results, Discussion)
                            5. Maintains an academic tone while being accessible to readers
                            6. Concludes with key findings and implications

                            Format the paper in markdown with proper headings and sections."""

                            # Exit spinner since we're about to start streaming the paper
                            if spinner:
                                spinner.__exit__(None, None, None)
                            
                            # Stream the research paper generation
                            research_stream = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": research_system_message},
                                    {"role": "user", "content": f"Write a research paper about: {tool_call['arguments']['query']}"}
                                ],
                                stream=True
                            )
                            
                            paper_content = ""
                            for chunk in research_stream:
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
