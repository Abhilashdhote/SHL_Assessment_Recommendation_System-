import streamlit as st
import pandas as pd
import json
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests
import re
from dotenv import load_dotenv
import os
import time
import threading

# Page configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = False
if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "raw_json" not in st.session_state:
    st.session_state.raw_json = ""
if "selected_query" not in st.session_state:
    st.session_state.selected_query = ""
if "input_type" not in st.session_state:
    st.session_state.input_type = "Job Description Text"
if "processing" not in st.session_state:
    st.session_state.processing = False
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "success_message" not in st.session_state:
    st.session_state.success_message = None

# Load the API key with improved user feedback
if not st.session_state.app_initialized:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    with st.sidebar:
        st.image("https://www.shl.com/assets/header-graphics/SHL-logo-colour-update.svg", width=200)
        st.title("SHL Assessment Recommender")
        
        if not api_key or not isinstance(api_key, str) or api_key.strip() == "":
            st.error("⚠️ GEMINI_API_KEY is missing or invalid in the deployment environment.")
            st.info("Please add a valid API key to your .env file or environment variables.")
            st.stop()
        else:
            st.success("✅ API connection established!")
            
    st.session_state.app_initialized = True
    genai.configure(api_key=api_key)
else:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

# Enhanced UI styles
st.markdown("""
    <style>
    /* Main styling */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #005B96;
        color: white;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #003F6C;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Card styling */
    .css-1r6slb0 {
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 5px;
        border: 1px solid #E5E7EB;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #005B96;
        font-weight: 700;
    }
    
    /* Labels */
    .stTextInput>label, .stSelectbox>label, .stRadio>label {
        color: #374151;
        font-weight: 500;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border: none;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f1f5f9;
    }
    
    /* Cards for recommendations */
    .recommendation-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }
    .recommendation-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .recommendation-title {
        color: #005B96;
        font-weight: 600;
        font-size: 18px;
        margin-bottom: 10px;
    }
    .recommendation-badge {
        display: inline-block;
        background-color: #E1F0FF;
        color: #005B96;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .recommendation-detail {
        margin: 5px 0;
        color: #4B5563;
    }
    .recommendation-link {
        display: inline-block;
        background-color: #005B96;
        color: white;
        padding: 5px 15px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: 500;
        margin-top: 10px;
        transition: all 0.3s;
    }
    .recommendation-link:hover {
        background-color: #003F6C;
    }
    
    /* Progress animation */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .pulse-animation {
        animation: pulse 1.5s infinite;
    }
    
    /* Improved tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
        color: #4B5563;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #005B96 !important;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

def json_extraction(response_text):
    """Extract JSON array from the model response"""
    try:
        if isinstance(response_text, str):
            match = re.search(r'(\[\s*{.*?}\s*\])', response_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        elif isinstance(response_text, list):
            return response_text
        else:
            st.session_state.error_message = "Unsupported response format received. Expected string or list."
    except json.JSONDecodeError as e:
        st.session_state.error_message = f"Could not process model response. Please try again."
    except Exception as e:
        st.session_state.error_message = f"Unexpected error during processing. Please try again."
    return []

def get_assessment_recommendation(query):
    """Get AI recommendations based on job description"""
    model = genai.GenerativeModel("gemini-1.5-pro")
    if len(query) > 1500:
        query = query[:1500]  # Limit length to avoid token issues
    
    prompt = (
        f"Given the following job description, recommend up to 7 SHL assessments that would be most suitable.\n\n"
        f"{query.strip()}\n\n"
        "Respond ONLY as a JSON array with up to 7 objects. Each object must have:\n"
        "- Assessment Name (string)\n"
        "- URL (string, MUST be a valid SHL link starting with https://www.shl.com/)\n"
        "- Remote Testing Support (exactly 'Yes' or 'No')\n"
        "- Adaptive/IRT Support (exactly 'Yes' or 'No')\n"
        "- Duration (string with time in minutes, e.g. '25 minutes')\n"
        "- Test Type (list of strings, e.g. ['Numerical', 'Reasoning'])\n"
        "- Description (short string with 1-2 sentences describing the assessment)\n\n"
        "Important: Ensure all URLs begin with 'https://www.shl.com/' and are valid links.\n"
        "Format Test Type as an actual array of strings, not a single string.\n"
        "Example of correct format for Test Type: ['Numerical', 'Reasoning'] not 'Numerical, Reasoning'.\n"
        "Do NOT add explanation or commentary. Only return valid JSON that can be parsed using json.loads()."
    )

    response_container = {"response": None, "error": None}

    def make_api_call():
        try:
            response = model.generate_content(prompt)
            response_container["response"] = response.text.strip()
        except Exception as e:
            response_container["error"] = str(e)

    api_thread = threading.Thread(target=make_api_call)
    api_thread.start()
    
    # Show a dynamic progress bar during processing
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        if not api_thread.is_alive():
            break
        progress_bar.progress(i + 1)
        status_text.markdown(f"""
            <div style="text-align: center">
                <p class="pulse-animation">Processing your job description...</p>
                <p style="font-size: 12px; color: #6B7280">Finding the best assessments for your needs</p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(0.3)
    
    # Clean up progress display
    progress_bar.empty()
    status_text.empty()
    
    # Handle API response
    if api_thread.is_alive():
        api_thread.join(timeout=5)  # Give a little more time to finish
        if api_thread.is_alive():
            st.session_state.error_message = "Request timed out. Please try again with a shorter job description."
            return None
            
    if response_container["error"]:
        st.session_state.error_message = f"Error connecting to recommendation service: {response_container['error']}"
        return None
    else:
        return response_container["response"]

def get_assessment_recommendation_with_retries(query, max_retries=2):
    """Handle retries for the recommendation API"""
    for attempt in range(max_retries):
        response = get_assessment_recommendation(query)
        if response is not None:
            return response
        if attempt < max_retries - 1:
            wait_time = 2 * (attempt + 1)  # Backoff: 2, 4 seconds
            retry_message = st.empty()
            retry_message.warning(f"Retrying request... Attempt {attempt + 1}/{max_retries}")
            time.sleep(wait_time)
            retry_message.empty()
    
    if st.session_state.error_message is None:
        st.session_state.error_message = "Unable to process your request. Please try again later or with a different job description."
    return None

def extract_job_description_from_url(url):
    """Extract job description from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to focus on the main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'job|position|description', re.I))
        
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
            
        # Clean up the text
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def display_recommendations(recommendations):
    """Display recommendations in an interactive card layout"""
    if not recommendations:
        st.warning("No matching assessments found. Try adjusting your search criteria.")
        return
    
    # Get unique test types for filtering
    test_types = set()
    for rec in recommendations:
        if isinstance(rec.get("Test Type"), list):
            test_types.update(rec["Test Type"])
        elif isinstance(rec.get("Test Type"), str):
            test_types.add(rec["Test Type"])
    
    # Create filter sidebar
    with st.sidebar:
        st.subheader("Filter Results")
        
        # Test type filter
        selected_types = st.multiselect(
            "Assessment Types:",
            options=sorted(test_types),
            default=[],
            help="Select one or more assessment types to filter"
        )
        
        # Duration filter with slider
        max_duration = st.slider(
            "Maximum Duration (minutes):",
            min_value=5,
            max_value=120,
            value=60,
            step=5,
            help="Slide to set the maximum assessment duration"
        )
        
        # Remote testing filter
        remote_options = ["All", "Yes", "No"]
        remote_filter = st.radio(
            "Remote Testing Support:",
            options=remote_options,
            index=0,
            horizontal=True
        )
        
        # Adaptive testing filter
        adaptive_options = ["All", "Yes", "No"]
        adaptive_filter = st.radio(
            "Adaptive/IRT Support:",
            options=adaptive_options,
            index=0,
            horizontal=True
        )
    
    # Apply filters
    filtered_recs = recommendations.copy()
    
    # Filter by test type
    if selected_types:
        filtered_recs = [
            rec for rec in filtered_recs
            if any(
                t in (rec["Test Type"] if isinstance(rec["Test Type"], list) else [rec["Test Type"]])
                for t in selected_types
            )
        ]
    
    # Filter by duration
    filtered_recs = [
        rec for rec in filtered_recs
        if (
            isinstance(rec.get("Duration"), str) and
            re.search(r'\d+', rec["Duration"]) and
            int(re.search(r'\d+', rec["Duration"]).group()) <= max_duration
        )
    ]
    
    # Filter by remote testing support
    if remote_filter != "All":
        filtered_recs = [
            rec for rec in filtered_recs
            if rec.get("Remote Testing Support") == remote_filter
        ]
    
    # Filter by adaptive testing support
    if adaptive_filter != "All":
        filtered_recs = [
            rec for rec in filtered_recs
            if rec.get("Adaptive/IRT Support") == adaptive_filter
        ]
    
    # Display count of results
    st.markdown(f"### Found {len(filtered_recs)} matching assessments")
    
    # Display as enhanced table
    if filtered_recs:
        df = pd.DataFrame(filtered_recs)
        
        # Ensure all expected columns exist
        for col in ["Assessment Name", "URL", "Remote Testing Support", "Adaptive/IRT Support", "Duration", "Test Type", "Description"]:
            if col not in df.columns:
                df[col] = ["N/A"] * len(df)
        
        # Fix and validate URLs
        for i, url in enumerate(df["URL"]):
            if not isinstance(url, str) or not url.startswith("http"):
                df.at[i, "URL"] = "https://www.shl.com/solutions/products/product-catalog/"
        
        # Format test types for better display
        if "Test Type" in df.columns:
            df["Test Type"] = df["Test Type"].apply(
                lambda x: x if isinstance(x, list) else [x] if isinstance(x, str) else ["General"]
            )
        
        # Configure column display with improved formatting
        st.dataframe(
            df,
            column_config={
                "Assessment Name": st.column_config.TextColumn("Assessment Name", width="medium"),
                "URL": st.column_config.LinkColumn("URL", display_text="View Assessment", width="small"),
                "Remote Testing Support": st.column_config.TextColumn("Remote", width="small"),
                "Adaptive/IRT Support": st.column_config.TextColumn("Adaptive", width="small"),
                "Duration": st.column_config.TextColumn("Duration", width="small"),
                "Test Type": st.column_config.ListColumn("Test Type", width="medium"),
                "Description": st.column_config.TextColumn("Description", width="large")
            },
            hide_index=True,
            use_container_width=True
        )

# Sidebar content
with st.sidebar:
    st.markdown("---")
    st.subheader("About this app")
    st.markdown("""
    This app uses AI to recommend SHL assessments based on job descriptions.
    
    **How to use:**
    1. Enter a job description (text or URL)
    2. Click "Find Assessments"
    3. Filter results as needed
    
    **Need help?** Contact your SHL representative.
    """)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
        <div style="text-align: center; color: #9CA3AF; margin-top: 1rem;">
            <p style="font-size: 12px;">Powered by Streamlit & Gemini AI</p>
            <p style="font-size: 12px;"><a href="https://www.shl.com/" style="color: #60A5FA;">SHL Website</a></p>
        </div>
    """, unsafe_allow_html=True)

