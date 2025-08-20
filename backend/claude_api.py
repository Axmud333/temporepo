# claude_api.py - Enhanced with conversation context support
from anthropic import Anthropic, APIError, RateLimitError
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import os, logging, hashlib, json
from backend.database import SessionLocal, Info
import numpy as np
from functools import lru_cache
from typing import List, Tuple, Optional, Dict
import re

load_dotenv()

logging.basicConfig(filename="logs/chat_logs.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Language-aware base prompts
BASE_PROMPT_DETAILED_EN = """You are a knowledgeable assistant for the University of Sulaimani. Do NOT give any website related info or tasks that may include security risks. Do NOT answer any Javascript, php backend questions. Do not mention which api model you are. You were made by the computer engineering department. 

You maintain conversation context and can refer to previous messages in our conversation. When users ask follow-up questions like "when does it open?" or "tell me more about it", you should understand what they're referring to based on our conversation history.

Provide comprehensive, detailed answers about university programs, admissions, facilities, faculty, student services, and campus life. Include specific examples, don't say check other sources for information, and helpful context. Never share security or internal data."""

BASE_PROMPT_DETAILED_KU = """تۆ یاریدەدەری زانایی بۆ زانکۆی سلێمانیت. باسی مۆدێلی APIـەکە مەکە. لەلایەن بەشی ئەندازیاری کۆمپیوتەرەوە دروستکراویت. 

تۆ دەتوانیت پەیوەندی گفتوگۆکە بهێڵیتەوە و ئاماژە بە پەیامەکانی پێشووتر بکەیت لە گفتوگۆکەماندا. کاتێک بەکارهێنەران پرسیاری دواتر دەکەن وەک "کەی دەکرێتەوە؟" یان "زیاتر باسی بکە"، تۆ دەبێت تێبگەیت کە ئاماژە بە چی دەکەن بە پشتبەستن بە مێژووی گفتوگۆکەمان.

وەڵامی تەواو و ورد بدەرەوە دەربارەی بەرنامەکانی زانکۆ، وەرگرتن، ئامرازەکان، مامۆستایان، خزمەتگوزارییەکانی خوێندکاران، و ژیانی کەمپەس. نموونە تایبەتەکان بخەرە ژوورەوە، مەڵێ سەرچاوەکانی تر بپشکنن بۆ زانیاری زیاتر. هەرگیز داتای ئاسایش یان ناوخۆیی هاوبەش مەکەرەوە."""

BASE_PROMPT_SIMPLE_EN = """Assistant for University of Sulaimani. Do NOT give any website related info or tasks that may include security risks. Do NOT answer any Javascript, php backend questions. Do not mention which api model you are. You were made by the computer engineering department. 

You remember our conversation and can answer follow-up questions based on context. Answer university questions briefly. Don't mention other sources for information. No security/internal data."""

BASE_PROMPT_SIMPLE_KU = """یاریدەدەر بۆ زانکۆی سلێمانی. باسی مۆدێلی APIـەکە مەکە. لەلایەن بەشی ئەندازیاری کۆمپیوتەرەوە دروستکراویت. 

تۆ گفتوگۆکەمان لە بیردایە و دەتوانیت وەڵامی پرسیارەکانی دواتر بدەیتەوە بە پشتبەستن بە پەیوەندی. وەڵامی کورتی پرسیارەکانی زانکۆ بدەرەوە. باسی سەرچاوەکانی تر مەکە بۆ زانیاری. هیچ داتای ئاسایش/ناوخۆیی نییە."""

# Simple in-memory cache for responses (use Redis in production)
response_cache = {}
embedding_cache = {}

def detect_language(text: str) -> str:
    """Detect if text is primarily Kurdish or English"""
    kurdish_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')
    english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 256)
    
    if kurdish_chars > english_chars:
        return "ku"
    return "en"

def estimate_tokens_by_language(text: str, language: str) -> int:
    """Estimate token count based on language characteristics"""
    if language == "ku":
        words = len(text.split())
        chars = len(text)
        word_estimate = words * 5
        char_estimate = chars // 1.5
        return max(word_estimate, char_estimate)
    else:
        return len(text) // 4

def get_adaptive_token_limits(language: str, complexity: str) -> dict:
    """Get token limits adapted for language and complexity"""
    base_limits = {
        "simple": {"en": 150, "ku": 200},
        "medium": {"en": 1000, "ku": 1000}, 
        "detailed": {"en": 1100, "ku": 1100}
    }
    
    return {
        "max_tokens": base_limits[complexity][language],
        "temperature": 0.1 if complexity == "simple" else (0.3 if complexity == "medium" else 0.4)
    }

