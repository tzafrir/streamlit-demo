# Chatbot Demo

This is a demo of a chatbot that supports:
* Assisting with general questions
* Generating images
* Generating audio
* Generating a research paper

### Third party services

* [OpenAI](https://openai.com) - for text generation
* [Hugging Face](https://huggingface.co) - for image and music generation
* [ElevenLabs](https://elevenlabs.io) - for text-to-speech generation
* [Brave](https://brave.com/search/api/) - for web search
* [Supabase](https://supabase.com) - for storing and querying usage data

### Cost Tracking

* OpenAI Costs are tracked in the `openai_costs` table on supabase
* All other APIs are on a free tier and are not tracked - TODO


## Prerequisites

1. Install ffmpeg:
   - Windows: Download from [ffmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

2. Set up Supabase:
   - Create an account at [Supabase](https://supabase.com)
   - Create a new project
   - Go to SQL Editor
   - Copy and paste the contents of `create_table.sql` and run it
   - Go to Project Settings > API to get your project URL and anon key

## Usage Examples

1. General Questions:
   - "What is the capital of France?"
   - "What is the meaning of life?"
   - "How to setup supabase in a python project?"

2. Image Generation:
   - "I want to see a sunset"
   - "Generate an image of a dog"
   - "Draw a painting of the moon"

3. Music Generation:
   - "Play a song about the ocean"
   - "Create background music for a video about cats"
   - "I want to hear a song about the meaning of life"

4. Research Paper Generation:
   - "Write a research paper on the history of democracy"
   - "I need help writing a paper on the future of AI"
   - "Create a research paper on NVIDIA's announcements from CES 2025"

## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in the following values in `.env`:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `HF_API_KEY`: Your Hugging Face API key
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
   - `BRAVE_API_KEY`: Your Brave API key
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase anon key

## Running Locally

1. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run streamlit_app.py
   ```

## Running with Docker

1. Build and run the container:
   ```bash
   docker build -t chatbot-demo .
   docker run -it --rm -p 8501:8501 --env-file .env chatbot-demo
   ```

2. Open http://localhost:8501 in your browser


## Design Decisions

* The app is powered by Streamlit, which makes it very easy to quickly build a streaming chatbot app, and supports images and audio natively
  * This also made it very easy to deploy for free on Streamlit's free tier

* Main LLM engine is OpenAI's GPT-4o, where I make use of advanced features:
  * Tool calling for triggering image/audio/research generation based on user query in natural language
  * Streaming responses for a more interactive experience
  * Usage tracking for cost tracking
  * Integration using the `openai` python package

* I chose Huggingface as an engine for running open source models, only because it was the easiest to create a separate account using the provided funds
  * Generally I prefer replicate.com
  * Huggingface is often slow arbitrarily, and that causes higher wait times than I am usually comfortable delivering
  * Integration is a simple POST request to the API

* Image generation:
  * I chose flux-schnell for image generation, because of its speed and quality, to compensate for the wait times of huggingface

* Song generation:
  * Optimally I would use a song generation AI such as Suno v4, but it does not have an official API
  * Instead, I am constructing a song "creatively" by overlaying generated music with a text-to-speech of the lyrics
  * Consider this a POC work in progress
  * The model intelligently decides if the user asked for a song with lyrics, and is also capable of generating music without lyrics
  * Audio processing:
    * The text-to-speech output is reduced in volume, and a second of silence is added to the beginning for better musicality
    * The music and speech are mixed together, and the output is served to the user
    * The spoken lyrics are cut off at the end of the generated music
   * Optimally I would generate the music and the TTS in parallel using async code, but I ran into issues combining async code with the Streamlit codeflow and chose to keep it simple for delivering on time

* Text to Speech:
  * ElevenLabs is used for text-to-speech generation, with a generous free tier and high quality output
  * Integration is using the `elevenlabs` python package

* Research paper generation:
  * I am using Brave's search engine to get real-world information to base the research paper on
    * Implementation is a simple GET request to the API
  * The research paper is generated in markdown format, and is formatted with proper citations and sections
  * The research paper is generated in a streaming fashion, and the user can see the progress as it is generated
