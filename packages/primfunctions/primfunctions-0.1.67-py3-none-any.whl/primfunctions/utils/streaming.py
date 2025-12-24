import re
import asyncio


# Language-specific punctuation sets for commonly used languages
PUNCTUATION_BY_LANGUAGE = {
    'en': ['.', '!', '?', '\n'],  # English
    'zh': ['.', '!', '?', '\n', '。', '！', '？', '，', '；', '：'],  # Chinese
    'ko': ['.', '!', '?', '\n', '。', '！', '？', '，', '；', '：'],  # Korean
    'ja': ['.', '!', '?', '\n', '。', '！', '？', '、', '；', '：'],  # Japanese (uses 、 instead of ，)
    'es': ['.', '!', '?', '\n', '¡', '¿'],  # Spanish (inverted punctuation)
    'fr': ['.', '!', '?', '\n', '«', '»'],  # French (guillemets)
    'it': ['.', '!', '?', '\n'],  # Italian
    'de': ['.', '!', '?', '\n'],  # German
    'hi': ['.', '!', '?', '\n', '।', '!', '?', '।', ';', ':'],  # Hindi
}

# Default punctuation marks (comprehensive set covering most languages)
DEFAULT_PUNCTUATION = ['.', '!', '?', '\n', '。', '！', '？', '，', '、', '；', '：', '¡', '¿', '«', '»', '।']


# Helper function to handle streaming response and chunking
async def stream_sentences(streaming_response, punctuation_marks=None, clean_text=True, min_sentence_length=6, language=None):
    """
    Streams OpenAI or Google Gemini response and yields complete sentences as strings.

    Args:
        streaming_response: The streaming response from OpenAI or Google Gemini
        punctuation_marks: Optional set of punctuation marks to use for sentence boundaries
                          Defaults to comprehensive set covering most languages
        clean_text: Whether to clean markdown and special characters for speech
                   Defaults to True
        min_sentence_length: Minimum length (in characters) for a sentence to be yielded
                           Defaults to 6 characters
        language: Optional language code to use language-specific punctuation
                 Supported: 'en', 'zh', 'ko', 'ja', 'es', 'fr', 'it', 'de'

    Yields:
        str: Complete sentences as they are formed
    """
    # Set punctuation marks based on language or use provided/default
    if language and language in PUNCTUATION_BY_LANGUAGE:
        punctuation_marks = PUNCTUATION_BY_LANGUAGE[language]
    elif punctuation_marks is None:
        punctuation_marks = DEFAULT_PUNCTUATION

    sentence_buffer = ""

    # Check if this is an async iterator (OpenAI) or sync iterator (Gemini)
    if hasattr(streaming_response, "__aiter__"):
        # OpenAI async streaming
        async for chunk in streaming_response:
            tool_calls = _extract_tool_calls_from_chunk(chunk)
            if tool_calls:
                yield {"tool_calls": tool_calls}

            content = _extract_content_from_chunk(chunk)
            sentence_buffer, complete_sentence = update_sentence_buffer(
                content,
                sentence_buffer,
                punctuation_marks,
                clean_text,
                min_sentence_length,
            )

            if complete_sentence:
                yield {"content": complete_sentence}
    else:
        # Gemini sync streaming - wrap in async to prevent blocking
        for chunk in streaming_response:
            content = _extract_content_from_chunk(chunk)
            sentence_buffer, complete_sentence = update_sentence_buffer(
                content,
                sentence_buffer,
                punctuation_marks,
                clean_text,
                min_sentence_length,
            )

            if complete_sentence:
                yield {"content": complete_sentence}

            # Yield control to prevent blocking the event loop
            await asyncio.sleep(0)

    # Handle any remaining text in buffer
    if sentence_buffer.strip():
        if clean_text:
            sentence_buffer = clean_text_for_speech(sentence_buffer)

        if sentence_buffer:
            # Force yield remaining content regardless of minimum length
            # This ensures no content is lost, especially for short phrases without punctuation
            yield {"content": sentence_buffer}


def _extract_tool_calls_from_chunk(chunk):
    if hasattr(chunk, "choices") and chunk.choices:
        if hasattr(chunk.choices[0], "delta") and hasattr(
            chunk.choices[0].delta, "tool_calls"
        ):
            return chunk.choices[0].delta.tool_calls or ""
    return ""


def _extract_content_from_chunk(chunk):
    """
    Extract content from streaming chunk, supporting OpenAI and Direct Gemini API formats only.

    Args:
        chunk: The streaming chunk from either OpenAI or Google Gemini (direct API)

    Returns:
        str: The content text from the chunk, or empty string if no content
    """
    # OpenAI format: chunk.choices[0].delta.content
    if hasattr(chunk, "choices") and chunk.choices:
        if hasattr(chunk.choices[0], "delta") and hasattr(
            chunk.choices[0].delta, "content"
        ):
            return chunk.choices[0].delta.content or ""

    # Google Gemini Direct API format: chunk.text
    if hasattr(chunk, "text"):
        return chunk.text or ""

    return ""


