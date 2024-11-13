import streamlit as st
import pandas as pd
import requests
import openai
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import re

# Set up Streamlit UI
st.title("Data Upload Interface with Web Search and LLM Processing")
st.write("Choose a source to upload data from:")

# Define global data variable
data = None

# Step 1: Choose between file upload or Google Sheets
upload_option = st.radio("Select Data Source:", ("From Computer", "From Google Sheets"))

# Step 2: Handling local file upload
if upload_option == "From Computer":
    uploaded_file = st.file_uploader("Choose a file", type=["csv"])
    if uploaded_file is not None:
        try:
            data = pd.read_csv(uploaded_file)
            st.success("Data successfully loaded from the uploaded file!")
        except Exception as e:
            st.error(f"Error loading file: {e}")

# Step 3: Google Sheets integration with automated OAuth flow
elif upload_option == "From Google Sheets":
    st.write("Authenticate with Google to access Google Sheets.")
    
    # Check if we have saved credentials (using pickle)
    credentials = None
    if os.path.exists("token.pkl"):
        with open("token.pkl", "rb") as token:
            credentials = pickle.load(token)
    
    # If credentials don't exist or are invalid, go through OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # OAuth Flow setup
            flow = Flow.from_client_secrets_file(
                'YOUR_CLIENT_SECRET_FILE.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'],
                redirect_uri='http://localhost:8501'
            )
            
            # Check if authorization response code is available in query params
            query_params = st.experimental_get_query_params()
            if "code" not in query_params:
                auth_url, _ = flow.authorization_url(prompt='consent')
                st.write(f"[Authenticate with Google]({auth_url})")
                st.stop()  # Stops Streamlit to wait for user to complete authorization
            else:
                # Automatically fetch token using the authorization code from query parameters
                flow.fetch_token(code=query_params["code"][0])
                credentials = flow.credentials
                
                # Save the credentials for future sessions using pickle
                with open("token.pkl", "wb") as token:
                    pickle.dump(credentials, token)
                
                # Clear query params after successful authorization to avoid repeat triggers
                st.experimental_set_query_params()
                
                # Show success message
                st.success("Successfully authenticated with Google!")

    # If we have valid credentials, connect to Google Sheets
    if credentials:
        try:
            service = build('sheets', 'v4', credentials=credentials)
            
            # Allow the user to enter a Google Sheet URL
            sheet_url = st.text_input("Enter Google Sheets URL:")
            
            # Extract the sheet ID from the URL
            sheet_id = None
            if sheet_url:
                match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
                if match:
                    sheet_id = match.group(1)
            
            if sheet_id:
                # Fetch data from Google Sheets
                result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="Sheet1").execute()
                values = result.get('values', [])
                
                if not values:
                    st.write("No data found in the Google Sheet.")
                else:
                    # Convert data to DataFrame and display
                    data = pd.DataFrame(values[1:], columns=values[0])  # First row as header
                    st.success("Data successfully loaded from Google Sheet!")
        except Exception as e:
            st.error(f"Failed to retrieve data. Error: {e}")

# Data Preview and Column Selection
if data is not None:
    st.write("Data preview:")
    st.dataframe(data)
    
    # Column selection for data interpretation
    column_options = data.columns.tolist()
    selected_column = st.selectbox("Select a column for data interpretation:", column_options)
    
    # Custom prompt input with placeholder
    st.write("Define a custom prompt. You can use placeholders like `{company}` for dynamic replacement.")
    custom_prompt = st.text_input("Enter your custom prompt:", value="Get me the email address of {company}")
    
    # API keys input
    serpapi_key = st.text_input("Enter your SerpAPI key:", type="password")
    openai_key = st.text_input("Enter your OpenAI API key:", type="password")

    # Web search for each entity and send results to ChatGPT
    if st.button("Process Data with LLM"):
        if serpapi_key and openai_key and selected_column:
            # Configure OpenAI API key
            openai.api_key = openai_key
            search_results = []
            parsed_results = []

            for entity in data[selected_column]:
                # Replace placeholder with actual entity
                query = custom_prompt.replace("{company}", entity)
                
                # Step 1: Make a request to SerpAPI for web search results
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": serpapi_key,
                }
                response = requests.get("https://serpapi.com/search", params=params)
                
                # Check if response is successful
                if response.status_code == 200:
                    result_json = response.json()
                    if "organic_results" in result_json:
                        # Collect relevant search results
                        search_text = "\n".join([
                            f"Title: {result['title']}\nLink: {result['link']}\nSnippet: {result['snippet']}"
                            for result in result_json["organic_results"]
                        ])
                        
                        # Step 2: Send search results and prompt to OpenAI LLM
                        gpt_prompt = f"Extract specific information based on this prompt: '{custom_prompt}'\n\nSearch Results:\n{search_text}"
                        
                        # Updated syntax for OpenAI ChatCompletion
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": gpt_prompt}
                            ],
                            max_tokens=100
                        )
                        
                        # Parse the response
                        parsed_output = response.choices[0].message['content'].strip()
                        parsed_results.append({
                            "Entity": entity,
                            "Extracted Information": parsed_output
                        })

            # Display the parsed results
            results_df = pd.DataFrame(parsed_results)
            st.write("Extracted Information from LLM:")
            st.dataframe(results_df)

            # Optional: Download results as CSV
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Extracted Results as CSV",
                data=csv,
                file_name="extracted_information.csv",
                mime="text/csv",
            )
        else:
            st.error("Please enter your SerpAPI and OpenAI keys and select a column.")
