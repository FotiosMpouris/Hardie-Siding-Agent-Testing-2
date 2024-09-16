import os
from dotenv import load_dotenv
from groq import Groq
from together import Together
from exa_py import Exa
from google.oauth2 import service_account
from googleapiclient.discovery import build
import streamlit as st
from bs4 import BeautifulSoup
import requests
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import numpy as np

# Load environment variables and initialize clients (unchanged)
load_dotenv()
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
together_client = Together(api_key=st.secrets["TOGETHER_API_KEY"])
exa_client = Exa(api_key=st.secrets["EXA_API_KEY"])

#adding this here from edit suggestions 9 16 @1034am
FOLDER_ID = '1Knd9Wk7pMSZue2mdgZZQtQfy1waUeLXH'
# Set up Google Drive and Docs API clients (unchanged)
creds = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_SERVICE_ACCOUNT_INFO"],
    scopes=['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/documents.readonly']
)
drive_service = build('drive', 'v3', credentials=creds)
docs_service = build('docs', 'v1', credentials=creds)


def remove_timestamps(text):
    """Remove timestamps in the format [hh:mm:ss] from the text."""
    return re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)

def extract_common_points(doc_contents):
    """Extract and return common themes from a list of document contents using TF-IDF and cosine similarity."""
    # Vectorize the document contents
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(doc_contents)
    
    # Calculate the similarity matrix
    similarity_matrix = cosine_similarity(X, X)
    
    # Identify common themes
    common_themes = defaultdict(float)
    
    # Average similarity score for each term
    terms = vectorizer.get_feature_names_out()
    for i in range(len(doc_contents)):
        # Get the index of the most similar document
        similar_indices = np.argsort(similarity_matrix[i])[::-1]
        
        # Aggregate terms from similar documents
        for j in similar_indices:
            if i != j:  # Ignore self-similarity
                for term_index in X[i].indices:
                    term = terms[term_index]
                    common_themes[term] += similarity_matrix[i][j]
    
    # Sort themes by relevance
    sorted_themes = sorted(common_themes.items(), key=lambda x: x[1], reverse=True)
    
    # Create a summary of common themes
    summary = "\n".join([f"{term}: {score:.2f}" for term, score in sorted_themes])
    
    return summary

# Example usage
doc_contents = [
    "Document content 1 with common theme.",
    "Document content 2 with a recurring theme.",
    "Another document with similar themes."
]

common_points_summary = extract_common_points(doc_contents)
print(common_points_summary)


