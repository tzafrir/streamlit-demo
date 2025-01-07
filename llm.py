"""
Language Model Integration Module

This module provides integration with OpenAI's GPT-4 model for various AI tasks including:
- General conversation
- Image generation prompting
- Music generation prompting
- Research paper generation

The module defines system prompts and tools for specialized tasks, and provides
functions to interact with the OpenAI API in a structured way.

Required Environment Variables:
    - OPENAI_API_KEY: API key for accessing OpenAI's API services

Dependencies:
    - openai: For interacting with OpenAI's API
"""

from openai import OpenAI
import os

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompts
ASSISTANT_SYSTEM_PROMPT = """You are a helpful assistant that is able to respond to user questions,
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

RESEARCH_SYSTEM_PROMPT = """You are a professional research paper writer. Your task is to write a well-structured, 
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

# Tool definitions
TOOLS = [
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
]

def get_chat_completion(messages, stream=True):
    """
    Get a chat completion from OpenAI's GPT-4o model with tool calling capabilities.
    
    Args:
        messages (list): List of message dictionaries containing role and content
        stream (bool, optional): Whether to stream the response. Defaults to True
        
    Returns:
        openai.Stream or openai.ChatCompletion: The model's response, either as a
        stream or complete response depending on the stream parameter
        
    Note:
        The function includes specialized tools for generating images, music,
        and research papers through function calling.
    """
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": ASSISTANT_SYSTEM_PROMPT}] + messages,
        tools=TOOLS,
        stream=stream,
        stream_options={"include_usage": True}
    )

def get_research_completion(query, search_results, stream=True):
    """
    Generate a research paper using GPT-4o based on a query and search results.
    
    Args:
        query (str): The research topic or question to investigate
        search_results (str): Web search results to use as context
        stream (bool, optional): Whether to stream the response. Defaults to True
        
    Returns:
        openai.Stream or openai.ChatCompletion: The generated research paper,
        either as a stream or complete response
        
    Note:
        The generated paper follows academic standards with proper sections,
        citations, and formatting in markdown.
    """
    system_message = RESEARCH_SYSTEM_PROMPT.format(search_results=search_results)
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Write a research paper about: {query}"}
        ],
        stream=stream,
        stream_options={"include_usage": True}
    ) 