import PyPDF2
import io
import os
import tempfile

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    text = ""
    
    try:
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return None

def extract_text_from_pdf_bytes(pdf_bytes):
    """
    Extract text content from PDF bytes (for Streamlit file uploader).
    
    Args:
        pdf_bytes (bytes): PDF file as bytes
        
    Returns:
        str: Extracted text content
    """
    text = ""
    
    try:
        # Create a file-like object from bytes
        file = io.BytesIO(pdf_bytes)
        
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Get the number of pages
        num_pages = len(pdf_reader.pages)
        
        # Extract text from each page
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
            
        return text
    except Exception as e:
        print(f"Error extracting text from PDF bytes: {str(e)}")
        return None

def save_uploaded_pdf(uploaded_file):
    """
    Save an uploaded PDF file to a temporary location.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        str: Path to the saved PDF file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        
        # Write the uploaded file to the temporary file
        temp_file.write(uploaded_file.getbuffer())
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        print(f"Error saving uploaded PDF: {str(e)}")
        return None
