import os
import streamlit as st
import pandas as pd
import time
from pathlib import Path

# Import utility modules
from utils.scraper import scrape_content, get_trending_topics
from utils.summarizer import summarize_text, generate_embeddings, answer_question
from utils.database import (
    VectorDB, create_or_load_vector_db, add_to_vector_db, 
    search_vector_db, get_all_topics
)
from utils.pdf_processor import extract_text_from_pdf
from utils.quiz_generator import generate_flashcards, generate_quiz
from utils.visualization import create_timeline_chart, create_knowledge_network

# Create data directory if it doesn't exist
Path("data").mkdir(exist_ok=True)

# App title and configuration
st.set_page_config(
    page_title="Knowledge Vault",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
def load_css():
    css = """
    <style>
    /* Main styles for the Knowledge Vault */
    
    /* Gradient background for headers */
    .block-container {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Card-like styling */
    div.element-container {
        border-radius: 8px;
        transition: transform 0.3s ease;
    }
    
    div.element-container:hover {
        transform: translateY(-2px);
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: bold;
        border-radius: 8px;
    }
    
    /* Custom styling for results */
    .topic-header {
        font-size: 18px;
        font-weight: bold;
        color: #FF4B4B;
        margin-bottom: 10px;
    }
    
    /* Glow effect for important elements */
    .glow-effect {
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .main-content {
        animation: fadeIn 0.5s ease-in-out;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_css()

# Initialize session state variables
if "db" not in st.session_state:
    st.session_state.db = create_or_load_vector_db()
if "user_profile" not in st.session_state:
    st.session_state.user_profile = "default"
if "offline_mode" not in st.session_state:
    st.session_state.offline_mode = False
if "topics" not in st.session_state:
    st.session_state.topics = get_all_topics(st.session_state.db)

# Sidebar for app navigation
st.sidebar.markdown("<div style='text-align: center;'><h1 style='color: #FF4B4B;'>Knowledge Vault 🧠</h1></div>", unsafe_allow_html=True)
# Display a brain icon emoji instead of the SVG
st.sidebar.markdown("<div style='text-align: center; font-size: 80px;'>🧠</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center;'><h4>Your Offline AI-Powered Knowledge Manager</h4></div>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# User profile selection
user_profiles = ["default"] + [f.name for f in Path("data").glob("*") if f.is_dir() and f.name != "default"]
selected_profile = st.sidebar.selectbox("Select User Profile:", user_profiles)

# Create new profile option
new_profile = st.sidebar.text_input("Create New Profile:")
if st.sidebar.button("Create Profile") and new_profile and new_profile not in user_profiles:
    Path(f"data/{new_profile}").mkdir(exist_ok=True)
    st.session_state.user_profile = new_profile
    st.rerun()

if selected_profile != st.session_state.user_profile:
    st.session_state.user_profile = selected_profile
    st.session_state.db = create_or_load_vector_db(profile=selected_profile)
    st.session_state.topics = get_all_topics(st.session_state.db)
    st.rerun()

# Offline mode toggle
offline_mode = st.sidebar.checkbox("Offline Mode", value=st.session_state.offline_mode)
if offline_mode != st.session_state.offline_mode:
    st.session_state.offline_mode = offline_mode
    st.rerun()

# App navigation
page = st.sidebar.radio(
    "Navigation:",
    ["Search & Learn", "Add Content", "My Knowledge", "Question & Answer", "Study Tools", "Research Assistant"]
)

# Main content area
if page == "Search & Learn":
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Search & Learn 🔍</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Explore and discover new knowledge</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Enter a topic to search or learn about:")
        
        if search_query:
            with st.spinner("Searching for information..."):
                # First check if we have this in our database
                search_results = search_vector_db(st.session_state.db, search_query, top_k=5)
                
                if search_results and len(search_results) > 0:
                    st.success("Found relevant information in your Knowledge Vault!")
                    
                    for i, result in enumerate(search_results):
                        with st.expander(f"{result['topic']} - Score: {round(result['score'], 2)}", expanded=i==0):
                            st.write(result["content"])
                            st.caption(f"Source: {result['source']}")
                            st.caption(f"Added on: {result['date']}")
                
                # If offline mode is disabled, offer to search online
                if not st.session_state.offline_mode and st.button("Search Online"):
                    try:
                        # First try Wikipedia
                        content = scrape_content(search_query, source="wikipedia")
                        if not content:
                            # Try general web search if Wikipedia fails
                            content = scrape_content(search_query, source="web")
                        
                        if content:
                            # Summarize the content
                            summary = summarize_text(content)
                            
                            st.subheader(f"Summary of {search_query}")
                            st.write(summary)
                            
                            # Save to knowledge base option
                            if st.button("Save to Knowledge Vault"):
                                # Generate embeddings and save
                                with st.spinner("Saving to Knowledge Vault..."):
                                    add_to_vector_db(
                                        st.session_state.db,
                                        topic=search_query,
                                        content=summary,
                                        source=f"Web search - {time.strftime('%Y-%m-%d')}",
                                        profile=st.session_state.user_profile
                                    )
                                    st.session_state.topics = get_all_topics(st.session_state.db)
                                st.success("Added to Knowledge Vault!")
                        else:
                            st.warning("Couldn't find information online. Try a different search term.")
                    except Exception as e:
                        st.error(f"Error searching online: {str(e)}")

    with col2:
        st.subheader("Trending Topics")
        if not st.session_state.offline_mode:
            try:
                trending = get_trending_topics()
                for topic in trending[:10]:
                    if st.button(topic):
                        # Set the search query to this trending topic
                        search_query = topic
                        st.rerun()
            except Exception as e:
                st.write("Trending topics unavailable")
                st.caption("Enable online mode to see trending topics")
        else:
            st.write("Trending topics unavailable in offline mode")

elif page == "Add Content":
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Add Content to Knowledge Vault ➕</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Import information from various sources</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["URL", "PDF Upload", "Manual Entry"])
    
    with tab1:
        st.subheader("Add Content from URL")
        url = st.text_input("Enter URL to scrape:")
        url_topic = st.text_input("Topic Name (for organizing):")
        
        if st.button("Scrape and Add") and url and url_topic:
            if st.session_state.offline_mode:
                st.error("Cannot scrape URLs in offline mode")
            else:
                with st.spinner("Scraping content..."):
                    try:
                        content = scrape_content(url, source="url")
                        if content:
                            # Summarize the content
                            summary = summarize_text(content)
                            
                            st.subheader("Content Summary")
                            st.write(summary)
                            
                            # Confirm adding to knowledge base
                            if st.button("Confirm and Save"):
                                with st.spinner("Saving to Knowledge Vault..."):
                                    add_to_vector_db(
                                        st.session_state.db,
                                        topic=url_topic,
                                        content=summary,
                                        source=url,
                                        profile=st.session_state.user_profile
                                    )
                                    st.session_state.topics = get_all_topics(st.session_state.db)
                                st.success("Added to Knowledge Vault!")
                        else:
                            st.error("Failed to extract content from the URL")
                    except Exception as e:
                        st.error(f"Error scraping URL: {str(e)}")
    
    with tab2:
        st.subheader("Upload PDF")
        pdf_file = st.file_uploader("Upload PDF file", type=["pdf"])
        pdf_topic = st.text_input("PDF Topic Name (for organizing):")
        
        if pdf_file is not None and pdf_topic:
            with st.spinner("Processing PDF..."):
                try:
                    # Save PDF temporarily
                    temp_pdf_path = f"data/temp_{pdf_file.name}"
                    with open(temp_pdf_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    
                    # Extract text from PDF
                    pdf_text = extract_text_from_pdf(temp_pdf_path)
                    
                    # Remove temporary file
                    os.remove(temp_pdf_path)
                    
                    if pdf_text:
                        # Summarize the content
                        summary = summarize_text(pdf_text)
                        
                        st.subheader("PDF Content Summary")
                        st.write(summary)
                        
                        # Confirm adding to knowledge base
                        if st.button("Save PDF Content"):
                            with st.spinner("Saving to Knowledge Vault..."):
                                add_to_vector_db(
                                    st.session_state.db,
                                    topic=pdf_topic,
                                    content=summary,
                                    source=f"PDF: {pdf_file.name}",
                                    profile=st.session_state.user_profile
                                )
                                st.session_state.topics = get_all_topics(st.session_state.db)
                            st.success("Added to Knowledge Vault!")
                    else:
                        st.error("Failed to extract text from PDF")
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
    
    with tab3:
        st.subheader("Manual Entry")
        manual_topic = st.text_input("Topic Name:")
        manual_content = st.text_area("Content:", height=300)
        manual_source = st.text_input("Source (optional):", "Manual Entry")
        
        if st.button("Save Manual Entry") and manual_topic and manual_content:
            with st.spinner("Saving to Knowledge Vault..."):
                try:
                    add_to_vector_db(
                        st.session_state.db,
                        topic=manual_topic,
                        content=manual_content,
                        source=manual_source,
                        profile=st.session_state.user_profile
                    )
                    st.session_state.topics = get_all_topics(st.session_state.db)
                    st.success("Added to Knowledge Vault!")
                except Exception as e:
                    st.error(f"Error saving entry: {str(e)}")

elif page == "My Knowledge":
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>My Knowledge Base 📖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Browse and manage your stored knowledge</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Show a list of topics in the knowledge base
    if not st.session_state.topics:
        st.info("Your Knowledge Vault is empty. Add some content to get started!")
    else:
        # Display timeline visualization
        st.subheader("Knowledge Timeline")
        timeline_chart = create_timeline_chart(st.session_state.db, st.session_state.user_profile)
        st.plotly_chart(timeline_chart, use_container_width=True)
        
        # List all topics
        st.subheader("All Topics")
        topic_filter = st.text_input("Filter topics:", "")
        
        filtered_topics = [topic for topic in st.session_state.topics 
                          if topic.lower().find(topic_filter.lower()) != -1]
        
        for topic in filtered_topics:
            with st.expander(topic):
                # Get the full content for this topic
                results = search_vector_db(st.session_state.db, topic, exact_match=True)
                for result in results:
                    st.write(result["content"])
                    st.caption(f"Source: {result['source']}")
                    st.caption(f"Added on: {result['date']}")
                    
                    # Delete option
                    if st.button(f"Delete '{topic}'"):
                        st.session_state.db.delete_by_topic(topic)
                        st.session_state.topics = get_all_topics(st.session_state.db)
                        st.success(f"Deleted topic: {topic}")
                        st.rerun()

elif page == "Question & Answer":
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Ask Questions About Your Knowledge 🤔</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Get answers based on your personal knowledge base</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    question = st.text_input("Ask a question about your stored knowledge:")
    
    if question:
        with st.spinner("Searching for an answer..."):
            try:
                answer = answer_question(st.session_state.db, question)
                
                st.subheader("Answer")
                st.write(answer["answer"])
                
                with st.expander("View Source Information"):
                    st.write(answer["context"])
                    st.caption(f"Source: {answer['source']}")
                    st.caption(f"Topic: {answer['topic']}")
                    
                # Add speech synthesis option
                if st.button("Read Answer Aloud"):
                    with st.spinner("Generating speech..."):
                        # Using JavaScript to use the Web Speech API for TTS
                        # Using JavaScript to use the Web Speech API for TTS
                        # Escape the answer text safely for JavaScript
                        escaped_answer = answer["answer"].replace("'", "''")
                        js_code = f"""
                        <script>
                        function speak() {{
                            const speech = new SpeechSynthesisUtterance('{escaped_answer}');
                            window.speechSynthesis.speak(speech);
                        }}
                        speak();
                        </script>
                        """
                        st.components.v1.html(js_code)
            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")

elif page == "Study Tools":
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Study Tools 📝</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Create flashcards and quizzes to test your knowledge</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Flashcards", "Quizzes"])
    
    with tab1:
        st.subheader("Generate Flashcards")
        
        flashcard_topic = st.selectbox("Select a topic for flashcards:", st.session_state.topics if st.session_state.topics else ["No topics available"])
        num_cards = st.slider("Number of flashcards:", 3, 15, 5)
        
        if st.button("Generate Flashcards") and flashcard_topic != "No topics available":
            with st.spinner("Generating flashcards..."):
                try:
                    # Get content for the selected topic
                    topic_content = search_vector_db(st.session_state.db, flashcard_topic, exact_match=True)
                    
                    if topic_content:
                        # Generate flashcards
                        flashcards = generate_flashcards(topic_content[0]["content"], num_cards)
                        
                        # Display flashcards
                        st.subheader(f"Flashcards for {flashcard_topic}")
                        
                        for i, card in enumerate(flashcards):
                            with st.expander(f"Card {i+1}: {card['question']}"):
                                st.write("**Answer:**")
                                st.write(card["answer"])
                    else:
                        st.warning(f"No content found for topic: {flashcard_topic}")
                except Exception as e:
                    st.error(f"Error generating flashcards: {str(e)}")
    
    with tab2:
        st.subheader("Generate Quiz")
        
        quiz_topic = st.selectbox("Select a topic for quiz:", st.session_state.topics if st.session_state.topics else ["No topics available"])
        num_questions = st.slider("Number of questions:", 3, 10, 5)
        
        if st.button("Generate Quiz") and quiz_topic != "No topics available":
            with st.spinner("Generating quiz..."):
                try:
                    # Get content for the selected topic
                    topic_content = search_vector_db(st.session_state.db, quiz_topic, exact_match=True)
                    
                    if topic_content:
                        # Generate quiz
                        quiz = generate_quiz(topic_content[0]["content"], num_questions)
                        
                        # Display quiz
                        st.subheader(f"Quiz for {quiz_topic}")
                        
                        # Store correct answers
                        correct_answers = []
                        user_answers = []
                        
                        for i, question in enumerate(quiz):
                            st.write(f"**Question {i+1}:** {question['question']}")
                            
                            # Store the correct answer
                            correct_answers.append(question['correct_answer'])
                            
                            # Display options
                            options = question['options']
                            user_choice = st.radio(f"Select answer for question {i+1}:", options, key=f"q{i}")
                            user_answers.append(user_choice)
                            
                            st.write("---")
                        
                        # Check answers button
                        if st.button("Check Answers"):
                            score = sum([1 for u, c in zip(user_answers, correct_answers) if u == c])
                            
                            st.success(f"Your score: {score}/{len(quiz)} ({score/len(quiz)*100:.1f}%)")
                            
                            # Show correct answers
                            st.subheader("Correct Answers")
                            for i, (question, correct, user) in enumerate(zip(quiz, correct_answers, user_answers)):
                                if user == correct:
                                    st.write(f"✅ Question {i+1}: {correct}")
                                else:
                                    st.write(f"❌ Question {i+1}: Your answer: {user}, Correct: {correct}")
                    else:
                        st.warning(f"No content found for topic: {quiz_topic}")
                except Exception as e:
                    st.error(f"Error generating quiz: {str(e)}")

elif page == "Research Assistant":
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Research Assistant 🔬</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em;'>Professional tools for academic and advanced research</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    tabs = st.tabs(["Literature Review", "Citation Generator", "Research Notes", "Concept Map"])
    
    with tabs[0]:  # Literature Review
        st.subheader("Literature Review Assistant")
        
        lit_review_query = st.text_area("Enter your research topic or question:", height=100, 
                                       placeholder="E.g., 'Impact of artificial intelligence on healthcare delivery systems'")
        
        col1, col2 = st.columns(2)
        with col1:
            min_sources = st.number_input("Minimum sources to include:", min_value=3, max_value=20, value=5)
        with col2:
            include_recent = st.checkbox("Prioritize recent sources", value=True)
        
        if st.button("Generate Literature Review") and lit_review_query:
            with st.spinner("Analyzing knowledge base and generating literature review..."):
                # Get relevant content from the knowledge base
                results = search_vector_db(st.session_state.db, lit_review_query, top_k=min_sources)
                
                if results and len(results) > 0:
                    st.success(f"Found {len(results)} relevant sources in your Knowledge Vault")
                    
                    # Prepare the literature review
                    st.subheader("Literature Review")
                    
                    # Introduction
                    st.markdown("### Introduction")
                    st.write(f"This literature review examines the research topic: **{lit_review_query}**. " 
                            f"Based on {len(results)} sources from the knowledge vault, this review synthesizes " 
                            f"key findings and identifies patterns across the literature.")
                    
                    # Main body with sources grouped by themes (simplified)
                    st.markdown("### Key Findings")
                    
                    # Get content by theme (just using topics as simple proxies for themes)
                    topics = list(set([r['topic'] for r in results]))
                    
                    for i, topic in enumerate(topics):
                        sources_in_topic = [r for r in results if r['topic'] == topic]
                        if sources_in_topic:
                            st.markdown(f"#### Theme {i+1}: {topic}")
                            for source in sources_in_topic:
                                # Get a summarized version for the literature review
                                summary = source['content'][:500] + "..." if len(source['content']) > 500 else source['content']
                                st.markdown(f"**Source: {source['source']}**")
                                st.write(summary)
                                st.caption(f"Added on: {source['date']}")
                                st.markdown("---")
                    
                    # Conclusion (simplified)
                    st.markdown("### Conclusion and Research Gaps")
                    st.write("This literature review highlights several important aspects of the research topic. "
                           "Further research may be needed to address gaps in the current knowledge base.")
                    
                    # Export option
                    if st.button("Export Literature Review"):
                        st.download_button(
                            label="Download as Text",
                            data="Literature Review: " + lit_review_query + "\n\n" + 
                                 "\n\n".join([f"Source: {r['source']}\n{r['content']}" for r in results]),
                            file_name="literature_review.txt",
                            mime="text/plain",
                        )
                else:
                    st.warning("Not enough relevant sources found in your Knowledge Vault. Try adding more content or refining your query.")
                    if not st.session_state.offline_mode:
                        st.info("Consider searching online for more sources using the 'Search & Learn' feature.")
    
    with tabs[1]:  # Citation Generator
        st.subheader("Citation Generator")
        
        # Source input
        source_type = st.selectbox("Source Type:", ["Journal Article", "Book", "Website", "Conference Paper"])
        
        # Common fields
        title = st.text_input("Title:")
        year = st.text_input("Year:")
        
        if source_type == "Journal Article":
            authors = st.text_input("Authors (comma separated):")
            journal = st.text_input("Journal:")
            volume = st.text_input("Volume:")
            issue = st.text_input("Issue:")
            pages = st.text_input("Pages:")
            doi = st.text_input("DOI (if available):")
            
        elif source_type == "Book":
            authors = st.text_input("Authors/Editors (comma separated):")
            publisher = st.text_input("Publisher:")
            place = st.text_input("Place of Publication:")
            edition = st.text_input("Edition (if not first):")
            
        elif source_type == "Website":
            authors = st.text_input("Authors/Organization (if known):")
            website = st.text_input("Website Name:")
            url = st.text_input("URL:")
            accessed = st.date_input("Date Accessed:")
            
        elif source_type == "Conference Paper":
            authors = st.text_input("Authors (comma separated):")
            conference = st.text_input("Conference Name:")
            location = st.text_input("Conference Location:")
            pages = st.text_input("Pages (if available):")
        
        # Citation style
        citation_style = st.selectbox("Citation Style:", ["APA", "MLA", "Chicago", "Harvard"])
        
        if st.button("Generate Citation") and title and year:
            st.subheader("Generated Citation")
            
            # Very basic citation formatting (would be more sophisticated in a real app)
            if citation_style == "APA":
                if source_type == "Journal Article":
                    author_list = [a.strip() for a in authors.split(",")]
                    author_text = ", ".join(author_list[:-1]) + " & " + author_list[-1] if len(author_list) > 1 else authors
                    citation = f"{author_text}. ({year}). {title}. *{journal}*, *{volume}*({issue}), {pages}."
                    if doi:
                        citation += f" https://doi.org/{doi}"
                elif source_type == "Book":
                    author_list = [a.strip() for a in authors.split(",")]
                    author_text = ", ".join(author_list[:-1]) + " & " + author_list[-1] if len(author_list) > 1 else authors
                    edition_text = f" ({edition} ed.)" if edition else ""
                    citation = f"{author_text}. ({year}). *{title}*{edition_text}. {publisher}."
                elif source_type == "Website":
                    citation = f"{authors}. ({year}). {title}. *{website}*. Retrieved {accessed.strftime('%B %d, %Y')}, from {url}"
                elif source_type == "Conference Paper":
                    author_list = [a.strip() for a in authors.split(",")]
                    author_text = ", ".join(author_list[:-1]) + " & " + author_list[-1] if len(author_list) > 1 else authors
                    citation = f"{author_text}. ({year}). {title}. *{conference}*, {location}."
            # Add other citation styles similarly (MLA, Chicago, Harvard)
            else:
                citation = f"Citation in {citation_style} format would be generated here."
            
            st.markdown(f"```\n{citation}\n```")
            
            # Add to knowledge base option
            if st.button("Save to Knowledge Vault"):
                with st.spinner("Saving citation..."):
                    add_to_vector_db(
                        st.session_state.db,
                        topic=f"Citation: {title}",
                        content=f"Citation: {citation}\n\nDetails:\nType: {source_type}\nYear: {year}\nTitle: {title}",
                        source="Citation Generator",
                        profile=st.session_state.user_profile
                    )
                    st.session_state.topics = get_all_topics(st.session_state.db)
                    st.success("Citation saved to Knowledge Vault!")
    
    with tabs[2]:  # Research Notes
        st.subheader("Research Notes Organizer")
        
        # Create a new note
        note_title = st.text_input("Note Title:")
        note_content = st.text_area("Note Content:", height=200)
        note_tags = st.text_input("Tags (comma separated):")
        
        if st.button("Save Research Note") and note_title and note_content:
            with st.spinner("Saving research note..."):
                # Format tags
                formatted_tags = ", ".join([tag.strip() for tag in note_tags.split(",")])
                
                # Add metadata
                note_with_metadata = f"# {note_title}\n\n"
                note_with_metadata += f"**Date:** {time.strftime('%Y-%m-%d')}\n"
                note_with_metadata += f"**Tags:** {formatted_tags}\n\n"
                note_with_metadata += note_content
                
                # Save to database
                add_to_vector_db(
                    st.session_state.db,
                    topic=f"Research Note: {note_title}",
                    content=note_with_metadata,
                    source="Research Notes",
                    profile=st.session_state.user_profile
                )
                st.session_state.topics = get_all_topics(st.session_state.db)
                st.success("Research note saved!")
        
        # Search existing notes
        st.markdown("---")
        st.subheader("Find Existing Notes")
        
        note_search = st.text_input("Search your research notes:")
        
        if note_search:
            results = search_vector_db(st.session_state.db, note_search, top_k=10)
            research_notes = [r for r in results if "Research Note: " in r['topic']]
            
            if research_notes:
                st.success(f"Found {len(research_notes)} relevant research notes")
                for note in research_notes:
                    with st.expander(note['topic'].replace("Research Note: ", "")):
                        st.markdown(note['content'])
                        st.caption(f"Created on: {note['date']}")
            else:
                st.info("No matching research notes found.")
    
    with tabs[3]:  # Concept Map
        st.subheader("Knowledge Concept Map")
        
        st.markdown("This concept map visualizes the connections between topics in your Knowledge Vault.")
        st.info("The size of each node indicates the amount of information on that topic.")
        
        # Simple implementation - in a real application, this would be a more sophisticated
        # visualization with D3.js or a similar library
        if st.session_state.topics:
            # Create network visualization
            network_chart = create_knowledge_network(st.session_state.db)
            st.plotly_chart(network_chart, use_container_width=True)
            
            # Export option
            if st.button("Export Concept Map"):
                st.info("In a complete implementation, this would allow you to export the concept map as an image or interactive HTML file.")
        else:
            st.warning("Your Knowledge Vault is empty. Add some content to generate a concept map.")

# Show footer
st.sidebar.markdown("---")
st.sidebar.caption("Knowledge Vault - Powered by HuggingFace & Streamlit")