def update_sentence_buffer(
    content, sentence_buffer, punctuation_marks=None, clean_text=True, min_sentence_length=3
):
    if punctuation_marks is None:
        punctuation_marks = DEFAULT_PUNCTUATION

    if content:
        sentence_buffer += content

        # Check if we have a complete sentence (ends with punctuation)
        if any(punct in sentence_buffer for punct in punctuation_marks):
            # Find the last sentence boundary, BUT exclude periods in time abbreviations
            last_sentence_end = _find_last_sentence_boundary(sentence_buffer, punctuation_marks)

            if last_sentence_end != -1:
                # Extract complete sentence
                complete_sentence = sentence_buffer[: last_sentence_end + 1]

                # Keep remaining text in buffer
                sentence_buffer = sentence_buffer[last_sentence_end + 1 :]

                # Clean and yield complete sentence
                if clean_text:
                    complete_sentence = clean_text_for_speech(complete_sentence)

                if complete_sentence and len(complete_sentence.strip()) >= min_sentence_length:
                    return sentence_buffer, complete_sentence

    return sentence_buffer, None


def _find_last_sentence_boundary(text, punctuation_marks):
    """Find the last sentence boundary, excluding periods in common abbreviations like 'a.m.', 'p.m.', etc."""
    last_sentence_end = -1
    
    for punct in punctuation_marks:
        # Special handling for periods - skip those in abbreviations
        if punct == '.':
            # Collect all period positions, then filter from right to left
            period_positions = [i for i, ch in enumerate(text) if ch == '.']
            
            # Check periods from right to left, skipping abbreviation periods
            for i in reversed(period_positions):
                # Look back to see if this period is part of an abbreviation
                start_idx = max(0, i - 10)
                substring = text[start_idx:i+1]
                
                # Only skip if this is an incomplete abbreviation (like "p." in "p.m" without the "m" yet)
                # If period is at end of buffer with no following text, could be incomplete abbreviation
                if i + 1 >= len(text):  # Period is at end of text
                    # Check if it could be an incomplete abbreviation
                    if _is_incomplete_abbreviation(substring):
                        continue  # Skip this period, wait for more text
                
                # This is either a complete abbreviation or not an abbreviation - use it as boundary
                # But still skip if it's recognized as a complete abbreviation in middle of sentence
                if _is_abbreviation_period(substring):
                    # At end of text - check if it's preceded by a number/time (like "6 p." or "3:30 p.")
                    if i + 1 >= len(text):
                        # Extract the last word before the period
                        text_before = text[:i].strip()
                        words = text_before.split()
                        if words and len(words) >= 2:
                            prev_word = words[-2]
                            # If preceded by a number or time format, it's a complete time phrase
                            # Patterns: "6", "3:30", "8:00", etc.
                            if re.search(r'^\d+(?::\d+)?$', prev_word):
                                return i  # Return the period position
                        continue  # Skip, might have more content (incomplete abbreviation)
                    # In middle of text - only skip if no space after (embedded in word)
                    if text[i + 1] not in (' ', '\n', '\t'):
                        continue  # Part of longer word/phrase, skip
                    # Has space after - it's a sentence boundary
                
                return i
        else:
            # For other punctuation, just find the last occurrence
            pos = text.rfind(punct)
            if pos > last_sentence_end:
                last_sentence_end = pos
    
    # If we found a non-period punctuation, return it
    if last_sentence_end != -1:
        return last_sentence_end
    
    # No sentence boundary found
    return -1


def _is_abbreviation_period(text):
    """Check if the period at the end of text is part of a known abbreviation."""
    text = text.strip()
    if not text or not text.endswith('.'):
        return False
    
    # Remove the trailing period for analysis
    prefix = text[:-1]
    
    # For abbreviations to be skipped, they should be at the end of text with space/word boundary before
    # Get the last "word" (sequence of chars after the last space or from start)
    words = prefix.split()
    if not words:
        return False
    
    last_word = words[-1]
    
    # Time abbreviations: a.m, p.m, a., p. (also incomplete forms like "p." in streaming)
    if re.search(r'^[ap](?:\.|\.m)?$', last_word, re.IGNORECASE):
        return True
    
    # Titles and suffixes (must be standalone, not part of longer word)
    if re.search(r'^(Mr|Mrs|Ms|Dr|Prof|St|Rev|Sr|Jr)$', last_word, re.IGNORECASE):
        return True
    
    # Company suffixes
    if re.search(r'^(Inc|Ltd|Co|Corp)$', last_word, re.IGNORECASE):
        return True
    
    # Common abbreviations
    if re.search(r'^(etc|vs|e\.g|i\.e|et al)$', last_word, re.IGNORECASE):
        return True
    
    return False


