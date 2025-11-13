# Project Baseline

AI-powered data analysis tool using Groq LLM and Streamlit. Upload CSV files and generate insights with natural language queries.

## Features

- **CSV Upload**: Upload any CSV file or use sample IMDB data
- **Natural Language Queries**: Ask questions about your data in plain English
- **Automatic Visualizations**: Generate bar charts and plots with simple requests
- **Multiple Models**: Choose from Llama 3.3 70B, Llama 3.1 8B, or Groq Compound
- **Interactive Charts**: Powered by Plotly for responsive visualizations

## Setup

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get Groq API key**
   - Sign up at https://groq.com
   - Get your API key from the console

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Start analyzing**
   - Enter your API key in the sidebar
   - Upload a CSV file or load sample data
   - Ask questions like "Create a bar chart of movie genres"

## Example Queries

- "Create a bar chart about genre distribution"
- "What is the average rating of movies?"
- "Show me the top 10 highest rated films"
- "Make a plot of revenue by year"
