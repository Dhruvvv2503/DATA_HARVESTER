import streamlit as st
import pandas as pd
import requests
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import google.generativeai as genai
import re
from time import sleep

# Initialize session state variables
if "credentials" not in st.session_state:
    st.session_state["credentials"] = None
if "data" not in st.session_state:
    st.session_state["data"] = None
if "sheet_id" not in st.session_state:
    st.session_state["sheet_id"] = None
if "selected_column" not in st.session_state:
    st.session_state["selected_column"] = None


class DataLoader:
    def __init__(self):
        self.credentials = st.session_state["credentials"]
        self.data = st.session_state["data"]
        self.sheet_id = st.session_state["sheet_id"]

    def load_from_file(self, file):
        """Load data from a CSV file."""
        try:
            self.data = pd.read_csv(file)
            st.session_state["data"] = self.data
            return "Data successfully loaded from the uploaded file!"
        except Exception as e:
            return f"Error loading file: {e}"

    def load_from_google_sheets(self, client_secret_file):
        """Authenticate and load data from Google Sheets with user guidance."""
        if os.path.exists("token.pkl"):
            with open("token.pkl", "rb") as token:
                self.credentials = pickle.load(token)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file(
                    client_secret_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets'],
                    redirect_uri='http://localhost:8501'
                )
                auth_url, _ = flow.authorization_url(prompt='consent')
                st.write("**Step 1:** [Click here to authorize with Google]({})".format(auth_url))
                st.write("**Step 2:** Copy the `code` parameter from the redirected URL and paste it below:")

                auth_code = st.text_input("Paste the Google authentication code here:")
                if st.button("Validate Authentication Code"):
                    if auth_code:
                        try:
                            flow.fetch_token(code=auth_code)
                            self.credentials = flow.credentials
                            st.session_state["credentials"] = self.credentials
                            with open("token.pkl", "wb") as token:
                                pickle.dump(self.credentials, token)
                            st.success("Authentication successful! You can now load data from Google Sheets.")
                        except Exception as e:
                            st.error(f"Error during authentication: {e}")
                    else:
                        st.warning("Please enter the Google authentication code.")

        if self.credentials:
            if not self.sheet_id:
                sheet_url = st.text_input(
                    "Enter Google Sheets URL:",
                    help="Paste the full Google Sheets URL (e.g., https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit)"
                )
                if st.button("Validate Google Sheet URL"):
                    if sheet_url:
                        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
                        if match:
                            self.sheet_id = match.group(1)
                            st.session_state["sheet_id"] = self.sheet_id
                            st.success("Google Sheets URL is valid!")
                        else:
                            st.error("Invalid Google Sheets URL format. Please check and try again.")
                    else:
                        st.warning("Please enter a Google Sheets URL.")

            # Only process further if the sheet URL is valid
            if self.sheet_id:
                try:
                    service = build('sheets', 'v4', credentials=self.credentials)
                    result = service.spreadsheets().values().get(spreadsheetId=self.sheet_id, range="Sheet1").execute()
                    values = result.get('values', [])
                    if not values:
                        return "No data found in the Google Sheet."
                    else:
                        self.data = pd.DataFrame(values[1:], columns=values[0])
                        st.session_state["data"] = self.data
                        return "Data successfully loaded from Google Sheet!"
                except Exception as e:
                    return f"Failed to retrieve data. Error: {e}"
        else:
            return "Please provide a valid Google Sheets URL before proceeding."


