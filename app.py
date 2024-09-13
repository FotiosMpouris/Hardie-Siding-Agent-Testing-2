import streamlit as st
from main_functions import (
    get_common_questions, search_hardie_siding, get_google_doc_by_address,
    scrape_specific_url, siding_project_agent, cold_email_agent
)

st.title("Hardie Siding Assistant")

# Get user's address
st.header("Your Hardie Siding Project")
address = st.text_input("Please enter your address:")
if address:
    google_doc_content = get_google_doc_by_address(address)
    if "No document found" not in google_doc_content and "Unable to retrieve document" not in google_doc_content:
        st.write("Document content successfully retrieved for your address.")
    else:
        st.write(google_doc_content)

# Interactive Q&A
st.header("Ask Questions About Your Siding Project")
user_question = st.text_input("Do you have any questions about your Hardie siding project? (type 'exit' to quit)")

if user_question and user_question.lower() != 'exit':
    # Perform search
    search_results = search_hardie_siding(user_question)

    # Generate cold email
    cold_email = cold_email_agent(user_question, search_results)

    # URL Construction with fallback
    query_mapping = {
        "what colors does hardie siding offer": "products/colors",
        "what styles of siding are available": "products/styles"
    }
    default_query = "products"
    page_path = query_mapping.get(user_question.lower(), default_query)
    url = f"https://www.jameshardie.com/{page_path}"
    scraped_content = scrape_specific_url(url)

    # Use siding_project_agent for interactive Q&A
    st.subheader("Expert Answer")
    siding_project_agent(user_question, search_results, cold_email, google_doc_content + "\n" + scraped_content)

    st.write("Feel free to ask more questions in the existing question box.")
elif user_question.lower() == 'exit':
    st.write("Thank you for using the Hardie Siding Assistant!")
