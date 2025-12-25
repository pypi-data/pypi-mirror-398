# researcher_tools.py

import os
import requests
from typing import List, Callable, Any, Dict
from langchain_core.tools import tool
from athenah_ai.logger import logger
from athenah_ai.config import config

# --- Google Search Tool (SerpAPI) ---


def google_search(
    query: str, api_key: str = None, cse_id: str = None, num: int = 5
) -> str:
    """
    Uses Google Custom Search API to search the web.
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    cse_id = cse_id or os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        logger.error("Google API key or CSE ID not set.")
        return "Google API key or CSE ID not set."
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"q": query, "key": api_key, "cx": cse_id, "num": num}
        resp = requests.get(url, params=params, timeout=config.http.default_timeout)
        resp.raise_for_status()
        results = resp.json().get("items", [])
        return "\n".join([f"{item['title']}: {item['link']}" for item in results])
    except Exception as e:
        logger.error(f"Google search error: {e}")
        return f"Google search error: {e}"


# --- DuckDuckGo Search Tool ---


def duckduckgo_search(query: str, num: int = 5) -> str:
    """
    Uses DuckDuckGo Instant Answer API (unofficial) to search the web.
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
        resp = requests.get(url, params=params, timeout=config.http.default_timeout)
        resp.raise_for_status()
        data = resp.json()
        results = []
        if "RelatedTopics" in data:
            for topic in data["RelatedTopics"][:num]:
                if "Text" in topic and "FirstURL" in topic:
                    results.append(f"{topic['Text']}: {topic['FirstURL']}")
        return "\n".join(results) if results else "No DuckDuckGo results found."
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return f"DuckDuckGo search error: {e}"


# --- Bing Search Tool (Bing Web Search API) ---


def bing_search(query: str, api_key: str = None, num: int = 5) -> str:
    """
    Uses Bing Web Search API to search the web.
    """
    api_key = api_key or os.environ.get("BING_API_KEY")
    if not api_key:
        logger.error("Bing API key not set.")
        return "Bing API key not set."
    try:
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": query, "count": num}
        resp = requests.get(url, headers=headers, params=params, timeout=config.http.default_timeout)
        resp.raise_for_status()
        results = resp.json().get("webPages", {}).get("value", [])
        return "\n".join([f"{item['name']}: {item['url']}" for item in results])
    except Exception as e:
        logger.error(f"Bing search error: {e}")
        return f"Bing search error: {e}"


# --- Wikipedia Search Tool ---


def wikipedia_search(query: str, num: int = 3) -> str:
    """
    Uses Wikipedia API to search for articles.
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": num,
        }
        resp = requests.get(url, params=params, timeout=config.http.default_timeout)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        return "\n".join(
            [
                f"{item['title']}: https://en.wikipedia.org/wiki/{item['title'].replace(' ', '_')}"
                for item in results
            ]
        )
    except Exception as e:
        logger.error(f"Wikipedia search error: {e}")
        return f"Wikipedia search error: {e}"


# --- Grokipedia Search Tool ---


def grokipedia_search(query: str, num: int = 5) -> str:
    """
    Searches Grokipedia for information.
    """
    try:
        url = "https://grokipedia.com/api/search"
        params = {"q": query, "limit": num}
        resp = requests.get(url, params=params, timeout=config.http.default_timeout)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return "No Grokipedia results found."
        return "\n".join(
            [
                f"{item.get('title', 'N/A')}: {item.get('url', 'N/A')}"
                for item in results
            ]
        )
    except Exception as e:
        logger.error(f"Grokipedia search error: {e}")
        return f"Grokipedia search error: {e}"


# --- Local Document Search Tool (FAISS, etc.) ---


def document_search(query: str, vector_db, k: int = 5) -> str:
    """
    Searches a local vector database (e.g., FAISS) for relevant documents.
    """
    try:
        results = vector_db.similarity_search(query, k=k)
        if not results:
            return "No relevant documents found."
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        logger.error(f"Document search error: {e}")
        return f"Document search error: {e}"


# --- File Read Tool ---


def read_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return f"Error reading file: {e}"


# --- Google PDF/Document Search Tool ---


def google_pdf_search(
    query: str, api_key: str = None, cse_id: str = None, num: int = 5
) -> str:
    """
    Uses Google Custom Search API to search for PDFs and documents.
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    cse_id = cse_id or os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        logger.error("Google API key or CSE ID not set.")
        return "Google API key or CSE ID not set."
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        # Restrict to filetype:pdf, doc, docx, ppt, pptx, xls, xlsx
        filetypes = ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx"]
        results = []
        for filetype in filetypes:
            params = {
                "q": f"{query} filetype:{filetype}",
                "key": api_key,
                "cx": cse_id,
                "num": num,
            }
            resp = requests.get(url, params=params, timeout=config.http.default_timeout)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            for item in items:
                link = item.get("link", "")
                if link.lower().endswith(tuple(filetypes)):
                    results.append(f"{item['title']}: {link}")
        return "\n".join(results) if results else "No document results found."
    except Exception as e:
        logger.error(f"Google PDF search error: {e}")
        return f"Google PDF search error: {e}"


