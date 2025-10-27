import os
import requests
import logging
import json
import traceback
from flask import current_app

# --- Core Dependencies for LLM-Powered Search ---
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# 🚨 CHANGE: Import GroqService
try:
    from app.groq_service import GroqService 
    LLM_SERVICE_AVAILABLE = True
except ImportError:
    LLM_SERVICE_AVAILABLE = False
    
# --- Azure AI Search Dependencies - REMOVED ---
# Azure AI Search has been removed from this implementation


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Provides LLM-powered web search functionality (Tavily + Groq)
    and specific internal data retrieval from Azure AI Search (no fallbacks).
    """
    
    def __init__(self):
        """Initialize data loader with only necessary services."""
        if not (TAVILY_AVAILABLE and LLM_SERVICE_AVAILABLE):
            raise RuntimeError("LLM-powered search cannot be initialized. Missing 'tavily-python' or 'app.groq_service'.")
        
        # Azure AI Search removed - using database service instead
        self.search_service = None
        
        # 🚨 CHANGE: Use GroqService
        self.llm_service = GroqService()
        logger.info('DataLoader initialized with LLM and Tavily services (Azure AI Search removed).')

# --- Internal Data Retrieval Methods (Azure AI Search ONLY) ---
    
    def _check_search_service(self):
        if not (self.search_service and self.search_service.is_available()):
            logger.error('Azure AI Search not available. Cannot perform internal data search.')
            return False
        return True

    def search_data(self, query, top=5):
        if not self._check_search_service(): return []
        try: return self.search_service.search_documents(query, top=top)
        except Exception as e:
            logger.error(f'Azure AI Search document search error: {str(e)}')
            return []
    
    def get_company_info(self):
        if not self._check_search_service(): return None
        try:
            results = self.search_service.search_company_info("*") 
            if results: return results[0]
            return None
        except Exception as e:
            logger.error(f'Azure AI Search company info error: {str(e)}')
            return None
    
    def get_product_data(self):
        if not self._check_search_service(): return []
        try:
            results = self.search_service.search_product_info("*")
            return results
        except Exception as e:
            logger.error(f'Azure AI Search product data error: {str(e)}')
            return []

# --- Exclusive LLM-Powered Web Search Method (Constrained) ---
    
    def search_web(self, query):
        """
        Perform LLM-powered web search exclusively using Tavily for results and Groq for synthesis.
        Applies domain constraints via ALLOWED_SEARCH_DOMAINS.
        """
        logger.info(f"🔍 Web search requested for query: {query}")
        
        tavily_key = current_app.config.get('TAVILY_API_KEY')
        groq_api_key = current_app.config.get('GROQ_API_KEY')
        
        # 🚨 CHANGE: Get allowed domains from config
        allowed_domains = current_app.config.get('ALLOWED_SEARCH_DOMAINS', [])
        
        missing_keys = []
        if not tavily_key:
            missing_keys.append('TAVILY_API_KEY')
        if not groq_api_key:
            missing_keys.append('GROQ_API_KEY')
        
        if missing_keys:
            logger.error(f"Required API keys for LLM-powered search are not configured. Missing: {', '.join(missing_keys)}")
            return []

        if not (TAVILY_AVAILABLE and LLM_SERVICE_AVAILABLE):
             logger.error("Tavily or GroqService dependencies are missing. Cannot perform web search.")
             return []

        try:
            # 🚨 CRITICAL CHANGE: Pass allowed_domains to the internal search function
            results = self._llm_powered_search(query, tavily_key, allowed_domains)
            if results:
                logger.info(f"LLM-powered search successful for: {query}")
                return results
        except Exception as e:
            error_msg = f"Critical LLM-powered search orchestration error: {str(e)}"
            logger.error(error_msg)
            
        logger.warning(f"LLM-powered web search failed for query: {query}")
        return []

    def _llm_powered_search(self, query, tavily_api_key, include_domains=None):
        """Perform LLM-powered web search using Tavily for results and Groq for synthesis."""
        try:
            logger.info(f"🔍 STARTING LLM-POWERED SEARCH for query: {query}")
            
            # 1. Get raw search results from Tavily (Constrained by domains)
            client = TavilyClient(api_key=tavily_api_key)
            logger.info(f"🔎 Getting raw search results from Tavily for: {query}. Constrained to domains: {include_domains}")
            
            tavily_response = client.search(
                query=query, 
                search_depth="advanced", 
                max_results=5,
                include_answer=False, 
                include_raw_content=False,
                include_domains=include_domains if include_domains else None
            )
            raw_search_results = self._format_tavily_results(tavily_response)
            
            if not raw_search_results:
                logger.warning("No raw search results found from Tavily or within the allowed domains.")
                return []
            
            # 2. Format search results for the LLM context
            search_context = ""
            for i, result in enumerate(raw_search_results):
                snippet_content = result.get('snippet', '')[:800] 
                search_context += f"[Source {i+1}] {result['title']}\n"
                search_context += f"URL: {result['url']}\n"
                search_context += f"Content: {snippet_content}\n\n"
            
            # 3. Create a prompt for the LLM to synthesize the search results
            prompt = f"""You are a helpful AI research assistant. Based **only** on the following search results, provide a comprehensive answer to the user's query: "{query}"

Search Results:
{search_context}

Please synthesize the information from these sources to provide a thorough and accurate answer. 
**Do not invent information**. If the search results do not contain the answer, state that clearly, for example: "The provided search results do not contain sufficient information to answer the query."
"""
            
            # 4. Call Groq API directly for synthesis
            logger.info("🤖 Calling Groq API to synthesize search results")
            
            response = self.llm_service.generate_completion( # Use self.llm_service (GroqService)
                messages=[
                    {"role": "system", "content": "You are a helpful AI research assistant that synthesizes information from search results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            if not response:
                logger.warning("No synthesis response from Groq API.")
                return [] 
            
            # 5. Format the results
            formatted_results = [{
                'title': f"AI-Synthesized Answer for: {query}",
                'url': "AI-generated research summary",
                'snippet': response 
            }]
            
            formatted_results.extend(raw_search_results)
            logger.info(f"✅ LLM-powered search completed successfully")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Critical Error in LLM-powered search: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
            
    def _format_tavily_results(self, response):
        """Format Tavily search results to match our standard format"""
        formatted = []
        if 'results' in response:
            for result in response['results']:
                formatted.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('content', '')
                })
        return formatted