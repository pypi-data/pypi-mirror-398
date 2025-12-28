#!/usr/bin/env python3
"""
MCP Server Google Cloud Vision - Production-ready OCR for LLMs

A Model Context Protocol server that provides powerful OCR capabilities
to LLMs like Claude, enabling them to read handwritten text, scanned PDFs,
and images with any orientation.

Developed by Kohen Avocats (https://kohenavocats.com)
Author: Hassan Kohen (https://kohenavocats.com/avocat-hassan-kohen/)

Sources:
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Google Vision API: https://cloud.google.com/vision/docs/reference/rest/v1/files/annotate
- Retry strategy: https://googleapis.dev/python/google-api-core/latest/retry.html
"""

import logging
import sys
import os
import base64
import unicodedata
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path
import asyncio
import random
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP, Context
    from mcp.server.session import ServerSession
    import aiohttp
    from aiohttp import ClientTimeout, TCPConnector
    logger.info("MCP modules loaded successfully")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Install with: uv add mcp aiohttp")
    sys.exit(1)

# Configuration - API key must be set via environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY environment variable is required")
    logger.error("Get your API key at: https://console.cloud.google.com/apis/credentials")
    sys.exit(1)

# Retry configuration with exponential backoff
RETRY_INITIAL_DELAY = 1.0
RETRY_MAX_DELAY = 60.0
RETRY_MULTIPLIER = 2.0
RETRY_DEADLINE = 120.0
MAX_RETRIES = 5

REQUEST_TIMEOUT = ClientTimeout(total=RETRY_DEADLINE, connect=10, sock_read=60)

_http_session: Optional[aiohttp.ClientSession] = None


async def get_http_session() -> aiohttp.ClientSession:
    """Reusable HTTP session with connection pooling"""
    global _http_session
    if _http_session is None or _http_session.closed:
        connector = TCPConnector(limit=20, limit_per_host=10, ttl_dns_cache=300, enable_cleanup_closed=True)
        _http_session = aiohttp.ClientSession(connector=connector, timeout=REQUEST_TIMEOUT, raise_for_status=False)
        logger.info("HTTP session created (pool: 20 connections)")
    return _http_session


async def close_http_session():
    """Clean session shutdown"""
    global _http_session
    if _http_session and not _http_session.closed:
        await _http_session.close()
        await asyncio.sleep(0.250)
        logger.info("HTTP session closed")


def calculate_backoff_with_jitter(attempt: int) -> float:
    """Exponential backoff with full jitter (AWS-style)"""
    delay = min(RETRY_INITIAL_DELAY * (RETRY_MULTIPLIER ** attempt), RETRY_MAX_DELAY)
    jittered_delay = random.uniform(0, delay * 2.0)
    return min(jittered_delay, RETRY_MAX_DELAY)