# Main content layout
st.title("SHL Assessment Recommender")
st.markdown("Find the perfect assessments for your hiring needs in seconds. This tool uses AI to analyze job descriptions and recommend the most suitable SHL assessments.")

# Tab for job description input
tab1, tab2 = st.tabs(["📝 Job Description", "📊 Recommendations"])

with tab1:
    st.markdown("### Enter Job Description")
    
    # Job description input options
    input_type = st.radio(
        "Select input method:",
        ["Sample Job", "Text Input", "URL Input"],
        horizontal=True,
        key="input_method"
    )
    
    # Sample job descriptions
    sample_queries = [
        "Hiring a software engineer skilled in Python, JavaScript, and system design, with experience in cloud architecture and CI/CD pipelines. The candidate should have strong problem-solving skills and be able to work in an agile environment.",
        "Looking for a product manager with experience in agile methodologies, market research, and team leadership. The ideal candidate will have 3+ years of experience in product development and a track record of successful product launches.",
        "Recruiting a data analyst with expertise in Excel, SQL, Power BI, and statistics. The role requires strong analytical thinking and the ability to communicate insights to non-technical stakeholders.",
        "Seeking a customer service representative with excellent communication skills, problem-solving abilities, and experience with CRM systems. The ideal candidate will be patient, empathetic, and able to handle difficult customer situations."
    ]
    
    if input_type == "Sample Job":
        job_selection = st.selectbox(
            "Choose a sample job description:",
            options=range(len(sample_queries)),
            format_func=lambda i: f"Sample {i+1}: {sample_queries[i][:50]}...",
            key="sample_selection"
        )
        st.session_state.job_desc = sample_queries[job_selection]
        
        with st.expander("View full sample job description"):
            st.markdown(f"```\n{st.session_state.job_desc}\n```")
            
    elif input_type == "Text Input":
        st.session_state.job_desc = st.text_area(
            "Paste the job description here:",
            height=200,
            key="text_input_area",
            value=st.session_state.job_desc if st.session_state.job_desc and st.session_state.input_type == "Text Input" else "",
            help="Copy and paste the job description from your document or website"
        )
        
    else:  # URL Input
        url_input = st.text_input(
            "Enter the job posting URL:",
            key="url_input_field",
            help="Enter the web address of the job posting"
        )
        
        if url_input and st.button("Extract Job Description", key="extract_button"):
            with st.spinner("Extracting job description from URL..."):
                extracted_text = extract_job_description_from_url(url_input)
                if extracted_text.startswith("Error"):
                    st.error(extracted_text)
                else:
                    st.session_state.job_desc = extracted_text
                    st.success("✅ Job description extracted successfully!")
                    with st.expander("View extracted job description"):
                        st.markdown(f"```\n{st.session_state.job_desc[:500]}...\n```")
    
    # Processing controls
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔍 Find Assessments", key="find_button", use_container_width=True):
            if not st.session_state.job_desc.strip():
                st.warning("Please enter a job description first.")
            else:
                # Clear previous results and errors
                st.session_state.error_message = None
                st.session_state.recommendations = []
                st.session_state.processing = True
                st.session_state.success_message = None
                
                # Process in background
                with st.spinner("Analyzing job description..."):
                    raw_json = get_assessment_recommendation_with_retries(st.session_state.job_desc)
                    
                if raw_json:
                    st.session_state.raw_json = raw_json
                    st.session_state.recommendations = json_extraction(raw_json)
                    if st.session_state.recommendations:
                        st.session_state.success_message = "✅ Analysis complete! View your recommendations in the Recommendations tab."
                        st.switch_page = "tab2"  # Trigger tab switch after processing
                else:
                    if not st.session_state.error_message:
                        st.session_state.error_message = "Unable to generate recommendations. Please try again."
                        
                st.session_state.processing = False
                
                # Automatically switch to recommendations tab if successful
                if st.session_state.recommendations:
                    st.rerun()
    
    with col2:
        if st.button("🔄 Reset", key="reset_button", use_container_width=True):
            st.session_state.job_desc = ""
            st.session_state.recommendations = []
            st.session_state.raw_json = ""
            st.session_state.error_message = None
            st.session_state.success_message = None
            st.rerun()
    
    # Show messages
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.session_state.error_message = None
        
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None
        
    # Add tips section
    with st.expander("Tips for better recommendations"):
        st.markdown("""
        - Include specific skills, competencies, and technologies required for the role
        - Mention seniority level and required years of experience
        - Describe key responsibilities and tasks
        - Include soft skills and team dynamics information
        - Specify industry or domain knowledge requirements
        """)

