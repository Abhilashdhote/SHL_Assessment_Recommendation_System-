# SHL Assessment Recommender

![SHL Logo](https://www.shl.com/assets/header-graphics/SHL-logo-colour-update.svg)

## Overview

The SHL Assessment Recommender is an AI-powered tool designed to help recruiters and HR professionals identify the most suitable SHL assessments for their hiring needs. By analyzing job descriptions, this application provides tailored recommendations from SHL's extensive catalog of assessments, saving time and improving the assessment selection process.

## Features

- **AI-Powered Recommendations**: Leverages Google's Gemini AI to analyze job descriptions and suggest relevant assessments
- **Multiple Input Methods**: Enter job descriptions via text input, URL extraction, or pre-defined samples
- **Interactive Filtering**: Filter recommendations by assessment type, duration, remote testing support, and adaptive testing capabilities
- **Detailed Assessment Information**: View comprehensive details for each recommended assessment
- **Modern, Responsive UI**: User-friendly interface with intuitive controls and visually appealing design

## Technology Stack

- **Streamlit**: Web application framework for rapid development
- **Google Gemini AI**: Large language model for job description analysis and assessment recommendations
- **BeautifulSoup**: Web scraping capabilities for extracting job descriptions from URLs
- **Pandas**: Data manipulation and display
- **Threading**: Non-blocking API calls for improved user experience

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/shl-assessment-recommender.git
   cd shl-assessment-recommender
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root directory and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Access the application in your web browser at `http://localhost:8501`

3. Enter a job description using one of the input methods:
   - Select a sample job description
   - Paste a job description directly
   - Enter a URL to a job posting

4. Click "Find Assessments" to generate recommendations

5. Use the filters in the sidebar to refine the results

## Application Structure

```
shl-assessment-recommender/
├── app.py                  # Main application file
├── .env                    # Environment variables (API keys)
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
└── assets/                 # Images and other static assets
```

## Key Functions

- `get_assessment_recommendation()`: Calls the Gemini API to analyze job descriptions
- `extract_job_description_from_url()`: Extracts job descriptions from provided URLs
- `display_recommendations()`: Renders the assessment recommendations with filtering
- `json_extraction()`: Parses the AI model's response into structured data

## Error Handling

The application includes robust error handling for:
- API connection issues
- Invalid job description URLs
- JSON parsing errors
- Empty or insufficient job descriptions
- Request timeouts

## Customization

The UI is extensively customized using Streamlit's theming capabilities and custom CSS. Key style elements include:
- Custom card layouts for recommendations
- Interactive buttons with hover effects
- Loading animations for better user experience
- Responsive layout for different screen sizes

## Requirements

- Python 3.7+
- Streamlit 1.10+
- Google Generative AI package
- Requests
- BeautifulSoup4
- Pandas
- Python-dotenv


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or support, please contact [Your Contact Information]
