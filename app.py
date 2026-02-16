import os
import json
import re
import subprocess
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from groq import Groq
from moviepy.editor import VideoFileClip
import tempfile
import uuid
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from data_store import (save_script_result, get_all_scripts, get_script_by_id, delete_script, get_stats,
                        create_user, authenticate_user, get_user_by_id)
import io

# Selenium removed for cloud deployment compatibility
SELENIUM_AVAILABLE = False

# Load environment variables
load_dotenv()

# Check if .env file exists (skip check if running on cloud with env vars)
if not os.path.exists('.env') and not os.getenv('GROQ_API_KEY'):
    print("\n" + "="*60)
    print("⚠️  ERROR: .env file not found!")
    print("="*60)
    print("\nPlease follow these steps:")
    print("1. Rename '.env.example' to '.env'")
    print("2. Edit .env and add your Groq API key")
    print("   Get free key at: https://console.groq.com")
    print("="*60 + "\n")
    exit(1)

# Check for API key
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key or groq_api_key == 'your_groq_api_key_here':
    print("\n" + "="*60)
    print("⚠️  ERROR: GROQ_API_KEY not configured!")
    print("="*60)
    print("\nPlease follow these steps:")
    print("1. Get your free API key at: https://console.groq.com")
    print("2. Open the .env file")
    print("3. Replace 'your_groq_api_key_here' with your actual key")
    print("="*60 + "\n")
    exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-' + str(uuid.uuid4()))

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Groq client
try:
    groq_client = Groq(api_key=groq_api_key)
except Exception as e:
    print("\n" + "="*60)
    print("⚠️  ERROR: Failed to initialize Groq client")
    print("="*60)
    print(f"\nError: {str(e)}")
    print("\nThis might be a Python version compatibility issue.")
    print("Recommended: Use Python 3.10 or 3.11 (you're using 3.14)")
    print("\nTo fix:")
    print("1. Install Python 3.11 from python.org")
    print("2. Reinstall dependencies: pip install -r requirements.txt")
    print("="*60 + "\n")
    input("Press Enter to exit...")
    exit(1)


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_current_user():
    """Get current user from session, create guest if none exists."""
    user_id = session.get('user_id')
    
    if user_id:
        user = get_user_by_id(user_id)
        if user:
            return user
    
    # Create a guest user
    guest_user = create_user(email='', password='', is_guest=True)
    session['user_id'] = guest_user['id']
    session['is_guest'] = True
    return guest_user