def video_transcript_agent(input_info):
    """
    Generate a new video transcript based on existing documents in the Google Drive folder
    and combined input information (general transcript and new project info).
    """
    try:
        # Get all documents from the specified folder
        query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.document'"
        results = drive_service.files().list(q=query).execute()
        files = results.get('files', [])
        if not files:
            return "No documents found in the specified folder."

        # Combine content from all documents
        doc_contents = []
        for file in files:
            doc_content = get_google_doc_content(file['id'])
            cleaned_content = remove_timestamps(doc_content)  # Remove timestamps
            doc_contents.append(cleaned_content)

        # Extract common points from the document contents
        common_points = extract_common_points(doc_contents)

        # Combine common points with input information
        combined_content = f"{common_points}\n\nCombined Input Information:\n{input_info}"

        # Generate new transcript using the AI model in a first-person conversational tone
        response = together_client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI scriptwriting assistant for a James Hardie siding sales team.
                    Analyze the following content from multiple documents, the general transcript, and new project information to create a comprehensive and personalized script.
                    Create a detailed, consistent framework for a conversational script in the first-person perspective. 
                    Ensure the script reflects common themes, incorporates the general transcript and new project information, and provides a comprehensive overview. 
                    Avoid any timestamps or names like Jim, and make sure the script feels natural, informative, and tailored to the specific project.
                    You are representing Patriot Contracting, *** do not mention that you are a James Hardie Elite 
                    Preferred Contractor until the end of the script"""
                },
                {
                    "role": "user",
                    "content": f"Create a detailed, personalized video transcript script based on the following content, general transcript, and new project information:\n\n{combined_content}"
                }
            ],
            max_tokens=1500,  # Increased token limit to accommodate more content
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error in video_transcript_agent: {str(e)}")
        return f"Unable to generate a new video transcript due to an error: {str(e)}"

def scrape_certainteed(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract relevant content (adjust selectors as needed)
        title = soup.find('h1').get_text() if soup.find('h1') else ""
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        headings = [h.get_text() for h in soup.find_all(['h2', 'h3', 'h4'])]
        list_items = [li.get_text() for li in soup.find_all('li')]

        # Combine the extracted content
        page_content = f"Title: {title}\n\n"
        page_content += "Headings:\n" + "\n".join(headings) + "\n\n"
        page_content += "Content:\n" + "\n".join(paragraphs) + "\n\n"
        page_content += "List Items:\n" + "\n".join(list_items)

        # Limit content length
        max_content_length = 2000  # Adjust as needed
        if len(page_content) > max_content_length:
            return page_content[:max_content_length] + "..."

        return page_content if page_content else "No relevant content found on this page."

    except requests.exceptions.RequestException as e:
        return f"An error occurred while trying to scrape the CertainTeed URL: {e}"

def scrape_specific_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        # Example: Extracting all paragraph and heading text
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        headings = [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])]
        list_items = [li.get_text() for li in soup.find_all('li')]

        # Combine the extracted content
        page_content = "\n".join(headings + paragraphs + list_items)

        # Limit content length
        max_content_length = 1000  # You can adjust this limit
        if len(page_content) > max_content_length:
            return page_content[:max_content_length] + "..."

        return page_content if page_content else "No relevant content found on this page. Please check the URL."

    except requests.exceptions.RequestException as e:
        return f"An error occurred while trying to scrape the URL: {e}"
#def get_common_questions():
    # ... (keep the existing implementation)
def get_common_questions():
    default_questions = [
        "What is Hardie Siding?",
        "How long does Hardie Siding last?",
        "Is Hardie Siding expensive?",
        "Can Hardie Siding be painted?",
        "Is Hardie Siding fire-resistant?"
    ]
    
    try:
        response = together_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": "Generate 5 common questions about Hardie siding."},
                {"role": "user", "content": "Please provide 5 common questions about Hardie siding."}
            ],
            max_tokens=150,
        )
        generated_questions = response.choices[0].message.content.split('\n')
        return generated_questions if len(generated_questions) == 5 else default_questions
    except Exception as e:
        st.warning(f"Unable to generate questions using API: {str(e)}. Using default questions.")
        return default_questions

#def search_hardie_siding(query):
    # ... (keep the existing implementation)
def search_hardie_siding(query):
    try:
        result = exa_client.search_and_contents(
            f"Hardie Siding: {query}",
            num_results=3,
        )
        return '\n'.join([f"Result {i+1}: {item.title}\n{item.text[:200]}..." for i, item in enumerate(result.results)])
    except Exception as e:
        st.error(f"Error in search_hardie_siding: {str(e)}")
        return f"Unable to search for '{query}' due to an error."

#def get_file_id_from_folder(folder_id, file_name):
    # ... (keep the existing implementation)
def get_file_id_from_folder(folder_id, file_name):
    """Retrieve file ID from Google Drive folder based on file name."""
    query = f"'{folder_id}' in parents and name = '{file_name}'"
    results = drive_service.files().list(q=query).execute()
    if 'files' in results and results['files']:
        return results['files'][0]['id']
    else:
        return None
#def get_google_doc_content(doc_id):
    # ... (keep the existing implementation)
def get_google_doc_content(doc_id):
    """Retrieve content from a Google Doc."""
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = ""
    for item in doc.get('body', {}).get('content', []):
        if 'paragraph' in item:
            elements = item.get('paragraph', {}).get('elements', [])
            for element in elements:
                if 'textRun' in element:
                    content += element.get('textRun', {}).get('content', '')
    return content

#adding def google doc by address from edit suggestion 9 16 @1037am
def get_google_doc_by_address(address):
    try:
        query = f"'{FOLDER_ID}' in parents and name contains '{address}'"
        
        results = drive_service.files().list(q=query).execute()
        files = results.get('files', [])
        
        if not files:
            return f"No document found for address: {address}"
        file_id = files[0]['id']
        file_name = files[0]['name']
        
        if file_name.endswith('.txt'):
            file = drive_service.files().get_media(fileId=file_id).execute()
            doc_content = file.decode('utf-8')
        else:
            doc_content = get_google_doc_content(file_id)
        
        if not doc_content:
            return "No content found in the document."
        
        return doc_content
    except Exception as e:
        return f"Unable to retrieve document for address '{address}' due to an error: {str(e)}"

#def test_google_drive_access():
    # ... (keep the existing implementation)
def test_google_drive_access():
    try:
        folder_id = '1Knd9Wk7pMSZue2mdgZZQtQfy1waUeLXH'
        query = f"'{folder_id}' in parents"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        st.write(f"Found {len(files)} files in the specified folder:")
        for file in files:
            st.write(f"File name: {file['name']}")  # Removed File ID from here

        return len(files) > 0
    except Exception as e:
        st.error(f"Error testing Google Drive access: {str(e)}")
        st.error(f"Credentials info: {creds.to_json()[:100]}...")  # Show first 100 chars of credentials
        return False
def siding_project_agent(user_question, search_results, cold_email, google_doc_content):
    if user_question.lower() == 'exit':
        st.write("Exiting the program.")
        return

    combined_input = f"User Question: {user_question}\nRelevant Information: {search_results}\n{google_doc_content}"

    try:
        response = together_client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert siding installer specializing in James Hardie siding and CertainTeed products. 
                    Provide concise, first-person responses. Focus on answering the user's question directly.
                    Compare and contrast Hardie and CertainTeed products when relevant. 
                    Avoid repetition and keep your answer under 300 words. If you're unsure about something, 
                    it's okay to say so. Offer to provide more details if the user wants them."""
                },
                {
                    "role": "user",
                    "content": combined_input
                }
            ],
            max_tokens=500,
            temperature=0.7,
        )
        st.write(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error in siding_project_agent: {str(e)}")
        st.write("I apologize, but I'm having trouble processing your request at the moment. Please try again or rephrase your question.")


# def siding_project_agent(user_question, search_results, cold_email, google_doc_content):
#     if user_question.lower() == 'exit':
#         st.write("Exiting the program.")
#         return

#     combined_input = f"User Question: {user_question}\nRelevant Information: {search_results}\n{google_doc_content}"

#     try:
#         response = together_client.chat.completions.create(
#             model="mistralai/Mixtral-8x7B-Instruct-v0.1",  # Changed to Mixtral model
#             messages=[
#                 {
#                     "role": "system",
#                     "content": """You are an expert James Hardie siding installer speaking directly to a customer. 
#                     Provide concise, first-person responses. Focus on answering the user's question directly.
#                     Avoid repetition and keep your answer above under 300 words. If you're unsure about something, 
#                     it's okay to say so. Offer to provide more details if the user wants them."""
#                 },
#                 {
#                     "role": "user",
#                     "content": combined_input
#                 }
#             ],
#             max_tokens=500,
#             temperature=0.7,
#         )
#         st.write(response.choices[0].message.content)
#     except Exception as e:
#         st.error(f"Error in siding_project_agent: {str(e)}")
#         st.write("I apologize, but I'm having trouble processing your request at the moment. Please try again or rephrase your question.")


def answer_question(question, common_questions, search_results, google_doc_content, hardie_url=None, certainteed_url=None):
    try:
        hardie_content = scrape_specific_url(hardie_url) if hardie_url else ""
        certainteed_content = scrape_certainteed(certainteed_url) if certainteed_url else ""
        
        # Use siding_project_agent for more interactive responses
        siding_project_agent(question, search_results, "", google_doc_content)
        
        # If siding_project_agent doesn't provide a response, fall back to the original method
        if not st.session_state.get('response_generated'):
            prompt = f"""
            I am an expert on siding, including Hardie Siding and CertainTeed products. I'm here to help you with your question. Based on the information I have, here is my response:

            Common Questions:
            {common_questions}

            Search Results:
            {search_results}

            Google Doc Content:
            {google_doc_content}

            Hardie Siding Content:
            {hardie_content}

            CertainTeed Content:
            {certainteed_content}

            User Question: {question}

            Let me provide you with a detailed and helpful answer based on what I know about both Hardie Siding and CertainTeed products.
            """

            response = groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful sales associate and expert installer specializing in various siding products, including Hardie Siding and CertainTeed."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
            )
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error in answer_question: {str(e)}")
        return f"Unable to answer the question '{question}' due to an error."