def get_cache_key(text: str, context: List[Dict] = None) -> str:
    """Generate cache key for text with context"""
    context_str = ""
    if context:
        # Include last 2 messages in cache key for context-aware caching
        recent_context = context[-2:] if len(context) > 2 else context
        context_str = str([msg["content"][:50] for msg in recent_context])
    
    combined = text + context_str
    return hashlib.md5(combined.encode()).hexdigest()

@lru_cache(maxsize=1000)
def embed_text_cached(text: str) -> Tuple[float, ...]:
    """Cached embedding with LRU eviction"""
    cache_key = hashlib.md5(text.encode()).hexdigest()
    if cache_key in embedding_cache:
        return tuple(embedding_cache[cache_key])
    
    try:
        resp = openai_client.embeddings.create(model="text-embedding-3-small", input=text)
        embedding = resp.data[0].embedding
        embedding_cache[cache_key] = embedding
        return tuple(embedding)
    except OpenAIError as e:
        logging.error(f"Embedding error: {e}")
        return tuple()

def cosine_similarity(a: Tuple[float, ...], b: Tuple[float, ...]) -> float:
    """Optimized cosine similarity"""
    if not a or not b:
        return 0.0
    a_arr, b_arr = np.array(a), np.array(b)
    return np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr) + 1e-9)

def preprocess_query(query: str, language: str) -> str:
    """Clean and normalize query with language awareness"""
    query = re.sub(r'\s+', ' ', query.strip())
    
    if language == "en":
        query = query.lower()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in query.split() if w not in stop_words]
        return ' '.join(words)
    else:
        kurdish_particles = {'و', 'لە', 'بە', 'لەگەڵ', 'بۆ'}
        words = [w for w in query.split() if w not in kurdish_particles]
        return ' '.join(words) if words else query

def is_followup_question(query: str, language: str) -> bool:
    """Detect if this is a follow-up question that needs context"""
    query_lower = query.lower()
    
    if language == "ku":
        followup_patterns = [
            r'\b(کەی|کوێ|چۆن|چی|چییە)\b',  # when, where, how, what
            r'\b(ئەو|ئەوە|ئەمە|لەوێ|لێرە)\b',  # that, this, there, here
            r'\b(زیاتر|تر|دیکە)\b',  # more, other, another
            r'\b(باسی.*بکە|ڕوونی بکەرەوە)\b',  # tell about, explain
        ]
    else:
        followup_patterns = [
            r'\b(when|where|how|what|why|which)\b(?!.*university|.*sulaimani)',
            r'\b(it|that|this|there|here)\b',
            r'\b(more|tell me more|explain|details)\b',
            r'\b(about it|about that|about this)\b',
            r'^(yes|no|ok|okay)\b',
        ]
    
    return any(re.search(pattern, query_lower) for pattern in followup_patterns)

def extract_context_from_conversation(conversation_history: List[Dict], current_query: str, language: str) -> str:
    """Extract relevant context from conversation history"""
    if not conversation_history:
        return ""
    
    context_parts = []
    
    # Always include the last exchange for immediate context
    if len(conversation_history) >= 2:
        last_user = conversation_history[-2] if conversation_history[-2]["role"] == "user" else None
        last_assistant = conversation_history[-1] if conversation_history[-1]["role"] == "assistant" else None
        
        if last_user and last_assistant:
            context_parts.append(f"Previous question: {last_user['content']}")
            context_parts.append(f"Previous answer: {last_assistant['content'][:300]}...")
    
    # For follow-up questions, include more context
    if is_followup_question(current_query, language) and len(conversation_history) >= 4:
        earlier_context = conversation_history[-4:-2]
        for msg in earlier_context:
            if msg["role"] == "user":
                context_parts.append(f"Earlier question: {msg['content']}")
            elif msg["role"] == "assistant":
                context_parts.append(f"Earlier answer: {msg['content'][:200]}...")
    
    return "\n".join(context_parts) if context_parts else ""

