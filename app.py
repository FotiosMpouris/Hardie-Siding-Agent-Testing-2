import streamlit as st
from main_functions import (
    get_common_questions, search_hardie_siding, get_google_doc_by_address, 
    answer_question, test_google_drive_access, scrape_specific_url, 
    siding_project_agent, cold_email_agent
)
st.title("Hardie Siding Assistant")
common_questions = get_common_questions()
# ... (previous code for Google Drive access test and common questions remains unchanged)
# Get user's address
st.header("Your Hardie Siding Project")
address = st.text_input("Please enter your address:")
if address:
    st.write(f"Address entered: {address}")
   # st.write("Attempting to retrieve document content...")
    google_doc_content = get_google_doc_by_address(address)
  #  st.write(f"Document content retrieval result: {google_doc_content[:100]}...")  # Show first 100 chars of the result
    if "No document found" not in google_doc_content and "Unable to retrieve document" not in google_doc_content:
        st.write("Document content successfully retrieved for your address.")
    else:
        st.write(google_doc_content)  # Display the error message
# Interactive Q&A
st.header("Ask Questions About Your Siding Project")
user_question = st.text_input("Do you have any questions about your Hardie siding project? (type 'exit' to quit)")
if user_question:
    if user_question.lower() == 'exit':
        st.write("Thank you for using the Hardie Siding Assistant!")
    else:
        st.write(f"Your question: {user_question}")
        # Perform search
        search_results = search_hardie_siding(user_question)
        # Generate cold email
        cold_email = cold_email_agent(user_question, search_results)
        st.subheader("Personalized Information")
        st.write(cold_email)
        # URL Construction with fallback
        query_mapping = {
            "what colors does hardie siding offer": "products/colors",
            "what styles of siding are available": "products/styles"
        }
        default_query = "products"
        page_path = query_mapping.get(user_question.lower(), default_query)
        url = f"https://www.jameshardie.com/{page_path}"

       # st.write(f"Attempting to scrape URL: {url}")
        scraped_content = scrape_specific_url(url)

        # Check if valid scraped content is returned
        # if scraped_content:
        #     st.write("Scraped content:", scraped_content[:100])  # Show first 100 chars for feedback
        # else:
        #     st.write("Could not retrieve specific information from the website. Please visit the official James Hardie site.")
        # Use siding_project_agent for interactive Q&A
        st.subheader("Expert Answer")
        siding_project_agent(user_question, search_results, cold_email, google_doc_content)
        # Fallback for common questions
        common_responses = {
            "what colors does hardie siding offer": "Hardie siding offers a wide variety of colors. Please check the official website for the full list."
        }

        # Get answer from document content, common questions, or search results if siding_project_agent doesn't provide a response
        if 'response_generated' not in st.session_state or not st.session_state.response_generated:
            answer = answer_question(user_question, common_questions, search_results, google_doc_content, scraped_content)
            answer = common_responses.get(user_question.lower(), answer)  # Use fallback if question matches
            st.write(answer)
st.write("Feel free to ask more questions in the question box.")