# --- DuckDuckGo PDF/Document Search Tool ---


def duckduckgo_pdf_search(query: str, num: int = 5) -> str:
    """
    Uses DuckDuckGo to search for PDFs and documents.
    """
    try:
        url = "https://duckduckgo.com/html/"
        filetypes = ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx"]
        results = []
        for filetype in filetypes:
            params = {"q": f"{query} filetype:{filetype}"}
            resp = requests.get(url, params=params, timeout=config.http.default_timeout)
            resp.raise_for_status()
            # DuckDuckGo HTML parsing (simple, not robust)
            links = [
                line
                for line in resp.text.split('href="')
                if any(line.lower().startswith(f) for f in ("http", "https"))
            ]
            for link in links:
                url_part = link.split('"')[0]
                if url_part.lower().endswith(filetype):
                    results.append(url_part)
            if len(results) >= num:
                break
        return "\n".join(results[:num]) if results else "No document results found."
    except Exception as e:
        logger.error(f"DuckDuckGo PDF search error: {e}")
        return f"DuckDuckGo PDF search error: {e}"


# --- Torrent Search Tool (Libgen, 1337x, etc.) ---


def libgen_search(query: str, num: int = 5) -> str:
    """
    Searches Library Genesis for books and returns download links.
    """
    try:
        url = "http://libgen.rs/search.php"
        params = {"req": query, "res": num, "column": "def"}
        resp = requests.get(url, params=params, timeout=config.http.extended_timeout)
        resp.raise_for_status()
        # Simple HTML parsing for links (not robust, for demo)
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for row in soup.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) > 9:
                title = cells[2].get_text(strip=True)
                mirrors = [a.get("href") for a in cells[9].find_all("a")]
                if mirrors:
                    links.append(f"{title}: {mirrors[0]}")
            if len(links) >= num:
                break
        return "\n".join(links) if links else "No Libgen results found."
    except Exception as e:
        logger.error(f"Libgen search error: {e}")
        return f"Libgen search error: {e}"


def torrent_search_1337x(query: str, num: int = 5) -> str:
    """
    Searches 1337x for torrents (books, files) and returns magnet links.
    """
    try:
        # Use a public API or scraping service for 1337x (here, using allorigins for demo)
        search_url = f"https://1337x.to/search/{query.replace(' ', '%20')}/1/"
        resp = requests.get(
            f"https://api.allorigins.win/get?url={search_url}", timeout=config.http.extended_timeout
        )
        resp.raise_for_status()
        import re
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.json()["contents"], "html.parser")
        results = []
        for row in soup.select("tr"):
            a = row.find("a", href=True)
            if a and "/torrent/" in a["href"]:
                title = a.get_text(strip=True)
                link = "https://1337x.to" + a["href"]
                # Get magnet link from detail page
                detail_resp = requests.get(
                    f"https://api.allorigins.win/get?url={link}", timeout=config.http.extended_timeout
                )
                detail_soup = BeautifulSoup(
                    detail_resp.json()["contents"], "html.parser"
                )
                magnet = detail_soup.find("a", href=re.compile(r"^magnet:"))
                if magnet:
                    results.append(f"{title}: {magnet['href']}")
            if len(results) >= num:
                break
        return "\n".join(results) if results else "No 1337x results found."
    except Exception as e:
        logger.error(f"1337x search error: {e}")
        return f"1337x search error: {e}"