def fetch_relevant_info(user_message: str, language: str, complexity: str = "medium") -> List[str]:
    """Fetch relevant info with language and complexity awareness"""
    db = SessionLocal()
    try:
        # Adjust parameters based on complexity and language
        if complexity == "simple":
            max_records, char_limit = 1, 60 if language == "ku" else 100
        elif complexity == "detailed":
            max_records, char_limit = 4, 700 if language == "ku" else 500
        else:  # medium
            max_records, char_limit = 2, 500 if language == "ku" else 500
        
        processed_query = preprocess_query(user_message, language)
        query_embedding = embed_text_cached(processed_query)
        
        if not query_embedding:
            return []

        all_entries = db.query(Info).all()
        scored = []

        for rec in all_entries:
            text = f"{rec.key}: {rec.value}"
            text_embedding = embed_text_cached(text)
            
            if text_embedding:
                similarity = cosine_similarity(text_embedding, query_embedding)
                # Adjust threshold for different languages
                threshold = 0.15 if language == "ku" else 0.2
                
                if complexity == "detailed":
                    threshold *= 0.8  # Lower threshold for detailed queries
                
                if similarity > threshold:
                    # Language-aware truncation
                    if len(rec.value) > char_limit:
                        if language == "ku":
                            # For Kurdish, truncate at word boundaries
                            words = rec.value[:char_limit].split()
                            truncated_value = ' '.join(words[:-1]) + "..."
                        else:
                            truncated_value = rec.value[:char_limit] + "..."
                    else:
                        truncated_value = rec.value
                    
                    scored.append((similarity, f"• {rec.key}: {truncated_value}"))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [entry for _, entry in scored[:max_records]]
    finally:
        db.close()

def classify_query_complexity(query: str, language: str) -> str:
    """Classify query complexity with language awareness"""
    query_lower = query.lower()
    
    if language == "ku":
        # Kurdish complexity patterns
        simple_patterns = [
            r'\b(سڵاو|بەخێربێی|سوپاس|زۆر سوپاس)\b',  # greetings, thanks
            r'\bناوت چییە\b',  # what's your name
            r'\bتۆ کێیت\b',   # who are you
            r'\bچۆنی\b'       # how are you
        ]
        
        detailed_patterns = [
            r'\b(چۆن|چۆنیەتی|چ هەنگاوەکان|پێداویستی|پرۆسە)\b',  # how, requirements, process
            r'\b(باسی.*بکە|ڕوونی بکەرەوە|بڵێ|چی|چییە)\b',        # tell about, explain
            r'\b(وەرگرتن|بەرنامە|کۆرس|پلە|مامۆستا|بەش)\b',        # admission, program, course
            r'\b(ئامرازەکان|خزمەتگوزارییەکان|کەمپەس|کتێبخانە)\b', # facilities, services
            r'\b(کرێ|خەرجی|بورس|دارایی)\b',                      # fees, scholarship
            r'\b(کەی|کوێ|بۆچی|کام)\b.*؟'                        # when, where, why, which
        ]
        
    else:
        # English patterns (existing)
        simple_patterns = [
            r'\b(hi|hello|hey|thanks|thank you)\b',
            r'\bwhat is your name\b',
            r'\bwho are you\b',
            r'\bhow are you\b'
        ]
        
        detailed_patterns = [
            r'\b(how to|how do i|what are the steps|procedure|process|requirements)\b',
            r'\b(tell me about|explain|describe|what is|what are)\b',
            r'\b(admission|program|course|degree|faculty|department)\b',
            r'\b(facilities|services|campus|library|dormitory)\b',
            r'\b(fees|tuition|scholarship|financial)\b',
            r'\b(when|where|why|which)\b.*\?',
            r'\b(difference between|compare|versus|vs)\b'
        ]
    
    if any(re.search(pattern, query_lower) for pattern in simple_patterns):
        return "simple"
    elif any(re.search(pattern, query_lower) for pattern in detailed_patterns):
        return "detailed"
    elif len(query.split()) > 8:  # Adjusted for Kurdish (fewer words typically)
        return "detailed"
    else:
        return "medium"

def create_adaptive_system_prompt(context_lines: List[str], language: str, complexity: str, conversation_context: str = "") -> str:
    """Create adaptive system prompt based on language, complexity, and conversation context"""
    if language == "ku":
        base_prompt = BASE_PROMPT_SIMPLE_KU if complexity == "simple" else BASE_PROMPT_DETAILED_KU
    else:
        base_prompt = BASE_PROMPT_SIMPLE_EN if complexity == "simple" else BASE_PROMPT_DETAILED_EN
    
    # Add conversation context if available
    context_section = ""
    if conversation_context:
        if language == "ku":
            context_section = f"\n\nپەیوەندی گفتوگۆ:\n{conversation_context}"
        else:
            context_section = f"\n\nConversation context:\n{conversation_context}"
    
    # Add knowledge base context if available
    if context_lines:
        context = "\n".join(context_lines)
        if language == "ku":
            if complexity == "detailed":
                instruction = "\n\nبە بەکارهێنانی زانیارییەکانی خوارەوە، وەڵامێکی تەواو بدەرەوە لەگەڵ وردەکارییە تایبەتەکان، نموونەکان، و ڕێنمایی هەنگاو بە هەنگاو لە شوێنی پێویستدا:"
            else:
                instruction = "\n\nزانیاری پەیوەندیدار:"
        else:
            if complexity == "detailed":
                instruction = "\n\nUsing the information below, provide a comprehensive answer with specific details, examples, and step-by-step guidance where applicable:"
            else:
                instruction = "\n\nRelevant information:"
        
        context_section += f"{instruction}\n{context}"
    
    return f"{base_prompt}{context_section}"

