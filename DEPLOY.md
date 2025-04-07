# Deployment Guide for Knowledge Vault

This guide will help you deploy the Knowledge Vault application so everyone can access it.

## GitHub Deployment

1. **Fork the Repository**:
   - Click the 'Fork' button at the top right of the repository page to create your own copy.

2. **Enable GitHub Pages**:
   - Go to your repository Settings > Pages
   - Select the 'main' branch and the root folder as the source
   - Click 'Save'

3. **Configure Streamlit Cloud Deployment**:
   - Sign up for [Streamlit Cloud](https://streamlit.io/cloud)
   - Connect your GitHub account
   - Select the forked repository
   - Choose `app.py` as the main file
   - Click 'Deploy'

## Requirements

Make sure your deployment environment has the following packages installed:
- streamlit>=1.22.0
- beautifulsoup4>=4.11.1
- faiss-cpu>=1.7.2
- numpy>=1.22.3
- pandas>=1.4.2
- plotly>=5.6.0
- pypdf2>=2.10.5
- pytrends>=4.8.0
- trafilatura>=1.2.2
- torch>=1.12.0

## Local Deployment

To run the application locally:

```bash
# Clone the repository
git clone https://github.com/yourusername/knowledge-vault.git
cd knowledge-vault

# Install dependencies
pip install streamlit beautifulsoup4 faiss-cpu numpy pandas plotly pypdf2 pytrends trafilatura torch

# Run the application
streamlit run app.py
```

The application will be available at http://localhost:8501.

## Offline Mode

The Knowledge Vault supports an offline mode that allows users to work with their stored knowledge without internet connectivity. Toggle this option in the sidebar.

## Mobile Compatibility

The Knowledge Vault is fully responsive and works on mobile devices through any modern web browser.

## Data Management

User data is stored locally in the `data/` directory by default. For cloud deployments, this data will be ephemeral unless you configure persistent storage.