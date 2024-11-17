# **PROJECT NAME - DATA HARVESTER**

### **Project Description**

Data Harvester is a comprehensive AI-based agent designed for efficient data extraction and processing. This tool facilitates seamless integration of datasets from CSV files or Google Sheets and leverages cutting-edge technologies such as large language models (LLMs) and web scraping APIs to retrieve and organize specific information based on user-defined queries.

### **Key Capabilities**

- **Data Input Options:** Users can upload CSV files or connect directly to Google Sheets with real-time access.  
- **Customizable Query Input:** Generate precise information retrieval queries using placeholder-based templates like `{company}`.  
- **Web Search Automation:** Automatically fetch relevant data for each entity in a dataset via integrated APIs such as SERP or ScraperAPI.  
- **Dynamic Column Selection:** Define any column for processing (e.g., company names, product codes) and retrieve targeted data based on user queries.  
- **LLM Integration:** Employ advanced language models to parse web results and extract specific information, such as emails and phone numbers.  
- **Output Flexibility:** View structured data in a user-friendly interface, download it as a CSV file, or update connected Google Sheets.  
- **Session Management:** Built-in session handling to maintain user credentials and data state during processing.  
- **Progress Feedback:** Includes real-time progress bars and error notifications for enhanced user experience.  

---

### **Setup Instructions**

Follow these steps to install dependencies and run the Data Harvester application:

#### **1. Clone the Repository**

Start by cloning the GitHub repository to your local machine:

```bash
git clone https://github.com/Dhruvvv2503/DATA_HARVESTER.git
cd DATA_HARVESTER
```

#### **2. Set Up a Virtual Environment (Optional but Recommended)**

To avoid dependency conflicts, create and activate a virtual environment:

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### **3. Install Dependencies**

Install the required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

#### **4. Configure API Keys**

The application uses a `secrets.toml` file for securely storing API keys. Ensure your `secrets.toml` file is in the `.streamlit/` directory.

Create the folder structure if it doesn’t already exist:
```bash
mkdir -p .streamlit
```

Add your API keys to `.streamlit/secrets.toml` in the following format:
```toml
[GEMINI]
API_KEY = "your_gemini_api_key"

[SERPAPI]
API_KEY = "your_serpapi_key"
```

Replace `your_gemini_api_key` and `your_serpapi_key` with your actual keys.

#### **5. Prepare the Google Sheets API Credentials**

Download the `client_secret.json` file from the Google Cloud Console and place it in the project directory.

#### **6. Run the Application**

Start the Streamlit application by running:
```bash
streamlit run app.py
```

This command will open the application in your default web browser.

---

### **Usage Guide**

#### **1. Dashboard Overview**

The Data Harvester dashboard is intuitive and user-friendly, designed for both technical and non-technical users.

#### **2. Steps to Use**

1. **Data Upload:** Upload a CSV file by clicking “Browse” or connect your Google Sheets using credentials.  
2. **Column Selection:** Choose any column containing entities to process, such as company names or product identifiers.  
3. **Custom Query Input:** Enter a prompt, e.g., "Find the email address and phone number for {company}".  
4. **Data Processing:** Initiate processing with LLM and web search integration. View progress in real-time.  
5. **Export Results:** Save the output to a CSV file or export directly to Google Sheets.  

---

### **Extra Features**

- **Enhanced Error Notifications:** Feedback mechanisms to inform users of issues during data processing.  
- **Real-Time Progress Bar:** Displays the status of ongoing tasks like web searches or LLM processing.  
- **Flexible Query Input:** Dynamic prompts for more specific information retrieval.  

---

### **Limitations**

1. **API Request Limits:** Ensure that your API keys have sufficient quota to handle large datasets.  
2. **File Size Constraints:** Large CSV files may slow down processing; optimize data before upload.  
3. **Dependency on Internet:** Requires an active internet connection for LLM integration and web scraping.  

---

### **FAQ**

**Q1: What should I do if I encounter an error?**  
A: The application provides real-time error notifications. Check your API keys, internet connection, and input data format.  

**Q2: How do I reset session data?**  
A: Restart the application to clear session data or reinitialize the session state via the dashboard.  

**Q3: Can I use this tool for non-commercial purposes?**  
A: Yes, but ensure compliance with the terms of use for all integrated APIs.  

---
