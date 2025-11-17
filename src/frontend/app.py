import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Project Baseline", page_icon="📊", layout="wide")

st.title("📊 Project Baseline - Data Analysis Agent")

if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "df" not in st.session_state:
    st.session_state.df = None

api_key = st.sidebar.text_input("Enter your Groq API Key:", type="password", value=st.session_state.groq_api_key)

model_options = {
    "Llama 3.3 70B (Recommended)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Fast)": "llama-3.1-8b-instant",
    "Groq Compound (Tools)": "groq-compound"
}

selected_model = st.sidebar.selectbox(
    "Choose Model:",
    options=list(model_options.keys()),
    index=0
)

st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])

if st.sidebar.button("Load Sample IMDB Data"):
    try:
        st.session_state.df = pd.read_csv('imdb_sample.csv')
        st.sidebar.success("Sample data loaded!")
    except FileNotFoundError:
        st.sidebar.error("Sample file not found")

if uploaded_file is not None:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")

if st.session_state.df is not None:
    st.sidebar.markdown("### Dataset Info")
    st.sidebar.write(f"Rows: {len(st.session_state.df)}")
    st.sidebar.write(f"Columns: {len(st.session_state.df.columns)}")
    
    with st.sidebar.expander("View Columns"):
        st.write(list(st.session_state.df.columns))

def analyze_data_with_groq(df, user_question, api_key, model):
    client = Groq(api_key=api_key)
    
    # Get basic info about the dataframe
    df_info = f"""
    Dataset Info:
    - Rows: {len(df)}
    - Columns: {list(df.columns)}
    - Sample data (first 3 rows):
    {df.head(3).to_string()}
    
    Data types:
    {df.dtypes.to_string()}
    """
    
    if any(word in user_question.lower() for word in ['chart', 'plot', 'graph', 'visualiz']):
        prompt = f"""
        You are a data analyst. Given this dataset:
        {df_info}
        
        User wants: {user_question}
        
        Provide ONLY the Python code using plotly.express to create the visualization.
        Use 'df' as the dataframe variable.
        Do NOT include any imports or fig.show().
        Start directly with the data processing code.
        
        Example format:
        # Process the data
        df_genre = df['Genre'].str.split(',').explode().str.strip()
        genre_counts = df_genre.value_counts().reset_index()
        genre_counts.columns = ['Genre', 'Count']
        fig = px.bar(genre_counts, x='Genre', y='Count', title='Genre Distribution')
        """
    else:
        prompt = f"""
        You are a data analyst. Given this dataset:
        {df_info}
        
        User question: {user_question}
        
        Provide analysis of the data to answer their question.
        """
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.1
    )
    
    return response.choices[0].message.content

if api_key and st.session_state.df is not None:
    st.session_state.groq_api_key = api_key
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Dataset Preview")
        st.dataframe(st.session_state.df.head(), use_container_width=True)
    
    with col2:
        st.subheader("Quick Stats")
        st.write(st.session_state.df.describe())
    
    st.subheader("Data Analysis Chat")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "chart" in message:
                st.plotly_chart(message["chart"], use_container_width=True)
    
    if prompt := st.chat_input("Ask about your data (e.g., 'Create a bar chart of movie genres')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                response = analyze_data_with_groq(
                    st.session_state.df, 
                    prompt, 
                    api_key, 
                    model_options[selected_model]
                )
                
                # Check if this is a visualization request
                if any(word in prompt.lower() for word in ['chart', 'plot', 'graph', 'visualiz']):
                    # This should be code only
                    code_section = response.strip()
                    
                    # Clean up the code - remove markdown formatting if present
                    if code_section.startswith("```python"):
                        code_section = code_section.replace("```python", "").replace("```", "").strip()
                    elif code_section.startswith("```"):
                        code_section = code_section.replace("```", "").strip()
                    
                    # Remove fig.show() and replace with just creating fig
                    code_section = code_section.replace("fig.show()", "")
                    
                    # Show the code to user
                    st.code(code_section, language='python')
                    
                    try:
                        exec_globals = {
                            'pd': pd, 
                            'px': px, 
                            'df': st.session_state.df.copy(),  # Use a copy to avoid modifying original
                            'go': go
                        }
                        exec(code_section, exec_globals)
                        
                        if 'fig' in exec_globals:
                            fig = exec_globals['fig']
                            st.plotly_chart(fig, use_container_width=True)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": response,
                                "chart": fig
                            })
                        else:
                            st.error("No chart was generated")
                            st.session_state.messages.append({"role": "assistant", "content": f"Code:\n{code_section}"})
                    except Exception as e:
                        st.error(f"Error creating chart: {str(e)}")
                        st.session_state.messages.append({"role": "assistant", "content": f"Code:\n{code_section}\nError: {str(e)}"})
                else:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

elif api_key and st.session_state.df is None:
    st.info("Please upload a CSV file or load sample data to start analyzing.")

elif not api_key:
    st.info("Please enter your Groq API key in the sidebar to start.")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Clear Data"):
    st.session_state.df = None
    st.session_state.messages = []
    st.rerun()