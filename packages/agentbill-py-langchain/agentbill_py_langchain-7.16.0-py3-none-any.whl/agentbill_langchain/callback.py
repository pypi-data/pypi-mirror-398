"""AgentBill LangChain Callback Handler"""

import time
import hashlib
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult
except ImportError:
    raise ImportError(
        "langchain is not installed. Install with: pip install langchain"
    )

import requests


class AgentBillCallback(BaseCallbackHandler):
    """LangChain callback handler that sends usage data to AgentBill.
    
    Example:
        callback = AgentBillCallback(
            api_key="agb_your_key",
            base_url="https://your-instance.supabase.co",
            customer_id="customer-123"
        )
        
        llm = ChatOpenAI(callbacks=[callback])
        result = llm.invoke("Hello!")
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        customer_id: Optional[str] = None,
        external_customer_id: Optional[str] = None,  # Alias for customer_id
        account_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        external_agent_id: Optional[str] = None,  # Alias for agent_id
        event_name: Optional[str] = None,
        debug: bool = False,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        enable_cost_guard: bool = True
    ):
        """Initialize AgentBill callback.
        
        Args:
            api_key: AgentBill API key (get from dashboard)
            base_url: AgentBill base URL (e.g., https://xxx.supabase.co)
            customer_id: Optional customer ID for tracking (UUID format)
            external_customer_id: Optional external customer ID (alias for customer_id when non-UUID)
            account_id: Optional account ID for tracking
            agent_id: Optional agent ID for tracking (UUID format)
            external_agent_id: Optional external agent ID (alias for agent_id when non-UUID)
            event_name: Optional custom event name (default: 'langchain_llm_call')
            debug: Enable debug logging
            batch_size: Number of signals to batch before sending
            flush_interval: Seconds between automatic flushes
            daily_budget: Optional daily budget override (SDK-level stricter limit)
            monthly_budget: Optional monthly budget override (SDK-level stricter limit)
            enable_cost_guard: Enable Cost Guard validation (default: True)
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        # Support external_customer_id as alias for customer_id
        self.customer_id = customer_id or external_customer_id
        self.external_customer_id = external_customer_id  # Store separately for tracking
        self.account_id = account_id
        # Support external_agent_id as alias for agent_id
        self.agent_id = agent_id or external_agent_id
        self.external_agent_id = external_agent_id  # Store separately for tracking
        self.event_name = event_name or 'langchain_llm_call'
        self.debug = debug
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.enable_cost_guard = enable_cost_guard
        self.enable_cost_guard = enable_cost_guard
        
        # Track active LLM calls
        self._active_runs: Dict[str, Dict[str, Any]] = {}
        
        # Batch queue
        self._signal_queue: List[Dict[str, Any]] = []
        self._last_flush = time.time()
        
        if self.debug:
            print(f"[AgentBill] Initialized with base_url={self.base_url}")
            if enable_cost_guard:
                print(f"[AgentBill] Cost Guard enabled - will validate before LLM calls")
    
    def _validate_request(self, model: str, prompts: List[str]) -> Dict:
        """
        Call ai-cost-guard-router for pre-flight validation
        
        v7.3.0 CRITICAL FIX: ALWAYS call validation - server decides based on:
        - Company budgets (via api_key)
        - Customer budgets (if customer_id provided)
        - Agent budgets (if agent_id provided)
        
        SDK budgets are OPTIONAL overrides that add stricter limits.
        """
        # v7.3.0: ALWAYS validate when Cost Guard is enabled - removed customer_id check
        if not self.enable_cost_guard:
            return {"allowed": True}
        
        url = f"{self.base_url}/functions/v1/ai-cost-guard-router"
        
        # Convert LangChain prompts to messages format for router
        messages = [{"role": "user", "content": prompt} for prompt in prompts]
        
        payload = {
            "api_key": self.api_key,
            "customer_id": self.customer_id,
            "model": model,
            "messages": messages,
            "daily_budget_override": self.daily_budget,
            "monthly_budget_override": self.monthly_budget,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            # Handle HTTP errors explicitly
            if response.status_code >= 500:
                if self.debug:
                    print(f"[AgentBill Cost Guard] ⚠️ Router server error {response.status_code} (failing open)")
                return {"allowed": True, "reason": "Router server error"}
            elif response.status_code >= 400:
                if self.debug:
                    print(f"[AgentBill Cost Guard] ❌ Router rejected {response.status_code}")
                return {"allowed": False, "reason": f"Router error: {response.text}"}
            
            result = response.json()
            
            if self.debug:
                print(f"[AgentBill Cost Guard] Validation result: {result}")
                if not result.get("allowed"):
                    print(f"[AgentBill Cost Guard] ❌ BLOCKED: {result.get('reason', 'Unknown')}")
            
            return result
        except Exception as e:
            if self.debug:
                print(f"[AgentBill Cost Guard] ⚠️ Validation error: {e} (failing open)")
            return {"allowed": True, "reason": "Validation network error"}
    
    def _hash_prompt(self, text: str) -> str:
        """Hash prompt for privacy."""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _extract_provider(self, serialized: Dict[str, Any]) -> str:
        """Extract provider from LLM serialization."""
        # Check id field
        for id_item in serialized.get("id", []):
            if "openai" in id_item.lower():
                return "openai"
            if "anthropic" in id_item.lower():
                return "anthropic"
            if "cohere" in id_item.lower():
                return "cohere"
            if "bedrock" in id_item.lower():
                return "bedrock"
        
        # Check kwargs
        kwargs = serialized.get("kwargs", {})
        if "openai" in str(kwargs).lower():
            return "openai"
        if "anthropic" in str(kwargs).lower():
            return "anthropic"
        
        return "unknown"
    
    def _extract_model(self, serialized: Dict[str, Any]) -> str:
        """Extract model name from LLM serialization."""
        # Try model_name in kwargs
        kwargs = serialized.get("kwargs", {})
        if "model_name" in kwargs:
            return kwargs["model_name"]
        if "model" in kwargs:
            return kwargs["model"]
        
        # Try id field
        for id_item in serialized.get("id", []):
            if "gpt" in id_item.lower():
                return id_item
            if "claude" in id_item.lower():
                return id_item
        
        return "unknown"
    
    def _send_signal(self, signal: Dict[str, Any]) -> None:
        """Send signal to AgentBill."""
        try:
            url = f"{self.base_url}/functions/v1/record-signals"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            if self.debug:
                print(f"[AgentBill] Sending signal: {signal.get('event_name')}")
            
            response = requests.post(url, json=[signal], headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[AgentBill] Error sending signal: {response.status_code} {response.text}")
            elif self.debug:
                print(f"[AgentBill] Signal sent successfully")
                
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] Error sending signal: {e}")
    
    def _queue_signal(self, signal: Dict[str, Any]) -> None:
        """Add signal to queue and flush if needed."""
        self._signal_queue.append(signal)
        
        # Flush if batch size reached or interval exceeded
        now = time.time()
        should_flush = (
            len(self._signal_queue) >= self.batch_size or
            (now - self._last_flush) >= self.flush_interval
        )
        
        if should_flush:
            self.flush()
    
    def flush(self) -> None:
        """Flush queued signals to AgentBill."""
        if not self._signal_queue:
            return
        
        try:
            url = f"{self.base_url}/functions/v1/record-signals"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            if self.debug:
                print(f"[AgentBill] Flushing {len(self._signal_queue)} signals")
            
            response = requests.post(
                url,
                json=self._signal_queue,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self._signal_queue.clear()
                self._last_flush = time.time()
                if self.debug:
                    print(f"[AgentBill] Flush successful")
            else:
                print(f"[AgentBill] Flush error: {response.status_code} {response.text}")
                
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] Flush error: {e}")
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """
        Called when LLM starts.
        
        CRITICAL: Now includes Cost Guard validation BEFORE LLM call.
        """
        run_id = kwargs.get("run_id") or str(UUID(int=0))
        
        # Extract metadata
        provider = self._extract_provider(serialized)
        model = self._extract_model(serialized)
        
        # v7.3.0 CRITICAL FIX: ALWAYS validate when Cost Guard enabled (removed customer_id check)
        if self.enable_cost_guard:
            validation = self._validate_request(model, prompts)
            
            # Block if not allowed
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Request blocked by Cost Guard")
                if self.debug:
                    print(f"[AgentBill Cost Guard] ❌ BLOCKING LLM call: {error_msg}")
                
                # Raise exception to prevent LLM call
                error = Exception(f"AgentBill Cost Guard: {error_msg}")
                error.code = "BUDGET_EXCEEDED" if "budget" in error_msg.lower() else \
                             "RATE_LIMIT_EXCEEDED" if "rate" in error_msg.lower() else \
                             "POLICY_VIOLATION"
                raise error
            
            # v7.6.5: Check for cached response from semantic cache
            # The response_data is a full OpenAI ChatCompletion-compatible object
            if validation.get("cached") and validation.get("response_data"):
                if self.debug:
                    print(f"[AgentBill] ✓ Cache hit - will return cached ChatCompletion object")
                # Store cached response to return in on_llm_end
                cached_response = validation.get("response_data")
                if isinstance(cached_response, dict):
                    cached_response["_agentbill_cached"] = True
                self._cached_response = cached_response
            
            # Validation passed
            if self.debug:
                print(f"[AgentBill Cost Guard] ✓ Validation passed")
            
            # Store request_id for tracking correlation
            validation_request_id = validation.get("request_id")
        else:
            validation_request_id = None
        
        # Store run info including run_id for potential trace correlation
        self._active_runs[str(run_id)] = {
            "start_time": time.time(),
            "prompts": prompts,
            "provider": provider,
            "model": model,
            "prompt_hash": self._hash_prompt(prompts[0]) if prompts else None,
            "prompt_sample": prompts[0][:200] if prompts else None,
            "run_id": str(run_id),
            "request_id": validation_request_id,  # For audit correlation
        }
        
        if self.debug:
            print(f"[AgentBill] LLM started: {model} ({provider})")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends."""
        run_id = str(kwargs.get("run_id", ""))
        run_info = self._active_runs.pop(run_id, None)
        
        if not run_info:
            return
        
        # Calculate latency
        latency_ms = int((time.time() - run_info["start_time"]) * 1000)
        
        # Extract token usage
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        total_tokens = token_usage.get("total_tokens", prompt_tokens + completion_tokens)
        
        # v7.16.0: Track OpenAI native prompt prefix caching (different from AgentBill semantic cache)
        # This is OpenAI's ~50% discount on repeated prompt prefixes, NOT our full semantic cache
        prompt_tokens_details = token_usage.get("prompt_tokens_details", {})
        cached_input_tokens = prompt_tokens_details.get("cached_tokens", 0) if prompt_tokens_details else 0
        completion_tokens_details = token_usage.get("completion_tokens_details", {})
        reasoning_output_tokens = completion_tokens_details.get("reasoning_tokens", 0) if completion_tokens_details else 0
        
        # Extract response content for caching
        response_content = ""
        if response.generations and len(response.generations) > 0:
            first_gen = response.generations[0]
            if first_gen and len(first_gen) > 0:
                response_content = first_gen[0].text if hasattr(first_gen[0], 'text') else str(first_gen[0])
        
        # Build signal with optional trace and Cost Guard correlation
        signal = {
            "event_name": self.event_name,
            "model": run_info["model"],
            "provider": run_info["provider"],
            "prompt_hash": run_info["prompt_hash"],
            "prompt_sample": run_info["prompt_sample"],
            "metrics": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                # v7.16.0: Include OpenAI native cache metrics
                "cached_input_tokens": cached_input_tokens,
                "reasoning_output_tokens": reasoning_output_tokens,
            },
            "latency_ms": latency_ms,
            "data_source": "langchain",
            "metadata": {
                "langchain_run_id": run_info.get("run_id", ""),
            },
        }
        
        # Add Cost Guard request_id for audit linking
        if run_info.get("request_id"):
            signal["request_id"] = run_info["request_id"]
        
        # Add customer/account if provided with UUID detection
        if self.customer_id:
            # Check if UUID format - send as customer_id, else customer_external_id
            import re
            uuid_regex = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            is_uuid = bool(uuid_regex.match(self.customer_id))
            if is_uuid:
                signal["customer_id"] = self.customer_id
            else:
                signal["customer_external_id"] = self.customer_id
        if self.account_id:
            signal["account_id"] = self.account_id
        
        # Queue signal
        self._queue_signal(signal)
        
        # v7.5.0: Cache AI response for semantic caching
        if response_content and run_info.get("prompt_hash"):
            self._cache_response(
                model=run_info["model"],
                prompt_hash=run_info["prompt_hash"],
                response_content=response_content,
                tokens_used=total_tokens
            )
        
        if self.debug:
            print(f"[AgentBill] LLM ended: {total_tokens} tokens, {latency_ms}ms")
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        run_id = str(kwargs.get("run_id", ""))
        self._active_runs.pop(run_id, None)
        
        if self.debug:
            print(f"[AgentBill] LLM error: {error}")
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when chain starts."""
        if self.debug:
            chain_name = serialized.get("id", ["unknown"])[-1]
            print(f"[AgentBill] Chain started: {chain_name}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain ends."""
        if self.debug:
            print(f"[AgentBill] Chain ended")
    
    def track_revenue(
        self,
        event_name: str,
        revenue: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track revenue for profitability analysis.
        
        Args:
            event_name: Event name (e.g., "chat_completion")
            revenue: Revenue amount (what you charged)
            metadata: Additional metadata
        """
        signal = {
            "event_name": event_name,
            "conversion_value": revenue,
            "revenue_source": "langchain",
            "data": metadata or {},
        }
        
        if self.customer_id:
            # Check if UUID format - send as customer_id, else customer_external_id
            import re
            uuid_regex = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            is_uuid = bool(uuid_regex.match(self.customer_id))
            if is_uuid:
                signal["customer_id"] = self.customer_id
            else:
                signal["customer_external_id"] = self.customer_id
        if self.account_id:
            signal["account_id"] = self.account_id
        
        self._queue_signal(signal)
        
        if self.debug:
            print(f"[AgentBill] Revenue tracked: ${revenue}")
    
    def _cache_response(
        self,
        model: str,
        prompt_hash: str,
        response_content: str,
        tokens_used: int = 0,
        cost: float = 0.0
    ) -> None:
        """
        Cache AI response for semantic caching (v7.5.0).
        Fire-and-forget - errors are logged but don't block.
        """
        try:
            url = f"{self.base_url}/functions/v1/cache-ai-response"
            
            # v7.15.2: Estimate prompt/completion tokens from total
            # LangChain often only provides total_tokens, so we estimate
            prompt_tokens = int(tokens_used * 0.3) if tokens_used > 0 else 0
            completion_tokens = tokens_used - prompt_tokens if tokens_used > 0 else 0
            
            payload = {
                "api_key": self.api_key,
                "prompt_hash": prompt_hash,
                "response_content": response_content,
                "model": model,
                "tokens_used": tokens_used,
                # v7.15.2: Send separate token counts for accurate cache cost calculations
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost": cost,
                "customer_id": self.customer_id,
                "agent_id": self.agent_id
            }
            
            requests.post(url, json=payload, timeout=5)
            
            if self.debug:
                print(f"[AgentBill] Response cached for semantic caching")
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] Cache response failed: {e}")
    
    def __del__(self):
        """Flush on cleanup."""
        self.flush()