class LLMProcessor:
    def __init__(self, api_key, serpapi_key, credentials=None):
        self.api_key = api_key
        self.serpapi_key = serpapi_key
        self.credentials = credentials
        self.configure_api()

    def configure_api(self):
        genai.configure(api_key=self.api_key)

    def get_search_results(self, query):
        params = {'engine': 'google', 'q': query, 'api_key': self.serpapi_key}
        try:
            response = requests.get('https://serpapi.com/search', params=params)
            response.raise_for_status()
            return response.json().get("organic_results", [])
        except requests.RequestException as e:
            st.error(f"Error fetching search results: {e}")
            return []

    def extract_information(self, text, prompt):
        extracted_data = {}
        if "email" in prompt.lower():
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            if emails:
                extracted_data['Email Address'] = emails
        if "phone" in prompt.lower():
            phones = re.findall(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b", text)
            if phones:
                extracted_data['Phone Numbers'] = phones
        if not extracted_data:
            extracted_data['Result'] = text[:200]
        return extracted_data

    def process_data(self, prompt, entities):
        results = []
        progress_bar = st.progress(0)  # Progress bar initialization
        total_entities = len(entities)

        for idx, entity in enumerate(entities):
            customized_query = prompt.replace("{company}", entity)
            search_results = self.get_search_results(customized_query)
            search_text = " ".join(result.get("snippet", "") for result in search_results)
            full_prompt = f"{customized_query}\nSearch Results: {search_text}"

            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(full_prompt)
                extracted_data = self.extract_information(response.text if response else "", prompt)
            except Exception as e:
                st.error(f"Error in LLM processing: {e}")
                extracted_data = {}

            result = {"Entity": entity}
            result.update(extracted_data)
            results.append(result)

            progress_bar.progress((idx + 1) / total_entities)  # Update progress bar
            sleep(0.1)  # Add slight delay for user feedback

        return pd.DataFrame(results)

    def export_to_google_sheet(self, sheet_id, data):
        if not self.credentials:
            st.error("No credentials available for Google Sheets export.")
            return

        try:
            service = build('sheets', 'v4', credentials=self.credentials)

            # Step 1: Add a new sheet
            sheet_name = st.text_input("Enter the name for the new sheet:", value="NewSheet")
            if not sheet_name:
                st.error("Sheet name cannot be empty.")
                return

            add_sheet_request = {
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": sheet_name
                            }
                        }
                    }
                ]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=add_sheet_request).execute()
            st.success(f"New sheet '{sheet_name}' created successfully.")

            # Step 2: Write data to the new sheet
            body = {'values': [data.columns.tolist()] + data.values.tolist()}
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            st.success(f"Data successfully exported to the new sheet '{sheet_name}'!")

        except Exception as e:
            st.error(f"An error occurred while exporting to Google Sheets: {e}")


# Streamlit Application
st.title("Data Upload Interface with Web Search and LLM Processing")
st.write("Choose a source to upload data from:")

data_loader = DataLoader()
data = st.session_state["data"]
is_google_sheets = False

upload_option = st.radio("Select Data Source:", ("From Computer", "From Google Sheets"))

if upload_option == "From Computer":
    uploaded_file = st.file_uploader("Choose a file", type=["csv"])
    if uploaded_file:
        message = data_loader.load_from_file(uploaded_file)
        st.success(message)
        data = st.session_state["data"]

elif upload_option == "From Google Sheets":
    is_google_sheets = True
    st.write("Authenticate with Google to access Google Sheets.")
    client_secret_file = "client_secret.json"
    message = data_loader.load_from_google_sheets(client_secret_file)
    if message:
        st.success(message)
        data = st.session_state["data"]

if data is not None:
    st.write("Data preview:")
    st.dataframe(data)

    # Column Selector
    selected_column = st.selectbox(
        "Select the column containing entities (e.g., company names):",
        data.columns,
        key="selected_column"
    )

    custom_prompt = st.text_input("Enter your custom prompt:", value="Get me the email address and phone numbers of {entity}")
    palm_api_key = st.secrets["GEMINI_API_KEY"]
    serpapi_key = st.secrets["SERPAPI_KEY"]

    if st.button("Proceed to LLM Processing"):
        llm_processor = LLMProcessor(api_key=palm_api_key, serpapi_key=serpapi_key, credentials=st.session_state["credentials"])
        entities = data[selected_column].dropna().tolist()

        st.write("Processing Data...")
        processed_data = llm_processor.process_data(custom_prompt, entities)

        st.write("Processed Data:")
        st.dataframe(processed_data)

        st.write("Export Options:")
        export_option = st.radio("Select export option:", ["Download as CSV", "Export to Google Sheets"])
        if export_option == "Download as CSV":
            csv_data = processed_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download Processed Data", data=csv_data, file_name="processed_data.csv", mime="text/csv")
        elif export_option == "Export to Google Sheets":
            if is_google_sheets:
                llm_processor.export_to_google_sheet(st.session_state["sheet_id"], processed_data)
            else:
                st.warning("Google Sheets export is only available when data is loaded from Google Sheets.")
