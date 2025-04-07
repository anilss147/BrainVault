# 🧠 Knowledge Vault

An offline AI-powered Knowledge Vault built with Python and Streamlit that scrapes, summarizes, and stores information using open-source NLP models.

![Knowledge Vault](assets/knowledge.svg)

## ✨ Features

- **🔍 Search & Learn**: Search your personal knowledge base or scrape content from the web
- **➕ Add Content**: Import information from URLs, PDFs, or manual entry
- **📖 My Knowledge**: Browse and manage your stored knowledge with a visual timeline
- **🤔 Question & Answer**: Ask questions about your stored knowledge
- **📚 Study Tools**: Generate flashcards and quizzes to test your knowledge
- **🔬 Research Assistant**: Professional tools for academic and research work
  - 📄 Literature Review Assistant
  - 📝 Citation Generator
  - 📋 Research Notes Organizer
  - 🌐 Knowledge Concept Map
- **🔌 Offline Mode**: Full functionality without internet connection
- **👥 User Profiles**: Separate knowledge bases for different users or subjects
- **📱 Mobile Compatible**: Works on all devices

## Deployment Options

### Deploy on Streamlit Cloud (Easiest)

1. Fork this repository
2. Sign up at [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app, pointing to your forked repository and to app.py

### Deploy on GitHub Pages

1. Fork this repository
2. Enable GitHub Pages in repository settings
3. The GitHub Actions workflow will automatically deploy the app

### Deploy Locally

```bash
# Clone the repository
git clone https://github.com/yourusername/knowledge-vault.git
cd knowledge-vault

# Install dependencies
pip install streamlit beautifulsoup4 faiss-cpu numpy pandas plotly pypdf2 pytrends trafilatura torch

# Run the app
streamlit run app.py
```

## For Students & Professionals

The Knowledge Vault is designed to help you:

### For Students:
- Create study materials (flashcards, quizzes) from your notes
- Build a personal searchable knowledge base from lecture notes, PDFs, and websites
- Prepare for exams with the Question & Answer feature

### For Professionals:
- Keep track of research materials and generate literature reviews
- Organize citations and references
- Create concept maps to visualize knowledge connections
- Take and organize research notes with powerful search capabilities

## Technical Details

- Built with Python and Streamlit
- Stores knowledge in a vector database (FAISS)
- Uses open-source NLP models for summarization and embeddings
- Modular architecture for easy extension

## Mobile Compatibility

The app is fully responsive and works on mobile devices. Access it through any modern web browser.

---

© 2023-2025 Knowledge Vault