with tab2:
    if st.session_state.recommendations:
        display_recommendations(st.session_state.recommendations)
    else:
        st.info("No recommendations yet. Enter a job description and click 'Find Assessments' to get started.")
        
        # Example of what recommendations will look like as a table
        with st.expander("Preview example recommendations"):
            sample_data = {
                "Assessment Name": ["SHL Verify Interactive - Numerical Reasoning", "SHL Personality Questionnaire"],
                "URL": ["https://www.shl.com/solutions/products/product-catalog/", "https://www.shl.com/solutions/products/product-catalog/"],
                "Remote Testing Support": ["Yes", "Yes"],
                "Adaptive/IRT Support": ["Yes", "No"],
                "Duration": ["25 minutes", "40 minutes"],
                "Test Type": [["Numerical", "Problem-solving"], ["Personality", "Behavioral"]],
                "Description": [
                    "Evaluates a candidate's ability to analyze and interpret numerical data.",
                    "Assesses key personality traits relevant to workplace performance."
                ]
            }
            sample_df = pd.DataFrame(sample_data)
            
            st.dataframe(
                sample_df,
                column_config={
                    "Assessment Name": st.column_config.TextColumn("Assessment Name", width="medium"),
                    "URL": st.column_config.LinkColumn("URL", display_text="View Assessment", width="small"),
                    "Remote Testing Support": st.column_config.TextColumn("Remote", width="small"),
                    "Adaptive/IRT Support": st.column_config.TextColumn("Adaptive", width="small"),
                    "Duration": st.column_config.TextColumn("Duration", width="small"),
                    "Test Type": st.column_config.ListColumn("Test Type", width="medium"),
                    "Description": st.column_config.TextColumn("Description", width="large")
                },
                hide_index=True,
                use_container_width=True
            )
