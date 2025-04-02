import re
import json
import pandas as pd
import streamlit as st
import time  # For simulating processing time

# Function to extract lead data from the pasted text
def extract_lead_data_from_text(text):
    pattern = re.compile(r'Event_datum: (\{.*?\})\s+Utm Medium: (.*?)\s*(?=\n|$)', re.DOTALL)
    matches = pattern.findall(text)
    
    extracted_data = []
    
    for match in matches:
        try:
            # Try parsing JSON with exception handling
            event_data = json.loads(match[0])  # Parse the JSON from event_datum
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            continue  # Skip this record or handle error as needed
        
        utm_medium = match[1].strip()  # Clean up the utm_medium
        
        # If Utm Medium is 'N/A' or empty, assign 'Organic'
        if not utm_medium or utm_medium == 'N/A':
            utm_medium = "Organic"
        
        field_info = event_data.get("field_information", {})
        brand_name = field_info.get("brandName", "")
        contact_number = field_info.get("contactNumber", "")
        
        # Check if categories is empty, if so, set to 'N/A'
        categories = ", ".join(field_info.get("categories", [])) or "N/A"
        
        extracted_data.append({
            "Contact No.": contact_number,
            "Brand Name": brand_name,
            "Categories": categories,
            "Utm Medium": utm_medium
        })
    
    return extracted_data

# Function to handle uploaded file processing
def extract_lead_data_from_file(uploaded_file):
    try:
        # Read the uploaded Excel or CSV file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Extract relevant columns
        if "Event Datum" in df.columns and "Utm Medium" in df.columns:
            leads = []
            for _, row in df.iterrows():
                event_datum = row["Event Datum"]
                utm_medium = row["Utm Medium"]
                
                # Extracting information from the Event Datum
                try:
                    event_data = json.loads(event_datum)  # Parse the JSON from Event Datum
                    field_info = event_data.get("field_information", {})
                    brand_name = field_info.get("brandName", "")
                    contact_number = field_info.get("contactNumber", "")
                    categories = ", ".join(field_info.get("categories", [])) or "N/A"
                    
                    # Clean and process Utm Medium
                    utm_medium = utm_medium.strip() if isinstance(utm_medium, str) else ""  # Strip any spaces

                    if not utm_medium or utm_medium.lower() == 'n/a':  # Ensure case insensitivity
                        utm_medium = "Organic"
                    
                    leads.append({
                        "Contact No.": contact_number,
                        "Brand Name": brand_name,
                        "Categories": categories,
                        "Utm Medium": utm_medium
                    })
                except Exception as e:
                    st.error(f"Error parsing Event Datum: {e}")
            
            return pd.DataFrame(leads)
        else:
            st.error("Excel file must contain 'Event Datum' and 'Utm Medium' columns.")
            return None
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None


# Streamlit app interface
def main():
    st.title("Lead Data Extractor")

    # File upload
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        # Extract data from uploaded file
        leads_df = extract_lead_data_from_file(uploaded_file)
        
        if leads_df is not None:
            # Display the DataFrame
            st.write("### Extracted Leads Data")
            st.dataframe(leads_df)

    # Option to process the pasted text
    text_input = st.text_area(
        label="Or Paste Lead Data Here",
        placeholder="Paste your lead data in the text box...",
        height=200
    )
    
    # Custom CSS for styling the button
    st.markdown("""
        <style>
            .stButton>button {
                background-color: #4CAF50; /* Soothing Green */
                color: white;
                font-size: 16px;
                font-weight: normal;
                border-radius: 5px;
                padding: 8px 25px; /* Slim button */
                border: none;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #45a049; /* Slightly darker green */
            }
            .stButton>button:active {
                background-color: #388e3c; /* Dark green */
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Button to process data
    if st.button("Process Data from Text"):
        if text_input:
            with st.spinner('Processing your data...'):
                # Simulate processing for 1 second
                time.sleep(0.60)
                leads = extract_lead_data_from_text(text_input)
                df = pd.DataFrame(leads)
                st.write("### Extracted Leads Data from Text")
                st.dataframe(df)
        else:
            st.warning("Please paste the lead data first.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
