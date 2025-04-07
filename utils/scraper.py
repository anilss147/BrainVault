import requests
import trafilatura
import time
import random
from bs4 import BeautifulSoup
from pytrends.request import TrendReq

def scrape_content(query_or_url, source="wikipedia"):
    """
    Scrape content from various sources based on query or direct URL.
    
    Args:
        query_or_url (str): Search query or direct URL
        source (str): Source type: "wikipedia", "web", or "url"
        
    Returns:
        str: Scraped content text
    """
    
    if source == "wikipedia":
        return scrape_wikipedia(query_or_url)
    elif source == "web":
        return scrape_web(query_or_url)
    elif source == "url":
        return scrape_url(query_or_url)
    else:
        raise ValueError(f"Unknown source type: {source}")

def scrape_wikipedia(query):
    """
    Scrape content from Wikipedia based on query.
    
    Args:
        query (str): Search query
        
    Returns:
        str: Wikipedia article text
    """
    # Format query for Wikipedia URL
    formatted_query = query.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{formatted_query}"
    
    try:
        # First try direct URL
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_tables=True, include_links=True, include_images=False)
        
        # If direct URL failed, try search
        if not text:
            search_url = f"https://en.wikipedia.org/w/index.php?search={query.replace(' ', '+')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers)
            
            # If redirected to an article page
            if "Special:Search" not in response.url:
                downloaded = trafilatura.fetch_url(response.url)
                text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
            else:
                # If we're at the search results page, try to get the first result
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.select('.mw-search-result-heading a')
                
                if search_results:
                    first_result_link = search_results[0].get('href')
                    if first_result_link:
                        wiki_url = f"https://en.wikipedia.org{first_result_link}"
                        downloaded = trafilatura.fetch_url(wiki_url)
                        text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
        
        return text
    except Exception as e:
        print(f"Error scraping Wikipedia: {str(e)}")
        return None

def scrape_web(query):
    """
    Scrape content from general web search.
    
    Args:
        query (str): Search query
        
    Returns:
        str: Combined text from top search results
    """
    # First try to get content from DuckDuckGo
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('a', class_='result__url')
        
        all_text = []
        
        # Extract text from top 3 results
        for i, result in enumerate(results[:3]):
            if i >= 3:  # Limit to 3 results
                break
                
            link = result.get('href')
            if link and not link.startswith(('javascript:', 'mailto:')):
                try:
                    # Use the enhanced website text content function
                    text = get_website_text_content(link)
                    if text:
                        all_text.append(text)
                except Exception as e:
                    print(f"Error scraping result {i}: {str(e)}")
                    continue
                    
            # Add small delay between requests
            time.sleep(1)
                
        if all_text:
            return "\n\n---\n\n".join(all_text)
        else:
            return None
    except Exception as e:
        print(f"Error in web scraping: {str(e)}")
        return None

def get_website_text_content(url):
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    
    Some common website to crawl information from:
    MLB scores: https://www.mlb.com/scores/YYYY-MM-DD
    
    Args:
        url (str): The URL to extract content from
        
    Returns:
        str: Extracted text content, or None if failed
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        
        # Check if download was successful
        if not downloaded:
            print(f"Failed to download content from {url}")
            return None
            
        # Extract main content
        text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
        return text
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return None

def scrape_url(url):
    """
    Scrape content from a specific URL.
    
    Args:
        url (str): Direct URL to scrape
        
    Returns:
        str: Text content from URL
    """
    return get_website_text_content(url)

def get_trending_topics(country_code='US', count=10):
    """
    Get trending search topics using PyTrends.
    
    Args:
        country_code (str): Country code for trends
        count (int): Number of trending topics to return
        
    Returns:
        list: List of trending topic strings or empty list if fails
    """
    try:
        # Initialize PyTrends
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Get trending searches for specified country
        trending_searches_df = pytrends.trending_searches(pn=country_code)
        
        # Convert to list
        trending_topics = trending_searches_df[0].tolist()
        
        # Return specified number of topics
        return trending_topics[:count]
    except Exception as e:
        print(f"Error getting trending topics: {str(e)}")
        # Return empty list instead of fallback to avoid synthetic data
        return []
