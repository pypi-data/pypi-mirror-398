"""
LangChain Integration - Automatic instrumentation for LangChain agents
"""
try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

if LANGCHAIN_AVAILABLE:
    from agenttrace.core.tracer import Tracer, Mode
    
    class AgentTraceCallback(BaseCallbackHandler):
        """LangChain callback handler that integrates with AgentTrace"""
        
        def __init__(self):
            self.tracer = Tracer.get_instance()
            super().__init__()
        
        def on_llm_start(self, serialized, prompts, **kwargs):
            """Called when LLM starts"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_llm_start", {
                    "prompts": prompts,
                    "serialized": str(serialized)
                })
        
        def on_llm_end(self, response: LLMResult, **kwargs):
            """Called when LLM ends"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_llm_end", {
                    "generations": [[gen.text for gen in gen_list] for gen_list in response.generations],
                    "llm_output": response.llm_output
                })
        
        def on_llm_error(self, error, **kwargs):
            """Called when LLM errors"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_llm_error", {
                    "error": str(error),
                    "error_type": type(error).__name__
                })
        
        def on_chain_start(self, serialized, inputs, **kwargs):
            """Called when chain starts"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_chain_start", {
                    "inputs": inputs,
                    "name": serialized.get("name", "unknown")
                })
        
        def on_chain_end(self, outputs, **kwargs):
            """Called when chain ends"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_chain_end", {
                    "outputs": outputs
                })
        
        def on_tool_start(self, serialized, input_str, **kwargs):
            """Called when tool starts"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_tool_start", {
                    "input": input_str,
                    "tool": serialized.get("name", "unknown")
                })
        
        def on_tool_end(self, output, **kwargs):
            """Called when tool ends"""
            if self.tracer.mode == Mode.RECORD:
                self.tracer.record_event("langchain_tool_end", {
                    "output": output
                })
    
    def setup_langchain_integration():
        """Setup LangChain integration - returns callback handler"""
        if not LANGCHAIN_AVAILABLE:
            print("⚠️  LangChain not installed. Install with: pip install langchain")
            return None
        
        print("AgentTrace: LangChain Integration Active")
        return AgentTraceCallback()
else:
    def setup_langchain_integration():
        """LangChain not available"""
        return None

