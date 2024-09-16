import streamlit as st
from main_functions import (
    get_common_questions, search_hardie_siding, get_google_doc_by_address,
    scrape_specific_url, siding_project_agent, cold_email_agent, video_transcript_agent,
    general_video_transcript_agent
)

st.title("Hardie Siding Assistant")
folder_id = st.text_input ("Enter Google Drive Folder ID", value="1Knd9Wk7pMSZue2mdgZZQtQfy1waUeLXH")

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
user_question = st.text_input("Do you have any questions about your Hardie siding project?")
if user_question and user_question.lower() != 'exit':
    # Perform search
    search_results = search_hardie_siding(user_question)
    # Scrape relevant content
    url = f"https://www.jameshardie.com/products"
    scraped_content = scrape_specific_url(url)
    # Combine all relevant information
    all_info = f"{search_results}\n{google_doc_content}\n{scraped_content}"
    # Use siding_project_agent for interactive Q&A
    st.subheader("Expert Answer")
    siding_project_agent(user_question, all_info, "", "")
    st.write("Feel free to ask more questions in the existing question box.")
elif user_question.lower() == 'exit':
    st.write("Thank you for using the Hardie Siding Assistant!")


if st.button("Generate New Video Transcript (Introductory/General)", key="generate_general_transcript"):
    if folder_id:
        with st.spinner("Generating new general video transcript..."):
            new_transcript = general_video_transcript_agent(folder_id, "")
        st.subheader("New General Video Transcript Template:")
        st.text_area("Generated General Transcript", new_transcript, height=300)
        st.download_button(
            label="Download New General Transcript",
            data=new_transcript,
            file_name="new_general_transcript.txt",
            mime="text/plain",
            key="download_general_transcript"
        )
    else:
        st.warning("Please enter a folder ID.")

if st.button("Generate New Project-Specific Video Transcript", key="generate_project_transcript"):
    if folder_id and new_project_info:
        with st.spinner("Generating new project-specific video transcript..."):
            new_transcript = video_transcript_agent(folder_id, new_project_info)
        st.subheader("New Project-Specific Video Transcript Template:")
        st.text_area("Generated Project-Specific Transcript", new_transcript, height=300)
        st.download_button(
            label="Download New Project-Specific Transcript",
            data=new_transcript,
            file_name="new_project_transcript.txt",
            mime="text/plain",
            key="download_project_transcript"
        )
    else:
        st.warning("Please enter both a folder ID and new project information.")



# if st.button("Generate New Script"):
#     if folder_id and new_project_info:
#         new_script = video_transcript_agent(folder_id, new_project_info)
#         st.write("Generated Script:")
#         st.write(new_script)
#     else:
#         st.warning("Please enter both a folder ID and new project information.")

# import streamlit as st
# from main_functions import (
#     get_common_questions, search_hardie_siding, get_google_doc_by_address,
#     scrape_specific_url, siding_project_agent, cold_email_agent
# )

# st.title("Hardie Siding Assistant")

# # Get user's address
# st.header("Your Hardie Siding Project")
# address = st.text_input("Please enter your address:")
# if address:
#     google_doc_content = get_google_doc_by_address(address)
#     if "No document found" not in google_doc_content and "Unable to retrieve document" not in google_doc_content:
#         st.write("Document content successfully retrieved for your address.")
#     else:
#         st.write(google_doc_content)

# # Interactive Q&A
# st.header("Ask Questions About Your Siding Project")
# user_question = st.text_input("Do you have any questions about your Hardie siding project?")

# if user_question and user_question.lower() != 'exit':
#     # Perform search
#     search_results = search_hardie_siding(user_question)

#     # Scrape relevant content
#     url = f"https://www.jameshardie.com/products"
#     scraped_content = scrape_specific_url(url)

#     # Combine all relevant information
#     all_info = f"{search_results}\n{google_doc_content}\n{scraped_content}"

#     # Use siding_project_agent for interactive Q&A
#     st.subheader("Expert Answer")
#     siding_project_agent(user_question, all_info, "", "")

#     st.write("Feel free to ask more questions in the existing question box.")
# elif user_question.lower() == 'exit':
#     st.write("Thank you for using the Hardie Siding Assistant!")