def require_auth(f):
    """Decorator to require authentication (guest or registered)."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        get_current_user()  # Ensures user exists
        return f(*args, **kwargs)
    return decorated_function


def is_instagram_url(url):
    """Check if the URL is a valid Instagram URL."""
    instagram_patterns = [
        r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[\w-]+',
        r'https?://(?:www\.)?instagram\.com/[\w.-]+/(?:p|reel|tv)/[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in instagram_patterns)


def download_instagram_video(url):
    """Download Instagram video using yt-dlp and return the file path."""
    try:
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'instagram_{unique_id}.mp4')
        
        # Use yt-dlp to download the video
        command = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--no-playlist',
            '--no-warnings',
            '--quiet',
            '-o', output_path,
            url
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise Exception(f"yt-dlp failed: {result.stderr}")
        
        if os.path.exists(output_path):
            return output_path
        else:
            raise Exception("Video file was not created")
    
    except subprocess.TimeoutExpired:
        raise Exception("Download timeout - video may be too large or network is slow")
    except FileNotFoundError:
        raise Exception("yt-dlp not found. Please install it: pip install yt-dlp")
    except Exception as e:
        raise Exception(f"Error downloading Instagram video: {str(e)}")


def normalize_url(url):
    """Normalize URL by adding protocol if missing and validating format."""
    url = url.strip()
    
    # Remove common prefixes that users might accidentally include
    url = url.replace('www.', '', 1) if url.startswith('www.') else url
    
    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Validate the URL
    parsed = urlparse(url)
    if not parsed.netloc:
        raise Exception("Invalid URL format. Please provide a valid domain (e.g., example.com)")
    
    return url


def try_fetch_about_page(base_url, headers):
    """Try to fetch common 'about' pages that might have more static content."""
    import requests
    from urllib.parse import urljoin
    
    about_paths = ['/about', '/about-us', '/about.html', '/company', '/who-we-are']
    
    for path in about_paths:
        try:
            about_url = urljoin(base_url, path)
            response = requests.get(about_url, headers=headers, timeout=10, allow_redirects=True)
            if response.status_code == 200 and len(response.text) > 500:
                return response
        except:
            continue
    
    return None


def scrape_with_selenium(url):
    """Scrape website using Selenium for JavaScript-rendered content."""
    if not SELENIUM_AVAILABLE:
        return None
    
    driver = None
    try:
        # Configure Chrome options for headless browsing
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize the driver with automatic ChromeDriver management
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        # Navigate to the URL
        driver.get(url)
        
        # Wait for body to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait a bit more for JavaScript to render
        import time
        time.sleep(3)
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        
        # Get the fully rendered HTML
        html_content = driver.page_source
        
        return html_content
    except Exception as e:
        print(f"Selenium scraping failed: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def scrape_website_with_js_wait(url, headers):
    """Try to scrape with a small delay to allow some JS to execute."""
    import time
    session = requests.Session()
    session.headers.update(headers)
    
    # Make multiple requests with delays
    for attempt in range(2):
        response = session.get(url, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        # Fix encoding issues - try to detect and set correct encoding
        # Check content type to ensure it's HTML
        content_type = response.headers.get('Content-Type', '').lower()
        
        # If it's not HTML, skip encoding fixes
        if 'text/html' in content_type or 'text/plain' in content_type or not content_type:
            # Try to get encoding from content-type header first
            if 'charset=' in content_type:
                try:
                    charset = content_type.split('charset=')[-1].split(';')[0].strip()
                    response.encoding = charset
                except:
                    pass
            elif response.encoding is None or response.encoding == 'ISO-8859-1':
                # Try to detect encoding from content
                response.encoding = response.apparent_encoding
        
        # Check if content seems loaded and is actually text (not binary garbage)
        try:
            text_content = response.text
            # Check if content looks like valid HTML/text (not binary)
            if len(text_content) > 1000:
                # Quick check: if more than 20% of chars are replacement chars, it's likely binary
                replacement_chars = text_content.count('�') + text_content.count('\ufffd')
                if replacement_chars < len(text_content) * 0.1:  # Less than 10% garbled
                    return response
        except:
            pass
        
        if attempt < 1:
            time.sleep(2)  # Wait before retry
    
    return response


def scrape_website_content(url):
    """Scrape website content and extract detailed information."""
    try:
        # Normalize and validate URL
        url = normalize_url(url)
        
        # Check if brotli is available for br encoding support
        try:
            import brotli
            accept_encoding = 'gzip, deflate, br'
        except ImportError:
            # If brotli not installed, don't request br encoding
            accept_encoding = 'gzip, deflate'
        
        # Add headers to mimic a real browser (more realistic headers)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': accept_encoding,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # Try HTTPS first, fallback to HTTP if needed
        response = None
        try:
            response = scrape_website_with_js_wait(url, headers)
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
            # If HTTPS fails, try HTTP
            if url.startswith('https://'):
                url_http = url.replace('https://', 'http://')
                try:
                    response = scrape_website_with_js_wait(url_http, headers)
                except Exception:
                    raise e  # Raise original error if HTTP also fails
        
        # Parse HTML - use response.text for proper encoding handling
        # If encoding detection failed, try common encodings
        try:
            html_text = response.text
        except UnicodeDecodeError:
            # Fallback: try decoding with different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    html_text = response.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Last resort: decode with errors ignored
                html_text = response.content.decode('utf-8', errors='ignore')
        
        # Check if content is garbled (binary/compressed not properly decoded)
        # Count replacement characters and other signs of binary content
        garbled_chars = html_text.count('�') + html_text.count('\ufffd') + html_text.count('\x00')
        is_garbled = garbled_chars > len(html_text) * 0.05  # More than 5% garbled
        
        # If content looks garbled, try Selenium immediately
        if is_garbled and SELENIUM_AVAILABLE:
            print(f"Content appears garbled ({garbled_chars} bad chars), trying Selenium...")
            rendered_html = scrape_with_selenium(url)
            if rendered_html:
                # Check if Selenium result is better
                selenium_garbled = rendered_html.count('�') + rendered_html.count('\ufffd')
                if selenium_garbled < garbled_chars:
                    html_text = rendered_html
                    is_garbled = False
        
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Initialize extracted data
        extracted_data = {}
        
        # If content is minimal, try to fetch an 'about' page
        initial_text_length = len(soup.get_text(strip=True))
        if initial_text_length < 500:
            about_response = try_fetch_about_page(url, headers)
            if about_response:
                # Fix encoding for about page too
                if about_response.encoding is None or about_response.encoding == 'ISO-8859-1':
                    about_response.encoding = about_response.apparent_encoding
                try:
                    about_html = about_response.text
                except UnicodeDecodeError:
                    about_html = about_response.content.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(about_html, 'html.parser')
                extracted_data['fetched_from'] = 'about_page'
        
        # Check if this is a JavaScript-heavy site (React, Vue, etc.)
        # Look for common SPA indicators
        is_spa = False
        body_text = soup.get_text(strip=True)
        
        # Detect SPA frameworks
        scripts = soup.find_all('script')
        for script in scripts:
            script_content = str(script)
            if any(framework in script_content.lower() for framework in ['react', 'vue', 'angular', 'next.js', 'nuxt']):
                is_spa = True
                break
        
        # Also check if body is nearly empty (common in SPAs before JS loads)
        if len(body_text) < 200:
            is_spa = True
        
        extracted_data['is_spa'] = is_spa
        
        # If SPA detected and content is minimal, try Selenium for JS rendering
        if is_spa and len(body_text) < 500 and SELENIUM_AVAILABLE:
            print(f"SPA detected, attempting JavaScript rendering with Selenium...")
            rendered_html = scrape_with_selenium(url)
            if rendered_html and len(rendered_html) > len(response.text):
                soup = BeautifulSoup(rendered_html, 'html.parser')
                body_text = soup.get_text(strip=True)
                extracted_data['rendered_with_js'] = True
                print(f"Successfully rendered JS content: {len(body_text)} chars")
        
        # 1. Extract title (multiple methods)
        title = None
        if soup.title:
            title = soup.title.string
        if not title:
            title = soup.find('meta', property='og:title')
            if title:
                title = title.get('content')
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        extracted_data['title'] = title or "Unknown Website"
        
        # 2. Extract meta description (multiple sources)
        meta_desc = None
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content')
        if not meta_desc:
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                meta_desc = og_desc.get('content')
        if not meta_desc:
            twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
            if twitter_desc:
                meta_desc = twitter_desc.get('content')
        extracted_data['description'] = meta_desc
        
        # 3. Extract keywords
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            extracted_data['keywords'] = keywords.get('content')
        
        # 4. Extract Open Graph data
        og_type = soup.find('meta', property='og:type')
        if og_type:
            extracted_data['type'] = og_type.get('content')
        
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name:
            extracted_data['site_name'] = og_site_name.get('content')
        
        # 5. Extract main content with priority
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 
                            'iframe', 'noscript', 'form', 'button']):
            element.decompose()
        
        # Try to find main content areas (priority order)
        main_content = None
        content_selectors = [
            ('main', {}),
            ('article', {}),
            ('div', {'class': ['content', 'main-content', 'post-content', 'entry-content', 'article-content']}),
            ('div', {'id': ['content', 'main-content', 'main', 'primary']}),
            ('section', {'class': ['content', 'main']}),
        ]
        
        for tag, attrs in content_selectors:
            if attrs:
                for attr_key, attr_values in attrs.items():
                    for attr_value in attr_values:
                        element = soup.find(tag, {attr_key: lambda x: x and attr_value in x.lower()})
                        if element:
                            main_content = element
                            break
                    if main_content:
                        break
            else:
                main_content = soup.find(tag)
            if main_content:
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find('body')
        
        # Extract text from main content
        if main_content:
            # Get all paragraphs
            paragraphs = main_content.find_all('p')
            content_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # If no paragraphs, try list items
            if not content_text or len(content_text) < 100:
                list_items = main_content.find_all(['li', 'div'])
                content_text += ' ' + ' '.join([item.get_text(strip=True) for item in list_items[:20] if item.get_text(strip=True)])
            
            # If still no content, get all text
            if not content_text or len(content_text) < 100:
                content_text = main_content.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            content_text = ' '.join(content_text.split())
            if content_text and len(content_text) > 50:
                extracted_data['content'] = content_text[:2000]  # Limit to 2000 chars
        
        # 6. Extract headings for structure
        headings = []
        for h_tag in ['h1', 'h2', 'h3']:
            for heading in soup.find_all(h_tag, limit=5):
                heading_text = heading.get_text(strip=True)
                if heading_text and len(heading_text) > 3:
                    headings.append(heading_text)
        if headings:
            extracted_data['headings'] = headings[:5]
        
        # 7. Extract company/brand information
        # Look for about, company info
        about_keywords = ['about', 'company', 'who we are', 'our story', 'mission']
        about_content = []
        for p in soup.find_all('p', limit=50):
            p_text = p.get_text(strip=True).lower()
            if any(keyword in p_text for keyword in about_keywords):
                about_content.append(p.get_text(strip=True))
        if about_content:
            extracted_data['about'] = ' '.join(about_content[:3])
        
        # Format the output
        output_parts = []
        
        output_parts.append(f"🌐 Website: {extracted_data['title']}")
        
        if extracted_data.get('site_name'):
            output_parts.append(f"🏢 Company: {extracted_data['site_name']}")
        
        if extracted_data.get('description'):
            output_parts.append(f"\n📝 Description:\n{extracted_data['description']}")
        
        if extracted_data.get('type'):
            output_parts.append(f"\n🔖 Type: {extracted_data['type']}")
        
        if extracted_data.get('keywords'):
            output_parts.append(f"\n🏷️ Keywords: {extracted_data['keywords']}")
        
        if extracted_data.get('headings'):
            output_parts.append(f"\n📑 Key Topics:\n• " + "\n• ".join(extracted_data['headings']))
        
        if extracted_data.get('about'):
            output_parts.append(f"\n💼 About:\n{extracted_data['about'][:500]}")
        
        if extracted_data.get('content'):
            output_parts.append(f"\n📄 Main Content:\n{extracted_data['content'][:1000]}")
        
        result = "\n".join(output_parts)
        
        # Clean up any garbled characters from the result
        def clean_garbled_text(text):
            """Remove or replace garbled characters from text."""
            import re
            # Remove null bytes and replacement characters
            text = text.replace('\x00', '').replace('\ufffd', '').replace('�', '')
            # Remove sequences of non-printable characters
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]+', ' ', text)
            # Remove excessive special characters that indicate binary content
            # If a line has more than 50% non-alphanumeric (excluding spaces and common punctuation), remove it
            clean_lines = []
            for line in text.split('\n'):
                if line.strip():
                    alnum_count = sum(1 for c in line if c.isalnum() or c.isspace() or c in '.,!?;:\'"()-')
                    if len(line) == 0 or alnum_count / len(line) > 0.4:  # At least 40% readable
                        clean_lines.append(line)
                else:
                    clean_lines.append(line)
            return '\n'.join(clean_lines)
        
        result = clean_garbled_text(result)
        
        # Enhanced fallback for SPA sites or sites with minimal content
        if len(result) < 100 or (is_spa and len(result) < 300):
            fallback_parts = []
            
            fallback_parts.append(f"🌐 Website: {extracted_data['title']}")
            
            # For SPA sites, rely heavily on meta tags
            if is_spa:
                fallback_parts.append("\n⚡ Note: This appears to be a modern web app (React/Vue/Angular)")
            
            # Extract all meta tags as fallback
            all_meta = soup.find_all('meta')
            meta_info = {}
            for meta in all_meta:
                if meta.get('name') and meta.get('content'):
                    meta_info[meta.get('name')] = meta.get('content')
                elif meta.get('property') and meta.get('content'):
                    meta_info[meta.get('property')] = meta.get('content')
            
            # Add useful meta information
            if 'description' in meta_info or 'og:description' in meta_info:
                desc = meta_info.get('description') or meta_info.get('og:description')
                fallback_parts.append(f"\n📝 Description:\n{desc}")
            
            if 'keywords' in meta_info:
                fallback_parts.append(f"\n🏷️ Keywords: {meta_info['keywords']}")
            
            if 'og:site_name' in meta_info:
                fallback_parts.append(f"\n🏢 Site: {meta_info['og:site_name']}")
            
            # Try to extract any visible text (even if minimal)
            body = soup.find('body')
            if body:
                # Make a copy to manipulate
                body_copy = soup.find('body')
                
                # Remove all script and style tags
                for element in body_copy(['script', 'style', 'noscript']):
                    element.decompose()
                
                # Try to find any divs with substantial text content
                divs_with_content = []
                for div in body_copy.find_all(['div', 'section', 'article', 'p', 'span']):
                    text = div.get_text(strip=True)
                    if text and len(text) > 50 and not text.startswith('JavaScript'):
                        divs_with_content.append(text)
                
                if divs_with_content:
                    combined_text = ' '.join(divs_with_content[:10])
                    combined_text = ' '.join(combined_text.split())[:1000]
                    if combined_text and len(combined_text) > 50:
                        fallback_parts.append(f"\n📄 Available Content:\n{combined_text}")
                else:
                    visible_text = body_copy.get_text(separator=' ', strip=True)
                    visible_text = ' '.join(visible_text.split())
                    
                    if visible_text and len(visible_text) > 20:
                        fallback_parts.append(f"\n📄 Available Content:\n{visible_text[:1000]}")
            
            # Extract JSON-LD structured data if available (common in modern sites)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json as json_lib
                    data = json_lib.loads(script.string)
                    if isinstance(data, dict):
                        if data.get('description'):
                            fallback_parts.append(f"\n📋 Additional Info:\n{data['description'][:500]}")
                        if data.get('@type'):
                            fallback_parts.append(f"\n🔖 Type: {data['@type']}")
                        break
                except:
                    pass
            
            result = "\n".join(fallback_parts)
            
            # Final fallback - if still too short, get raw text
            if len(result) < 100:
                body_text = soup.get_text(separator=' ', strip=True)
                body_text = ' '.join(body_text.split())[:1500]
                result = f"🌐 Website: {extracted_data['title']}\n\n📄 Content:\n{body_text if body_text else 'Unable to extract detailed content. This may be a dynamically-loaded website.'}"
        
        # Ultimate fallback for JavaScript-heavy sites with minimal content
        if len(result) < 150:
            # Try Selenium as last resort if not already tried
            if SELENIUM_AVAILABLE and not extracted_data.get('rendered_with_js'):
                print(f"Content too short, attempting Selenium as last resort...")
                rendered_html = scrape_with_selenium(url)
                if rendered_html:
                    soup = BeautifulSoup(rendered_html, 'html.parser')
                    
                    # Remove scripts and styles
                    for element in soup(['script', 'style', 'noscript']):
                        element.decompose()
                    
                    # Get title
                    title = soup.title.string if soup.title else extracted_data.get('title', 'Unknown Website')
                    
                    # Get meta description
                    meta_desc = None
                    meta_tag = soup.find('meta', attrs={'name': 'description'})
                    if meta_tag:
                        meta_desc = meta_tag.get('content')
                    if not meta_desc:
                        og_desc = soup.find('meta', property='og:description')
                        if og_desc:
                            meta_desc = og_desc.get('content')
                    
                    # Get body text
                    body = soup.find('body')
                    if body:
                        body_text = body.get_text(separator=' ', strip=True)
                        body_text = ' '.join(body_text.split())[:1500]
                        
                        if len(body_text) > 100:
                            result = f"🌐 Website: {title}\n"
                            result += f"⚡ Rendered with JavaScript support\n"
                            if meta_desc:
                                result += f"\n📝 Description:\n{meta_desc}\n"
                            result += f"\n📄 Content:\n{body_text}"
            
            # If still too short, provide domain-based fallback
            if len(result) < 150:
                # Try to get information from the domain itself
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.replace('www.', '')
            
                # Build a descriptive result from what we have
                fallback_result = f"🌐 Website: {extracted_data['title']}\n"
                fallback_result += f"🔗 Domain: {domain}\n"
                
                # If we have any meta info, use it
                if extracted_data.get('description'):
                    fallback_result += f"\n📝 Description:\n{extracted_data['description']}\n"
                
                if extracted_data.get('keywords'):
                    fallback_result += f"\n🏷️ Keywords: {extracted_data['keywords']}\n"
                
                # Add a helpful message
                fallback_result += f"\n⚠️ Note: This website uses JavaScript to load content dynamically. "
                fallback_result += f"Static scraping returned limited information. "
                
                # Try to provide generic info based on domain
                category = None
                if any(word in domain.lower() for word in ['shop', 'store', 'buy', 'commerce', 'cart']):
                    category = "E-commerce/Shopping"
                elif any(word in domain.lower() for word in ['blog', 'news', 'post', 'article']):
                    category = "Blog/News/Content"
                elif any(word in domain.lower() for word in ['app', 'tech', 'dev', 'code', 'software', 'forge', 'digital']):
                    category = "Technology/Software/Digital Services"
                elif any(word in domain.lower() for word in ['health', 'medical', 'doctor', 'clinic']):
                    category = "Healthcare/Medical"
                elif any(word in domain.lower() for word in ['food', 'restaurant', 'cafe', 'recipe']):
                    category = "Food & Beverage"
                elif any(word in domain.lower() for word in ['edu', 'learn', 'course', 'school', 'university']):
                    category = "Education/Training"
                
                if category:
                    fallback_result += f"\n\n💡 Detected Category: {category}"
                    fallback_result += f"\n\n📝 Suggested Description:\n"
                    fallback_result += f"'{extracted_data['title']}' is a {category.lower()} platform/website "
                    fallback_result += f"available at {domain}. "
                
                fallback_result += f"\n\n💬 Please provide more details:\n"
                fallback_result += f"In the text area below, you can manually describe:\n"
                fallback_result += f"• What products/services you offer\n"
                fallback_result += f"• Your target audience\n"
                fallback_result += f"• Your unique value proposition\n"
                fallback_result += f"• Your brand personality/tone\n"
                fallback_result += f"\nExample: 'We are a modern web development agency specializing in building "
                fallback_result += f"custom web applications for startups. We focus on React, Node.js, and cloud solutions.'"
                
                result = fallback_result
        
        return result
    
    except requests.exceptions.Timeout:
        raise Exception("Website took too long to respond. Please try again.")
    except requests.exceptions.SSLError:
        raise Exception("SSL certificate error. The website may not be secure.")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to website. Please check the URL.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            raise Exception("Access denied (403). This website blocks automated scraping. Please manually describe your brand instead.")
        elif e.response.status_code == 404:
            raise Exception("Page not found (404). Please check the URL.")
        else:
            raise Exception(f"HTTP Error {e.response.status_code}: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch website: {str(e)}")
    except Exception as e:
        raise Exception(f"Error scraping website: {str(e)}")


def extract_audio(video_path):
    """Extract audio from video file and return audio file path."""
    try:
        # Create a temporary file for the audio
        audio_path = video_path.rsplit('.', 1)[0] + '.mp3'
        
        # Load video and extract audio
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, logger=None)
        video.close()
        
        return audio_path
    except Exception as e:
        raise Exception(f"Error extracting audio: {str(e)}")


def transcribe_audio(audio_path):
    """Transcribe audio using Groq Whisper API."""
    try:
        with open(audio_path, 'rb') as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="json",
                language="en",
                temperature=0.0
            )
        return transcription.text
    except Exception as e:
        raise Exception(f"Error transcribing audio: {str(e)}")


def analyze_and_rewrite_script(transcription, brand_input):
    """Use Groq LLM to analyze video style and rewrite script."""
    try:
        # First, analyze the style
        style_prompt = f"""Analyze the following video transcription and identify its style characteristics:

Transcription:
{transcription}

Provide a concise analysis covering:
1. Tone (e.g., casual, professional, energetic, calm)
2. Pacing (e.g., fast-paced, moderate, slow and deliberate)
3. Format (e.g., hook-driven, storytelling, educational, promotional)
4. Key stylistic elements (e.g., use of questions, direct address, repetition)

Keep your analysis brief and actionable (3-4 sentences)."""

        style_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": style_prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        style_analysis = style_response.choices[0].message.content
        
        # Now, rewrite the script
        rewrite_prompt = f"""You are a script writer specializing in social media content.

Original Transcription:
{transcription}

Style Analysis:
{style_analysis}

Brand/Company Information:
{brand_input}

Task: Rewrite the script to maintain the EXACT same style, tone, pacing, and format as the original, but customize the content to promote the brand/company provided above. The rewritten script should:
- Match the original's speaking style and energy
- Follow the same structure and pacing
- Replace the original content with relevant information about the new brand
- Be ready to use as a video script (natural, conversational)
- Be approximately the same length as the original

Provide ONLY the rewritten script, without any explanations or meta-commentary."""

        rewrite_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": rewrite_prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        rewritten_script = rewrite_response.choices[0].message.content
        
        return {
            'style_analysis': style_analysis,
            'rewritten_script': rewritten_script
        }
    except Exception as e:
        raise Exception(f"Error analyzing/rewriting script: {str(e)}")


@app.route('/')
def index():
    """Redirect to dashboard."""
    user = get_current_user()
    return render_template('generate.html', user=user)


@app.route('/dashboard')
def dashboard():
    """Dashboard page."""
    user = get_current_user()
    stats = get_stats(user['id'])
    scripts = get_all_scripts(user['id'])
    return render_template('dashboard.html', stats=stats, recent_scripts=scripts[:5], user=user)


@app.route('/generate')
def generate():
    """Generate script page."""
    user = get_current_user()
    return render_template('generate.html', user=user)


@app.route('/history')
def history():
    """History page."""
    user = get_current_user()
    scripts = get_all_scripts(user['id'])
    return render_template('history.html', scripts=scripts, user=user)


@app.route('/analytics')
def analytics():
    """Analytics page."""
    user = get_current_user()
    stats = get_stats(user['id'])
    return render_template('analytics.html', stats=stats, user=user)


@app.route('/library')
def library():
    """Library page."""
    user = get_current_user()
    scripts = get_all_scripts(user['id'])
    return render_template('library.html', scripts=scripts, user=user)


@app.route('/settings')
def settings():
    """Settings page."""
    user = get_current_user()
    return render_template('settings.html', user=user)


@app.route('/view/<script_id>')
def view_script(script_id):
    """View individual script."""
    user = get_current_user()
    script = get_script_by_id(script_id)
    if not script:
        return render_template('error.html', message='Script not found', user=user), 404
    return render_template('view_script.html', script=script, user=user)


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/auth/signup', methods=['POST'])
def signup():
    """Handle user signup."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Validate email format
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create user
        user = create_user(email, password, is_guest=False)
        
        # If there was a guest session, we could migrate their data here
        old_user_id = session.get('user_id')
        if old_user_id and old_user_id.startswith('guest_'):
            # Migrate guest data to new user (optional feature)
            pass
        
        # Set session
        session['user_id'] = user['id']
        session['is_guest'] = False
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'is_guest': user['is_guest']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/auth/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate
        user = authenticate_user(email, password)
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Set session
        session['user_id'] = user['id']
        session['is_guest'] = False
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'is_guest': user['is_guest']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/auth/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    session.clear()
    return jsonify({'success': True})