def _is_incomplete_abbreviation(text):
    """Check if text ends with an incomplete abbreviation pattern (e.g., 'p.' but no 'm' following).
    
    Only return True if the pattern strongly suggests incompleteness.
    For "6 p.", it's likely a complete sentence with time, not an incomplete "p.m",
    so we should NOT treat it as incomplete.
    """
    text = text.strip()
    if not text or not text.endswith('.'):
        return False
    
    prefix = text[:-1]
    words = prefix.split()
    if not words:
        return False
    
    last_word = words[-1]
    
    # Only treat as incomplete if we have a VERY strong signal that more is coming
    # For example, at the very start of a number/sentence context with nothing before
    # But NOT for "6 p." which is a complete time phrase
    
    # Pattern: word that is just a single letter followed by period
    # BUT only if the word before it is also a single letter or abbreviation
    # Examples: "Mr." by itself is incomplete, "6 p." is complete
    if re.search(r'^[ap]$', last_word, re.IGNORECASE):
        # Check if there's a word before this single letter
        if len(words) >= 2:
            prev_word = words[-2]
            # If previous word is a number like "6", this is likely "6 p.m" (complete time phrase)
            # Treat as complete, not incomplete
            if re.search(r'^\d+$', prev_word):
                return False  # "6 p." is complete
            # If previous word is another single letter/abbrev, might be incomplete
            if len(prev_word) == 1:
                return True  # "a p." might be incomplete
        
        # Single letter alone with no context - ambiguous, but safer to treat as incomplete
        # (could be waiting for "m" in "p.m")
        # Actually, if it's at end of sentence naturally, let's treat as complete
        # The logic in _find_last_sentence_boundary will handle it with context
        return False  # Be permissive - let the context decide
    
    return False


def clean_text_for_speech(text):
    """
    Clean text for better speech synthesis by removing/replacing problematic characters,
    and ensure the sentence contains at least one character (including Unicode).

    Args:
        text: The text to clean

    Returns:
        str: Cleaned text suitable for speech synthesis, or empty string if no meaningful chars
    """
    if not text:
        return text

    # Remove markdown formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold** -> bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic* -> italic
    text = re.sub(r"__(.*?)__", r"\1", text)  # __bold__ -> bold
    text = re.sub(r"_(.*?)_", r"\1", text)  # _italic_ -> italic
    text = re.sub(r"~~(.*?)~~", r"\1", text)  # ~~strikethrough~~ -> strikethrough
    text = re.sub(r"`(.*?)`", r"\1", text)  # `code` -> code

    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)  # # Header -> Header

    # Smart replacements - only replace symbols that are truly problematic for speech
    # and preserve context where possible
    
    # Handle currency symbols more intelligently
    text = re.sub(r'\$(\d+(?:\.\d{2})?)', r'$\1', text)  # Keep $200 as $200, don't replace
    
    # Handle percentages
    text = re.sub(r'(\d+)%', r'\1 percent', text)  # 50% -> 50 percent
    
    # Handle ampersands in common contexts
    text = re.sub(r'\b&\b', ' and ', text)  # A & B -> A and B
    
    # Handle mathematical operators only in mathematical contexts
    # Don't replace +, =, <, > in normal text as they might be part of natural language
    
    # Handle truly problematic symbols for speech
    replacements = {
        "|": " or ",  # A|B -> A or B
        "\\": " backslash ",  # Only when needed
        "/": " slash ",  # Only when needed
        "^": " caret ",  # Only when needed
        "~": " tilde ",  # Only when needed
    }

    for symbol, replacement in replacements.items():
        text = text.replace(symbol, replacement)

    # Remove brackets and their content (often contains technical info)
    # But be more selective - don't remove if it's part of natural language
    text = re.sub(r"\[.*?\]", "", text)  # [link text] ->
    text = re.sub(r"\{.*?\}", "", text)  # {code} ->

    # Clean up URLs (replace with "link") - this is actually good
    text = re.sub(r"https?://\S+", "link", text)
    text = re.sub(r"www\.\S+", "link", text)

    # Clean up email addresses - this is also good
    text = re.sub(r"\S+@\S+\.\S+", "email address", text)

    # Clean up multiple spaces and newlines
    text = re.sub(r"\s+", " ", text)  # Multiple spaces -> single space
    text = re.sub(r"\n+", ". ", text)  # Multiple newlines -> period space

    # Remove leading/trailing whitespace
    text = text.strip()

    # Ensure the sentence contains at least one meaningful character (including Unicode)
    # This includes letters, numbers, CJK characters, and Indic scripts
    if not re.search(r"[\w\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u3300-\u33ff\ufe30-\ufe4f\u0900-\u097f\u0980-\u09ff\u0a00-\u0a7f\u0a80-\u0aff\u0b00-\u0b7f\u0b80-\u0bff\u0c00-\u0c7f\u0c80-\u0cff\u0d00-\u0d7f\u0d80-\u0dff\u0e00-\u0e7f\u0e80-\u0eff\u0f00-\u0fff]", text):
        return ""

    return text