# --- Torrent Download Tool (aria2c, transmission-cli, etc.) ---


def download_torrent(magnet_link: str, download_dir: str = "/tmp") -> str:
    """
    Downloads a torrent using aria2c (must be installed).
    """
    import subprocess

    try:
        cmd = ["aria2c", "--dir", download_dir, magnet_link]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=config.http.download_timeout)
        if result.returncode == 0:
            return f"Download started for: {magnet_link}"
        else:
            logger.error(f"aria2c error: {result.stderr}")
            return f"aria2c error: {result.stderr}"
    except Exception as e:
        logger.error(f"Torrent download error: {e}")
        return f"Torrent download error: {e}"


# --- List of Search Engines (for reference) ---

SEARCH_ENGINES = [
    "Google",
    "Bing",
    "DuckDuckGo",
    "Yahoo",
    "Yandex",
    "Baidu",
    "Ecosia",
    "Qwant",
    "Startpage",
    "Brave Search",
    "Wikipedia",
    "Grokipedia",
    "WolframAlpha",
    "You.com",
    "Mojeek",
    "Swisscows",
    "MetaGer",
    "Searx",
    "Gigablast",
    "Neeva (defunct)",
    "Ask.com",
    "Dogpile",
    "Local Document Search (FAISS, Chroma, etc.)",
]

# --- Tool Decorators ---


@tool
def google_search_tool(query: str) -> str:
    """Search the web for PDFs and documents using Google Custom Search."""
    return google_pdf_search(query)


@tool
def duckduckgo_search_tool(query: str) -> str:
    """Search the web for PDFs and documents using DuckDuckGo."""
    return duckduckgo_pdf_search(query)


@tool
def wikipedia_search_tool(query: str) -> str:
    """Search Wikipedia for articles."""
    return wikipedia_search(query)


@tool
def grokipedia_search_tool(query: str) -> str:
    """Search Grokipedia for information."""
    return grokipedia_search(query)


@tool
def read_file_tool(path: str) -> str:
    """Read a file from a path. Include the full path to the file."""
    return read_file(path)


@tool
def libgen_search_tool(query: str) -> str:
    """Search for books and download links on Library Genesis."""
    return libgen_search(query)


@tool
def torrent_search_tool(query: str) -> str:
    """Search for torrents (books, files) and get magnet links from 1337x."""
    return torrent_search_1337x(query)


@tool
def download_torrent_tool(magnet_link: str) -> str:
    """Download a torrent using a magnet link (requires aria2c installed)."""
    return download_torrent(magnet_link)


# --- Tool Factory ---


def get_research_tools(
    vector_db=None,
    google_api_key=None,
    google_cse_id=None,
    bing_api_key=None,
    enable_torrents: bool = True,
) -> List:
    """
    Returns a list of tool functions for research, including document and torrent tools.
    """
    tools = [
        google_search_tool,
        duckduckgo_search_tool,
        wikipedia_search_tool,
        grokipedia_search_tool,
        read_file_tool,
    ]

    if vector_db:

        @tool
        def document_search_tool(query: str) -> str:
            """Search local indexed documents for relevant information."""
            return document_search(query, vector_db)

        tools.append(document_search_tool)

    if enable_torrents:
        tools.extend(
            [
                libgen_search_tool,
                torrent_search_tool,
                download_torrent_tool,
            ]
        )

    return tools