@app.route('/auth/current-user')
def current_user():
    """Get current user info."""
    user = get_current_user()
    return jsonify({
        'id': user['id'],
        'email': user.get('email'),
        'is_guest': user['is_guest']
    })


@app.route('/scrape-website', methods=['POST'])
def scrape_website():
    """Scrape website content from URL."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Scrape the website
        content = scrape_website_content(url)
        
        return jsonify({
            'success': True,
            'content': content
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/script/<script_id>', methods=['GET', 'DELETE'])
def handle_script(script_id):
    """Get or delete a script."""
    if request.method == 'GET':
        script = get_script_by_id(script_id)
        if not script:
            return jsonify({'error': 'Script not found'}), 404
        return jsonify(script)
    
    elif request.method == 'DELETE':
        success = delete_script(script_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to delete'}), 400


@app.route('/api/script/<script_id>/export')
def export_script(script_id):
    """Export a single script as JSON."""
    script = get_script_by_id(script_id)
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    output = io.BytesIO()
    output.write(json.dumps(script, indent=2).encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'script_{script_id}.json'
    )


@app.route('/api/export-all')
def export_all():
    """Export all scripts as JSON."""
    scripts = get_all_scripts()
    
    output = io.BytesIO()
    output.write(json.dumps({'scripts': scripts}, indent=2).encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'all_scripts_{int(os.time.time())}.json'
    )


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear all history."""
    try:
        if os.path.exists('data/history.json'):
            with open('data/history.json', 'w') as f:
                json.dump({'scripts': [], 'stats': {'total_scripts': 0, 'total_videos': 0}}, f)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/import-data', methods=['POST'])
