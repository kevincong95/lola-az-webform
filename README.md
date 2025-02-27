---
# AI-Powered Tutoring System

An interactive tutoring application built with LangGraph and Streamlit that creates personalized lessons and asks questions to test understanding.

## Features

- Generates a custom lesson plan based on your chosen topic
- Creates multiple-choice questions to test understanding
- Provides immediate feedback on answers
- Summarizes your learning progress at the end

## How to Use

1. Enter a topic you want to learn about
2. Click "Start Lesson" to generate a personalized lesson plan
3. Answer the questions that are presented
4. Receive a learning summary upon completion

## Setup for Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Run the application: `streamlit run cassie_streamlit.py`

## Deployment

This application is deployed on Streamlit Community Cloud.