# def answer_question(question, common_questions, search_results, google_doc_content, url=None):
#     try:
#         scraped_content = scrape_specific_url(url) if url else ""
        
#         # Use siding_project_agent for more interactive responses
#         siding_project_agent(question, search_results, "", google_doc_content)
        
#         # If siding_project_agent doesn't provide a response, fall back to the original method
#         if not st.session_state.get('response_generated'):
#             prompt = f"""
#             I am an expert on Hardie Siding, and I'm here to help you with your question. Based on the information I have, here is my response:

#             Common Questions:
#             {common_questions}

#             Search Results:
#             {search_results}

#             Google Doc Content:
#             {google_doc_content}

#             Scraped Content:
#             {scraped_content}

#             User Question: {question}

#             Let me provide you with a detailed and helpful answer based on what I know.
#             """

#             response = groq_client.chat.completions.create(
#                 model="llama-3.1-70b-versatile",
#                 messages=[
#                     {"role": "system", "content": "You are a helpful sales associate and expert hardie installer specializing in Hardie Siding."},
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=500,
#             )
#             return response.choices[0].message.content
#     except Exception as e:
#         st.error(f"Error in answer_question: {str(e)}")
#         return f"Unable to answer the question '{question}' due to an error."

def cold_email_agent(target, search_results):
    # Combine all search results into a single string
    combined_results = "\n".join(search_results)
    response = together_client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        messages=[
            {
                "role": "system",
                "content": """You are an expert james hardie siding installer.
                Your task is to write concise and personalized anwers to the most common questions about James Hardie Siding that Market Research given to you.
                Make sure to utilize all 4 areas of the research I(What are the most common topics covered in James Hardie siding video transcripts, How does James Hardie siding solve the problem of exterior home damage,
                What are the most common questions homeowners face when deciding to use James Hardie siding for their homes, and What are the definitions of key terms related to James Hardie siding used in video transcripts)
                Focus on describing what the target avatar will get, add an opportunity for customers to ask questions about their home.
                Keep the information concise and use plain English.
                DO NOT OUTPUT ANY OTHER TEXT !!! ONLY THE COLD EMAIL ITSELF!.
                """
            },
            {
                "role": "user",
                "content": f"Here is the target avatar: {target} \n Here is the market research: #### {combined_results} #### ONLY OUTPUT THE EMAIL ITSELF. NO OTHER TEXT!!"
            }
        ],
        max_tokens=500,
        temperature=0.1,
        top_p=1,
        top_k=50,
        repetition_penalty=1,
        stop=["<|eot_id|>"]
    )
    return response.choices[0].message.content