async def retry_with_backoff(func, *args, **kwargs):
    """Retry with exponential backoff. Only retries on network errors and 429/503"""
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            last_exception = e
            if attempt == MAX_RETRIES - 1:
                raise
            wait_time = calculate_backoff_with_jitter(attempt)
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed (network). Retry in {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "503" in error_str:
                last_exception = e
                if attempt == MAX_RETRIES - 1:
                    raise
                wait_time = calculate_backoff_with_jitter(attempt)
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed (quota). Retry in {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            else:
                raise
    raise last_exception


# Google Vision API feature mapping
FEATURE_MAPPING = {
    "text": "TEXT_DETECTION",
    "document": "DOCUMENT_TEXT_DETECTION",
    "labels": "LABEL_DETECTION",
    "faces": "FACE_DETECTION",
    "objects": "OBJECT_LOCALIZATION",
    "logos": "LOGO_DETECTION",
    "landmarks": "LANDMARK_DETECTION",
    "web": "WEB_DETECTION",
    "safe_search": "SAFE_SEARCH_DETECTION"
}


async def analyze_with_vision_api(image_content: bytes, features: List[str], is_pdf: bool = False) -> Dict:
    """Call Google Vision API. For PDF > 5 pages: PARALLEL requests in batches of 5"""
    if is_pdf:
        url = f"https://vision.googleapis.com/v1/files:annotate?key={GOOGLE_API_KEY}"
    else:
        url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"

    content_base64 = base64.b64encode(image_content).decode('utf-8')
    request_features = [{"type": FEATURE_MAPPING[f], "maxResults": 50} for f in features if f in FEATURE_MAPPING]

    if is_pdf:
        return await _process_pdf_parallel(url, content_base64, request_features)
    else:
        return await _process_image(url, content_base64, request_features)


async def _process_image(url: str, content_base64: str, request_features: List[Dict]) -> Dict:
    """Process a single image"""
    request_body = {"requests": [{"image": {"content": content_base64}, "features": request_features}]}
    session = await get_http_session()

    async def make_request():
        async with session.post(url, json=request_body) as response:
            response_text = await response.text()
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Vision API error ({response.status}): {response_text[:500]}")
                raise Exception(f"Vision API error: {response.status} - {response_text[:200]}")

    return await retry_with_backoff(make_request)


async def _process_pdf_parallel(url: str, content_base64: str, request_features: List[Dict]) -> Dict:
    """Process PDF with 5-page batches IN PARALLEL for optimal performance"""
    request_body = {"requests": [{"inputConfig": {"content": content_base64, "mimeType": "application/pdf"}, "features": request_features}]}
    session = await get_http_session()

    async def make_first_request():
        async with session.post(url, json=request_body) as response:
            response_text = await response.text()
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Vision API error ({response.status}): {response_text[:500]}")
                raise Exception(f"Vision API error: {response.status} - {response_text[:200]}")

    first_result = await retry_with_backoff(make_first_request)
    all_responses = [first_result]

    total_pages = 0
    if "responses" in first_result and first_result["responses"]:
        total_pages = first_result["responses"][0].get("totalPages", 0)

    logger.info(f"PDF: {total_pages} total pages")

    if total_pages > 5:
        tasks = []
        for start_page in range(6, total_pages + 1, 5):
            end_page = min(start_page + 4, total_pages)
            pages_to_request = list(range(start_page, end_page + 1))
            request_body_pages = {"requests": [{"inputConfig": {"content": content_base64, "mimeType": "application/pdf"}, "features": request_features, "pages": pages_to_request}]}
            tasks.append(_fetch_pdf_pages(session, url, request_body_pages, pages_to_request))

        logger.info(f"Launching {len(tasks)} PARALLEL requests (pages 6-{total_pages})")
        additional_responses = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, resp in enumerate(additional_responses):
            if isinstance(resp, Exception):
                logger.error(f"Batch #{idx + 1} error: {resp}")
            elif resp is not None:
                all_responses.append(resp)

    return combine_pdf_responses(all_responses)


async def _fetch_pdf_pages(session: aiohttp.ClientSession, url: str, request_body: Dict, pages: List[int]) -> Optional[Dict]:
    """Fetch a batch of pages with retry"""
    async def make_request():
        async with session.post(url, json=request_body) as response:
            if response.status == 200:
                logger.info(f"Pages {pages} OK")
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Pages {pages} error: {response.status} - {error_text[:200]}")
                raise Exception(f"API error for pages {pages}: {response.status}")

    try:
        return await retry_with_backoff(make_request)
    except Exception as e:
        logger.error(f"Pages {pages} failed after {MAX_RETRIES} attempts: {e}")
        return None


def combine_pdf_responses(responses: List[Dict]) -> Dict:
    """Combine multiple API responses for a multi-page PDF"""
    if not responses:
        return {}
    combined = responses[0].copy()
    if len(responses) > 1 and "responses" in combined and combined["responses"]:
        base_response = combined["responses"][0]
        if "responses" not in base_response:
            base_response["responses"] = []
        for resp in responses[1:]:
            if "responses" in resp and resp["responses"]:
                if "responses" in resp["responses"][0]:
                    base_response["responses"].extend(resp["responses"][0]["responses"])
    return combined


def extract_text_from_response(response: Dict, is_pdf: bool = False) -> str:
    """Extract text from Vision API response with multi-page support"""
    if not response.get("responses"):
        return ""

    if is_pdf:
        all_text = []
        main_response = response.get("responses", [])
        if main_response and isinstance(main_response[0], dict):
            if "responses" in main_response[0]:
                inner_responses = main_response[0]["responses"]
                for page_result in inner_responses:
                    if "fullTextAnnotation" in page_result:
                        text = page_result["fullTextAnnotation"].get("text", "")
                        if text:
                            all_text.append(text)
                    elif "textAnnotations" in page_result and page_result["textAnnotations"]:
                        text = page_result["textAnnotations"][0].get("description", "")
                        if text:
                            all_text.append(text)
            else:
                for result in main_response:
                    if "fullTextAnnotation" in result:
                        text = result["fullTextAnnotation"].get("text", "")
                        if text:
                            all_text.append(text)
                    elif "textAnnotations" in result and result["textAnnotations"]:
                        text = result["textAnnotations"][0].get("description", "")
                        if text:
                            all_text.append(text)

        if all_text:
            if len(all_text) > 1:
                return "\n\n--- Page suivante ---\n\n".join(all_text)
            else:
                return all_text[0]
        return ""
    else:
        result = response["responses"][0]
        if "fullTextAnnotation" in result:
            return result["fullTextAnnotation"].get("text", "")
        if "textAnnotations" in result and result["textAnnotations"]:
            return result["textAnnotations"][0].get("description", "")
    return ""


def find_file_with_special_chars(file_path: str) -> Optional[str]:
    """Find files with complex Unicode characters (French accents, special quotes, etc.)"""
    logger.info(f"Searching: {repr(file_path)}")

    if os.path.exists(file_path):
        return file_path

    # Try different Unicode normalizations
    for norm in ['NFD', 'NFC', 'NFKD', 'NFKC']:
        normalized = unicodedata.normalize(norm, file_path)
        if os.path.exists(normalized):
            logger.info(f"Found with {norm}")
            return normalized

    # Try common character replacements
    replacements = [('\u2019', "'"), ('\u201c', '"'), ('\u201d', '"'), ('\u2013', '-'), ('\u2014', '-'), ('\u2026', '...')]
    for old, new in replacements:
        test = file_path.replace(old, new)
        if os.path.exists(test):
            return test

    # Try path resolution
    try:
        resolved = str(Path(file_path).expanduser().resolve())
        if os.path.exists(resolved):
            return resolved
    except:
        pass

    # Case-insensitive search in parent directory
    try:
        parent = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        if parent and os.path.exists(parent):
            filename_norm = unicodedata.normalize('NFC', filename.lower())
            for f in os.listdir(parent):
                if unicodedata.normalize('NFC', f.lower()) == filename_norm:
                    return os.path.join(parent, f)
    except:
        pass

    logger.error(f"File not found: {repr(file_path)}")
    return None


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage server lifecycle: startup and shutdown"""
    logger.info("Starting Google Vision MCP server")
    logger.info(f"API Key configured: {GOOGLE_API_KEY[:10]}...")
    logger.info(f"Retry config: initial={RETRY_INITIAL_DELAY}s, max={RETRY_MAX_DELAY}s, multiplier={RETRY_MULTIPLIER}, deadline={RETRY_DEADLINE}s")
    await get_http_session()
    try:
        yield
    finally:
        logger.info("Stopping server...")
        await close_http_session()


mcp = FastMCP("google-vision", lifespan=app_lifespan)


@mcp.tool()
async def analyze_image(
    image_path: str,
    features: List[str] = ["text", "labels"],
    response_format: Literal["json", "markdown"] = "markdown",
    ctx: Context[ServerSession, None] | None = None
) -> str:
    """
    Analyze an image with Google Cloud Vision API.

    Features: text, document, labels, faces, objects, logos, landmarks, web, safe_search
    Returns: OCR text + detected objects/logos/faces based on requested features.
    """
    if ctx:
        await ctx.info(f"Analyzing {os.path.basename(image_path)}")

    found_path = find_file_with_special_chars(image_path)
    if not found_path:
        error_response = {
            "error": "file_not_found",
            "message": "Image file not found",
            "provided_path": image_path,
            "suggestion": "Verify the path is absolute and the file exists. Example: /Users/name/image.jpg"
        }
        if response_format == "json":
            return json.dumps(error_response, indent=2)
        else:
            return f"Error: Image file not found\n\nProvided path: {image_path}\n\nSuggestion: Verify the path is absolute and the file exists.\nValid example: /Users/name/image.jpg"

    try:
        with open(found_path, 'rb') as f:
            image_content = f.read()

        if ctx:
            await ctx.report_progress(0.3, 1.0, "Sending to Vision API...")

        response = await analyze_with_vision_api(image_content, features)

        if ctx:
            await ctx.report_progress(0.8, 1.0, "Formatting results...")

        text = extract_text_from_response(response, is_pdf=False)
        result = response.get("responses", [{}])[0]

        labels_list = []
        if "labels" in features and "labelAnnotations" in result:
            labels_list = [{"description": label["description"], "score": round(label.get("score", 0) * 100, 1)} for label in result["labelAnnotations"][:10]]

        faces_count = 0
        if "faces" in features and "faceAnnotations" in result:
            faces_count = len(result["faceAnnotations"])

        objects_list = []
        if "objects" in features and "localizedObjectAnnotations" in result:
            objects_list = [{"name": obj["name"], "score": round(obj.get("score", 0) * 100, 1)} for obj in result["localizedObjectAnnotations"][:10]]

        logos_list = []
        if "logos" in features and "logoAnnotations" in result:
            logos_list = [{"description": logo["description"], "score": round(logo.get("score", 0) * 100, 1)} for logo in result["logoAnnotations"]]

        if ctx:
            await ctx.report_progress(1.0, 1.0, "Done")

        if response_format == "json":
            return json.dumps({"filename": os.path.basename(found_path), "text": text, "labels": labels_list, "faces_count": faces_count, "objects": objects_list, "logos": logos_list}, indent=2, ensure_ascii=False)
        else:
            output = f"Analysis of {os.path.basename(found_path)}\n\n"
            if "text" in features or "document" in features:
                output += f"Extracted text:\n{text}\n\n" if text else "No text detected\n\n"
            if labels_list:
                output += "Detected objects:\n"
                for label in labels_list:
                    output += f"- {label['description']} ({label['score']}%)\n"
                output += "\n"
            if faces_count > 0:
                output += f"Faces detected: {faces_count}\n\n"
            if objects_list:
                output += "Localized objects:\n"
                for obj in objects_list:
                    output += f"- {obj['name']} ({obj['score']}%)\n"
                output += "\n"
            if logos_list:
                output += "Detected logos:\n"
                for logo in logos_list:
                    output += f"- {logo['description']} ({logo['score']}%)\n"
                output += "\n"
            return output

    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        if ctx:
            await ctx.error(f"Error: {str(e)}")

        error_response = {"error": "analysis_failed", "message": str(e), "suggestion": "Check if the file is a valid image format (JPG, PNG, GIF, BMP, WEBP). If the error persists, verify your Google Vision API quota."}

        if response_format == "json":
            return json.dumps(error_response, indent=2)
        else:
            return f"Error during analysis: {str(e)}\n\nSuggestion: Check if the file is a valid image format (JPG, PNG, GIF, BMP, WEBP).\nIf the error persists, verify your Google Vision API quota."


@mcp.tool()
async def analyze_pdf(
    pdf_path: str,
    extract_text_only: bool = True,
    response_format: Literal["json", "markdown"] = "markdown",
    ctx: Context[ServerSession, None] | None = None
) -> str:
    """
    Extract text from a PDF file using Google Cloud Vision OCR.

    Handles multi-page PDFs (up to 2000 pages) with parallel processing.
    Auto-saves to .txt file if text exceeds 5000 characters. Max size: 20 MB.
    """
    if ctx:
        await ctx.info(f"Analyzing PDF: {os.path.basename(pdf_path)}")

    found_path = find_file_with_special_chars(pdf_path)
    if not found_path:
        error_response = {"error": "file_not_found", "message": "PDF file not found", "provided_path": pdf_path, "suggestion": "Verify the path is absolute and ends with .pdf. Example: /Users/name/document.pdf"}
        if response_format == "json":
            return json.dumps(error_response, indent=2)
        else:
            return f"Error: PDF file not found\n\nProvided path: {pdf_path}\n\nSuggestion: Verify the path is absolute and ends with .pdf.\nValid example: /Users/name/document.pdf"

    try:
        with open(found_path, 'rb') as f:
            pdf_content = f.read()

        file_size_mb = len(pdf_content) / (1024 * 1024)
        if file_size_mb > 20:
            error_response = {"error": "file_too_large", "message": f"PDF file is too large ({file_size_mb:.2f} MB)", "limit_mb": 20, "suggestion": "Split the PDF into smaller files or compress it using a PDF tool."}
            if response_format == "json":
                return json.dumps(error_response, indent=2)
            else:
                return f"Error: PDF file is too large ({file_size_mb:.2f} MB)\n\nLimit: 20 MB\n\nSuggestion: Split the PDF into smaller files or compress it using a PDF tool."

        logger.info(f"Analyzing PDF: {os.path.basename(found_path)} ({file_size_mb:.2f} MB)")

        if ctx:
            await ctx.report_progress(0.2, 1.0, f"PDF loaded ({file_size_mb:.1f} MB)")

        features_to_use = ["document"] if extract_text_only else ["document", "labels", "logos"]

        if ctx:
            await ctx.report_progress(0.3, 1.0, "Sending to Vision API (may take time)...")

        response = await analyze_with_vision_api(pdf_content, features_to_use, is_pdf=True)

        if ctx:
            await ctx.report_progress(0.8, 1.0, "Extracting text...")

        text = extract_text_from_response(response, is_pdf=True)

        if not text:
            error_response = {"error": "no_text_extracted", "message": "No text could be extracted from this PDF", "filename": os.path.basename(found_path), "size_mb": round(file_size_mb, 2), "suggestion": "The PDF may contain only images without text, be corrupted, or use an unsupported language/encoding."}
            if response_format == "json":
                return json.dumps(error_response, indent=2)
            else:
                return f"Analysis of PDF: {os.path.basename(found_path)}\nSize: {file_size_mb:.2f} MB\n\nNo text could be extracted.\n\nPossible reasons:\n- PDF contains only images without text\n- PDF is corrupted or protected\n- Language/encoding not supported"

        word_count = len(text.split())
        char_count = len(text)
        pages_count = text.count('--- Page suivante ---') + 1

        logger.info(f"Extracted: {pages_count} pages, {word_count} words, {char_count} characters")

        saved_file_path = None
        if char_count > 5000:
            if ctx:
                await ctx.report_progress(0.9, 1.0, "Saving text...")

            base_name = os.path.splitext(os.path.basename(found_path))[0]
            output_filename = f"{base_name}_extracted.txt"
            output_path = os.path.join(os.path.dirname(found_path), output_filename)

            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Text extracted from: {os.path.basename(found_path)}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Pages: {pages_count}\n")
                    f.write(f"Statistics: {word_count} words, {char_count} characters\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(text)
                saved_file_path = output_path
                logger.info(f"Saved: {output_path}")
            except Exception as e:
                logger.error(f"Save error: {e}")

        if ctx:
            await ctx.report_progress(1.0, 1.0, "Done")

        if response_format == "json":
            result = {"filename": os.path.basename(found_path), "size_mb": round(file_size_mb, 2), "pages": pages_count, "words": word_count, "characters": char_count, "saved_file": saved_file_path}
            if saved_file_path and char_count > 5000:
                result["text_preview"] = text[:500]
                result["text_end"] = text[-300:]
            else:
                result["text"] = text
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            if saved_file_path and char_count > 5000:
                output = f"PDF analyzed successfully\n\nFile: {os.path.basename(found_path)}\nSize: {file_size_mb:.2f} MB\nPages: {pages_count}\nStatistics: {word_count} words, {char_count} characters\n\nFull text saved to:\n{saved_file_path}\n\n--- Preview (first 500 characters) ---\n{text[:500]}...\n\n--- End of document (last 300 characters) ---\n...{text[-300:]}\n"
            else:
                output = f"PDF analysis: {os.path.basename(found_path)}\n\nSize: {file_size_mb:.2f} MB\nStatistics: {word_count} words, {char_count} characters\n\n"
                if saved_file_path:
                    output += f"Saved to: {saved_file_path}\n\n"
                output += f"Extracted text:\n{text}\n"
            return output

    except Exception as e:
        logger.error(f"PDF error: {e}", exc_info=True)
        if ctx:
            await ctx.error(f"Error: {str(e)}")

        error_response = {"error": "analysis_failed", "message": str(e), "filename": os.path.basename(found_path) if found_path else pdf_path}

        if "400" in str(e):
            error_response["suggestion"] = "The PDF may be in an unsupported format. Try converting it to a standard PDF format."
        elif "413" in str(e):
            error_response["suggestion"] = "File is too large. Try splitting it into smaller PDFs."
        elif "timeout" in str(e).lower():
            error_response["suggestion"] = "Request timed out. The server may be overloaded, try again in a few minutes."
        else:
            error_response["suggestion"] = "Verify the PDF is not corrupted or password-protected. Check your Google Vision API quota."

        if response_format == "json":
            return json.dumps(error_response, indent=2)
        else:
            error_msg = f"Error during PDF analysis\n\nFile: {os.path.basename(found_path) if found_path else pdf_path}\nError: {str(e)}\n\nSuggestion: {error_response.get('suggestion', 'Check the error message above.')}\n"
            return error_msg


if __name__ == "__main__":
    mcp.run()
