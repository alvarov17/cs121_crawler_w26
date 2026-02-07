import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

import re
from urllib.parse import urlparse

def extract_next_links(url, resp):
    """
    Returns a list of absolute URLs found on the page.
    """
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    # resp.raw_response.url: the url, again
    # resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    links = []

    if resp.status != 200 or resp.raw_response is None:
        return links

    try:
        content = resp.raw_response.content
        soup = BeautifulSoup(content, "html.parser")

        for tag in soup.find_all("a", href=True):
            href = tag.get("href")

            # resolve relative urls
            abs_url = urljoin(resp.url, href)

            # removes fragments from urls
            abs_url, _ = urldefrag(abs_url)

            links.append(abs_url)

    except Exception:
        return []

    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)

        # only http(s) protocol
        if parsed.scheme not in {"http", "https"}:
            return False

        # domain restrictions
        allowed_domains = (
            ".ics.uci.edu",
            ".cs.uci.edu",
            ".informatics.uci.edu",
            ".stat.uci.edu"
        )

        if not any(parsed.netloc.endswith(d) for d in allowed_domains):
            return False
        if "calendar" in parsed.path or "events" in parsed.path:
            if re.search(r"\d{4}[-/]\d{2}", parsed.path):
                return False
            if "tag" in parsed.path or "page" in parsed.path:
                return False
        if "ical=" in url:
            return False

        # Filter file types (given regex)
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            r"|png|tiff?|mid|mp2|mp3|mp4"
            r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1"
            r"|thmx|mso|arff|rtf|jar|csv"
            r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            parsed.path.lower()
        ):
            return False
        
        if "doku.php" in parsed.path:
            return False
        if parsed.query.count("=") > 2:
            return False
        if "?" in parsed.path and parsed.query.count("=") > 2:
            return False

        # spider trap prevention
        # Very long URLs (often traps)
        if len(url) > 300:
            return False

        # calendar loops
        if re.search(r"(/[^/]+)\1{2,}", parsed.path):
            return False

        # query explosion
        if parsed.query.count("=") > 5:
            return False

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