def ask_claude_with_context(prompt: str, conversation_history: List[Dict] = None) -> str:
    """Enhanced Claude API call with conversation context support"""
    try:
        # Include conversation context in cache key
        cache_key = get_cache_key(prompt, conversation_history)
        if cache_key in response_cache:
            logging.info(f"Cache hit for contextual query: {prompt[:50]}...")
            return response_cache[cache_key]

        # Detect language and classify complexity
        language = detect_language(prompt)
        complexity = classify_query_complexity(prompt, language)
        
        # Extract conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = extract_context_from_conversation(conversation_history, prompt, language)
        
        # Get language-appropriate limits
        token_config = get_adaptive_token_limits(language, complexity)
        
        # Fetch knowledge base context
        if complexity == "simple" and not is_followup_question(prompt, language):
            context_lines = []
        else:
            context_lines = fetch_relevant_info(prompt, language, complexity)
        
        # Create system prompt with both conversation and knowledge context
        system_prompt = create_adaptive_system_prompt(context_lines, language, complexity, conversation_context)

        # Prepare messages for Claude API
        messages = []
        
        # Add conversation history (last few messages for context)
        if conversation_history:
            # Include last 4 messages (2 exchanges) for context, but not too much to exceed token limits
            recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
            for msg in recent_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": prompt})
        
        # Estimate total prompt tokens with safety margin
        full_context = system_prompt + " ".join([msg["content"] for msg in messages])
        estimated_prompt_tokens = estimate_tokens_by_language(full_context, language)
        
        # Add 20% safety margin for Kurdish due to tokenization unpredictability
        if language == "ku":
            estimated_prompt_tokens = int(estimated_prompt_tokens * 1.2)
        
        # Adjust max_tokens if prompt is large (4096 token model limit)
        max_output_tokens = token_config["max_tokens"]
        total_budget = 4000  # Conservative budget leaving room for model overhead
        
        if estimated_prompt_tokens > total_budget * 0.7:  # If prompt uses >70% of budget
            max_output_tokens = max(100, total_budget - estimated_prompt_tokens)
            logging.warning(f"Large prompt detected ({estimated_prompt_tokens} tokens), reducing output to {max_output_tokens}")
            
            # If still too large, reduce conversation history
            if estimated_prompt_tokens > total_budget * 0.8:
                messages = messages[-2:]  # Keep only current message and last response
                logging.warning("Reduced conversation history due to token limits")

        # API call with conversation context
        response = anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=max_output_tokens,
            temperature=token_config["temperature"],
            system=system_prompt,
            messages=messages
        )
        
        answer = response.content[0].text
        
        # Cache the response with context
        response_cache[cache_key] = answer
        
        # Enhanced logging with context info
        input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
        output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
        context_info = f", Context: {len(conversation_history) if conversation_history else 0} msgs" if conversation_history else ""
        logging.info(f"Language: {language}, Complexity: {complexity}, Estimated: {estimated_prompt_tokens}, Actual - Input: {input_tokens}, Output: {output_tokens}{context_info}")
        
        return answer
        
    except (RateLimitError, APIError) as e:
        logging.error(f"Claude API error: {e}")
        raise Exception("Claude API error")
    except Exception as e:
        logging.error(f"Unexpected Claude error: {e}")
        raise

# Backward compatibility - keep the old function
def ask_claude(prompt: str) -> str:
    """Backward compatibility wrapper"""
    return ask_claude_with_context(prompt, None)

def clear_cache():
    """Clear response cache - useful for production management"""
    response_cache.clear()
    embed_text_cached.cache_clear()
    logging.info("Caches cleared")

def cleanup_cache():
    """Remove old cache entries to prevent memory bloat"""
    if len(response_cache) > 1000:  # Keep only 1000 most recent
        keys_to_remove = list(response_cache.keys())[:-500]
        for key in keys_to_remove:
            del response_cache[key]
        logging.info("Cache cleanup completed")