def main():
    st.title("Siding Project Assistant")

    # Get user address and retrieve Google Doc content
    user_address = st.text_input("Please enter your address:")
    if user_address:
        google_doc_content = get_google_doc_by_address(user_address)
    else:
        google_doc_content = ""

    # Get user input for search query
    user_input = st.text_input("Enter your question about siding:")

    # Get CertainTeed URL input
    certainteed_url = st.text_input("Enter a specific CertainTeed URL (optional):")

    if user_input:
        # Generate queries based on the user input
        generated_queries = get_common_questions()  # You might want to modify this to generate queries based on user input

        # Perform web searches for each query
        search_results = [search_hardie_siding(query) for query in generated_queries]

        # Generate a cold email based on the user input and search results
        cold_email = cold_email_agent(user_input, search_results)

        # Call the answer_question function with the retrieved Google Doc content and CertainTeed URL
        answer = answer_question(user_input, generated_queries, search_results, google_doc_content, certainteed_url=certainteed_url)
        st.write(answer)

    # New feature: Generate video transcript
    st.write("---")
    st.write("Generate new video transcript for new client")
    if st.button("Click Here"):
        folder_id = '1Knd9Wk7pMSZue2mdgZZQtQfy1waUeLXH'  # Your Google Drive folder ID
        new_transcript = video_transcript_agent(folder_id)
        st.write("New Video Transcript Template:")
        st.text_area("Generated Transcript", new_transcript, height=300)

if __name__ == "__main__":
    main()

# def main():
#     st.title("Hardie Siding Project Assistant")

#     # Get user address and retrieve Google Doc content
#     user_address = st.text_input("Please enter your address:")
#     if user_address:
#         google_doc_content = get_google_doc_by_address(user_address)
#     else:
#         google_doc_content = ""

#     # Get user input for search query
#     user_input = st.text_input("Enter your question about Hardie siding:")

#     if user_input:
#         # Generate queries based on the user input
#         generated_queries = get_common_questions()  # You might want to modify this to generate queries based on user input

#         # Perform web searches for each query
#         search_results = [search_hardie_siding(query) for query in generated_queries]

#         # Generate a cold email based on the user input and search results
#         cold_email = cold_email_agent(user_input, search_results)

#         # Call the siding_project_agent function with the retrieved Google Doc content
#         siding_project_agent(user_input, search_results, cold_email, google_doc_content)

#     # New feature: Generate video transcript
#     st.write("---")
#     st.write("Generate new video transcript for new client")
#     if st.button("Click Here"):
#         folder_id = '1Knd9Wk7pMSZue2mdgZZQtQfy1waUeLXH'  # Your Google Drive folder ID
#         new_transcript = video_transcript_agent(folder_id)
#         st.write("New Video Transcript Template:")
#         st.text_area("Generated Transcript", new_transcript, height=300)

# if __name__ == "__main__":
#     main()
