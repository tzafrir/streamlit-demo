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
* [Brave](https://brave.com) - for web search
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