def import_data():
    """Import scripts from JSON."""
    try:
        data = request.get_json()
        # Merge with existing data
        from data_store import DATA_FILE, ensure_data_dir
        ensure_data_dir()
        
        with open(DATA_FILE, 'r') as f:
            existing = json.load(f)
        
        if 'scripts' in data:
            existing['scripts'].extend(data['scripts'])
            existing['stats']['total_scripts'] = len(existing['scripts'])
            existing['stats']['total_videos'] = len(existing['scripts'])
        
        with open(DATA_FILE, 'w') as f:
            json.dump(existing, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/process', methods=['POST'])
def process_video():
    """Process uploaded video and generate rewritten script."""
    try:
        # Get process mode (transcription or full)
        process_mode = request.form.get('process_mode', 'transcription').strip()
        
        # Get brand input (only required for full process)
        brand_input = request.form.get('brand_input', '').strip()
        if process_mode == 'full' and not brand_input:
            return jsonify({'error': 'Please provide website URL or brand introduction for full process'}), 400
        
        # Check if Instagram URL is provided
        instagram_url = request.form.get('instagram_url', '').strip()
        video_path = None
        
        if instagram_url:
            # Download from Instagram
            if not is_instagram_url(instagram_url):
                return jsonify({'error': 'Invalid Instagram URL. Please provide a valid Instagram post/reel URL'}), 400
            
            try:
                video_path = download_instagram_video(instagram_url)
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        
        elif 'video' in request.files:
            # Handle file upload
            video_file = request.files['video']
            if video_file.filename == '':
                return jsonify({'error': 'No video file selected'}), 400
            
            if not allowed_file(video_file.filename):
                return jsonify({'error': 'Invalid file type. Please upload a video file (MP4, MOV, AVI, MKV, WEBM)'}), 400
            
            # Save uploaded video
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)
        
        else:
            return jsonify({'error': 'Please provide either a video file or Instagram URL'}), 400
        
        # Process video
        try:
            # Step 1: Extract audio
            audio_path = extract_audio(video_path)
            
            # Step 2: Transcribe audio
            transcription = transcribe_audio(audio_path)
            
            # Clean up files
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Get current user
            user = get_current_user()
            
            # If transcription-only mode, return just the transcription
            if process_mode == 'transcription':
                # Save to history (transcription only)
                script_data = {
                    'source_type': 'instagram' if instagram_url else 'upload',
                    'source': instagram_url if instagram_url else video_file.filename if 'video_file' in locals() else '',
                    'brand_input': '',
                    'transcription': transcription,
                    'style_analysis': '',
                    'rewritten_script': ''
                }
                script_id = save_script_result(script_data, user['id'])
                
                return jsonify({
                    'success': True,
                    'mode': 'transcription',
                    'script_id': script_id,
                    'transcription': transcription
                })
            
            # Full process: Step 3: Analyze and rewrite script
            result = analyze_and_rewrite_script(transcription, brand_input)
            
            # Save to history
            script_data = {
                'source_type': 'instagram' if instagram_url else 'upload',
                'source': instagram_url if instagram_url else video_file.filename if 'video_file' in locals() else '',
                'brand_input': brand_input,
                'transcription': transcription,
                'style_analysis': result['style_analysis'],
                'rewritten_script': result['rewritten_script']
            }
            script_id = save_script_result(script_data, user['id'])
            
            return jsonify({
                'success': True,
                'mode': 'full',
                'script_id': script_id,
                'transcription': transcription,
                'style_analysis': result['style_analysis'],
                'rewritten_script': result['rewritten_script']
            })
        
        except Exception as e:
            # Clean up files on error
            if os.path.exists(video_path):
                os.remove(video_path)
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
            raise e
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== CLEANUP & STORAGE ROUTES ====================

def get_folder_size(folder_path):
    """Get total size of a folder in bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size


def format_size(size_bytes):
    """Format bytes to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# ==================== PUBLIC TRANSCRIPTION API ====================

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    """
    Public API endpoint to transcribe Instagram videos.
    
    Request JSON:
    {
        "url": "https://www.instagram.com/reel/ABC123/"
    }
    
    Response JSON:
    {
        "success": true,
        "transcription": "The video transcript text...",
        "video_info": {...}
    }
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: url',
                'usage': {
                    'method': 'POST',
                    'content_type': 'application/json',
                    'body': {'url': 'https://www.instagram.com/reel/ABC123/'}
                }
            }), 400
        
        instagram_url = data['url'].strip()
        
        # Validate Instagram URL
        if not instagram_url or 'instagram.com' not in instagram_url:
            return jsonify({
                'success': False,
                'error': 'Invalid Instagram URL. Must be a valid instagram.com URL.'
            }), 400
        
        # Download video
        try:
            video_path = download_instagram_video(instagram_url)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to download video: {str(e)}'
            }), 400
        
        if not video_path:
            return jsonify({
                'success': False,
                'error': 'Failed to download video'
            }), 400
        
        audio_path = None
        try:
            # Extract audio
            audio_path = extract_audio(video_path)
            if not audio_path:
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract audio from video'
                }), 500
            
            # Transcribe audio
            transcription = transcribe_audio(audio_path)
            if not transcription:
                return jsonify({
                    'success': False,
                    'error': 'Failed to transcribe audio. Video may have no speech.'
                }), 500
            
            # Return successful response
            return jsonify({
                'success': True,
                'transcription': transcription,
                'video_info': {
                    'title': 'Instagram Video',
                    'url': instagram_url
                }
            })
            
        finally:
            # Cleanup files
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/transcribe', methods=['GET'])
def api_transcribe_info():
    """Show API usage info."""
    return jsonify({
        'api': 'Instagram Video Transcription API',
        'version': '1.0',
        'usage': {
            'method': 'POST',
            'endpoint': '/api/transcribe',
            'content_type': 'application/json',
            'body': {
                'url': 'https://www.instagram.com/reel/ABC123/'
            }
        },
        'example_curl': "curl -X POST -H 'Content-Type: application/json' -d '{\"url\": \"YOUR_INSTAGRAM_URL\"}' https://YOUR_DOMAIN/api/transcribe"
    })


# ==================== STORAGE & CLEANUP ENDPOINTS ====================

@app.route('/api/storage-info')
def storage_info():
    """Get storage usage information."""
    try:
        uploads_folder = app.config['UPLOAD_FOLDER']
        
        # Count files and calculate size
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        audio_extensions = {'.mp3', '.wav', '.m4a'}
        
        video_count = 0
        audio_count = 0
        video_size = 0
        audio_size = 0
        other_count = 0
        other_size = 0
        
        if os.path.exists(uploads_folder):
            for filename in os.listdir(uploads_folder):
                filepath = os.path.join(uploads_folder, filename)
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if ext in video_extensions:
                        video_count += 1
                        video_size += file_size
                    elif ext in audio_extensions:
                        audio_count += 1
                        audio_size += file_size
                    elif filename != '.gitkeep':
                        other_count += 1
                        other_size += file_size
        
        total_size = video_size + audio_size + other_size
        total_count = video_count + audio_count + other_count
        
        return jsonify({
            'success': True,
            'storage': {
                'total_files': total_count,
                'total_size': total_size,
                'total_size_formatted': format_size(total_size),
                'videos': {
                    'count': video_count,
                    'size': video_size,
                    'size_formatted': format_size(video_size)
                },
                'audio': {
                    'count': audio_count,
                    'size': audio_size,
                    'size_formatted': format_size(audio_size)
                },
                'other': {
                    'count': other_count,
                    'size': other_size,
                    'size_formatted': format_size(other_size)
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_uploads():
    """Delete all files in uploads folder (keeps scripts in history)."""
    try:
        uploads_folder = app.config['UPLOAD_FOLDER']
        deleted_count = 0
        deleted_size = 0
        errors = []
        
        if os.path.exists(uploads_folder):
            for filename in os.listdir(uploads_folder):
                if filename == '.gitkeep':
                    continue  # Keep .gitkeep file
                    
                filepath = os.path.join(uploads_folder, filename)
                if os.path.isfile(filepath):
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        deleted_size += file_size
                    except Exception as e:
                        errors.append(f"Failed to delete {filename}: {str(e)}")
        
        return jsonify({
            'success': True,
            'deleted_files': deleted_count,
            'freed_space': deleted_size,
            'freed_space_formatted': format_size(deleted_size),
            'errors': errors if errors else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    print("\n" + "="*60)
    print("🚀 Instagram Video Script Rewriter")
    print("="*60)
    print("✓ Groq API key loaded")
    print("✓ Server starting...")
    print(f"\n📍 Open your browser to: http://localhost:{port}")
    print("="*60 + "\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
