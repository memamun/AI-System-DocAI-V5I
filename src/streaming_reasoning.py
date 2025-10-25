"""
Streaming Reasoning Engine for AI-System-DocAI V5I
Provides real-time streaming of LLM reasoning process with live thinking display
"""
from __future__ import annotations
import json
import logging
import time
import re
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Generator, Tuple

from llm import BaseLLM
from config import config_manager

logger = logging.getLogger(__name__)

@dataclass
class StreamingReasoningResult:
    """Streaming reasoning result with real-time updates"""
    answer: str = ""
    reasoning_chain: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    source_citations: List[Dict[str, Any]] = field(default_factory=list)
    supporting_facts: List[str] = field(default_factory=list)
    alternative_interpretations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    current_step: str = ""
    is_complete: bool = False
    
    def to_dict(self):
        return asdict(self)

class StreamingReasoningEngine:
    """
    Streaming reasoning engine that provides real-time updates of the thinking process
    """
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.config = config_manager.config.reasoning
        logger.info(f"StreamingReasoningEngine initialized with LLM: {self.llm.name}")
    
    def process_query_stream(self, query: str, context: List[Dict[str, Any]]) -> Generator[StreamingReasoningResult, None, None]:
        """
        Process query with streaming reasoning updates
        """
        start_time = time.time()
        
        if not context:
            logger.warning("No context provided for reasoning.")
            result = StreamingReasoningResult(
                answer="No relevant documents found to answer the query.",
                reasoning_chain=["No document context was retrieved."],
                confidence_score=0.0,
                metadata={
                    "query_time_ms": int((time.time() - start_time) * 1000),
                    "llm_backend": self.llm.name,
                    "device_used": config_manager.get_llm_device()
                },
                is_complete=True
            )
            yield result
            return
        
        # Generate prompts
        system_prompt, user_prompt = self._generate_streaming_prompt(query, context)
        
        try:
            # Initialize result
            result = StreamingReasoningResult(
                metadata={
                    "query_time_ms": 0,
                    "llm_backend": self.llm.name,
                    "device_used": config_manager.get_llm_device()
                }
            )
            
            # Stream the response
            full_response = ""
            current_step = ""
            step_content = []
            
            for chunk in self.llm.generate_stream(system_prompt, user_prompt, self.config.max_tokens):
                full_response += chunk
                
                # Update current step
                result.current_step = self._extract_current_step(full_response)
                
                # Extract partial answer
                partial_answer = self._extract_partial_answer(full_response)
                if partial_answer and partial_answer != result.answer:
                    result.answer = partial_answer
                
                # Extract reasoning chain
                reasoning_chain = self._extract_reasoning_chain_streaming(full_response)
                if reasoning_chain != result.reasoning_chain:
                    result.reasoning_chain = reasoning_chain
                
                # Update metadata
                result.metadata["query_time_ms"] = int((time.time() - start_time) * 1000)
                
                yield result
            
            # Final processing
            result.is_complete = True
            result.answer = self._extract_final_answer(full_response)
            result.reasoning_chain = self._extract_reasoning_chain_streaming(full_response)
            result.source_citations = self._extract_citations_streaming(full_response, context)
            result.supporting_facts = self._extract_supporting_facts_streaming(full_response)
            result.alternative_interpretations = self._extract_alternatives_streaming(full_response)
            result.confidence_score = self._calculate_confidence_score(result)
            result.metadata["query_time_ms"] = int((time.time() - start_time) * 1000)
            
            # Generate well-organized final answer from structured JSON data
            result.answer = self._generate_organized_answer_from_json(result)
            
            logger.info(f"Streaming reasoning completed in {result.metadata['query_time_ms']}ms")
            yield result
            
        except Exception as e:
            logger.error(f"Error during streaming LLM reasoning: {e}", exc_info=True)
            
            # Check if it's an API configuration error
            error_msg = str(e)
            if "API key" in error_msg or "not set" in error_msg:
                user_msg = "API configuration required. Please click 'Configure' to set up your API key and endpoint."
            elif "Connection error" in error_msg or "protocol" in error_msg:
                user_msg = "Connection error. Please check your API endpoint URL and internet connection."
            else:
                user_msg = f"Error: {error_msg}"
            
            result = StreamingReasoningResult(
                answer=user_msg,
                reasoning_chain=[f"Configuration Error: {user_msg}"],
                confidence_score=0.0,
                metadata={
                    "query_time_ms": int((time.time() - start_time) * 1000),
                    "llm_backend": self.llm.name,
                    "device_used": config_manager.get_llm_device(),
                    "error": str(e)
                },
                is_complete=True
            )
            yield result
    
    def _generate_streaming_prompt(self, query: str, context: List[Dict[str, Any]]) -> Tuple[str, str]:
        """Generate system and user prompts optimized for streaming"""
        system_prompt = (
            "You are an expert document analysis AI with advanced reasoning capabilities. "
            "You use a 'slow-thinking' approach, showing your reasoning process step by step. "
            "Think out loud as you work through the problem, then provide a clear final answer. "
            "Your response will be streamed in real-time, so structure it clearly with step headers."
        )
        
        context_text = "\n\n".join([
            f"--- Document: {item.get('file', 'Unknown')} (Page: {item.get('page', 'N/A')}) --- \n{item.get('text', '')}"
            for item in context
        ])
        
        user_prompt = f"""Here are the relevant document snippets:

{context_text}

Question: {query}

Please think through this step by step and provide your reasoning process in real-time. Show your thinking as you work:

STEP 1 - ANALYSIS:
Let me analyze what this question is asking for...

STEP 2 - INFORMATION GATHERING:
From the provided context, I can see that... [Reference specific snippets with [1], [2], etc.]

STEP 3 - REASONING:
Based on the information gathered, I can conclude that...

STEP 4 - SYNTHESIS:
Putting this all together, the answer is...

FINAL ANSWER:
[Provide your complete, well-reasoned answer here]

IMPORTANT: 
- Use [1], [2], [3] to cite specific document snippets
- Show your reasoning process step by step
- Be conversational and explain your thinking
- Reference the document sources in your reasoning"""
        
        return system_prompt, user_prompt
    
    def _extract_current_step(self, response: str) -> str:
        """Extract the current step being worked on"""
        lines = response.split('\n')
        current_step = ""
        
        for line in lines:
            line = line.strip()
            if re.match(r'STEP \d+', line.upper()):
                current_step = line
            elif "FINAL ANSWER:" in line.upper():
                current_step = "FINAL ANSWER"
                break
        
        return current_step
    
    def _extract_partial_answer(self, response: str) -> str:
        """Extract partial answer as it's being generated with progressive building"""
        lines = response.split('\n')
        
        # Look for FINAL ANSWER section first
        final_answer_started = False
        answer_lines = []
        
        for line in lines:
            line = line.strip()
            if "FINAL ANSWER:" in line.upper():
                final_answer_started = True
                # Extract the answer part after "FINAL ANSWER:"
                answer_part = line.split(":", 1)
                if len(answer_part) > 1:
                    answer_lines.append(answer_part[1].strip())
                continue
            
            if final_answer_started and line:
                answer_lines.append(line)
        
        # If we found FINAL ANSWER section, format it properly
        if answer_lines:
            # Join lines while preserving structure
            answer_text = '\n'.join(answer_lines).strip()
            return self._format_answer_structure(answer_text)
        
        # If no FINAL ANSWER yet, build progressive answer from content
        content_lines = []
        in_reasoning_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering a reasoning section
            if any(indicator in line.upper() for indicator in ['STEP', 'ANALYSIS:', 'REASONING:', 'INFORMATION GATHERING:', 'SYNTHESIS:']):
                in_reasoning_section = True
                continue
            
            # Skip reasoning headers and bullets
            if (line.startswith('**') or 
                line.startswith('-') or 
                line.startswith('*') or
                line.startswith('STEP')):
                continue
            
            # Collect substantial content
            if len(line) > 15 and not in_reasoning_section:
                content_lines.append(line)
        
        # Return the accumulated content
        if content_lines:
            return ' '.join(content_lines).strip()
        
        return ""
    
    def _extract_final_answer(self, response: str) -> str:
        """Extract the final answer from complete response"""
        lines = response.split('\n')
        
        # Look for FINAL ANSWER section
        final_answer_started = False
        answer_lines = []
        
        for line in lines:
            line = line.strip()
            if "FINAL ANSWER:" in line.upper():
                final_answer_started = True
                # Extract the answer part after "FINAL ANSWER:"
                answer_part = line.split(":", 1)
                if len(answer_part) > 1:
                    answer_lines.append(answer_part[1].strip())
                continue
            
            if final_answer_started and line:
                answer_lines.append(line)
        
        if answer_lines:
            return ' '.join(answer_lines).strip()
        
        # Fallback: use the last substantial sentence
        for line in reversed(lines):
            line = line.strip()
            if (line and 
                not line.startswith('STEP') and 
                not line.startswith('**') and
                len(line) > 20):
                return line
        
        return "No clear answer found in response."
    
    def _extract_reasoning_chain_streaming(self, response: str) -> List[str]:
        """Extract reasoning chain from streaming response"""
        reasoning = []
        lines = response.split('\n')
        
        current_step = None
        step_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for various step header patterns
            step_patterns = [
                r'STEP \d+',  # STEP 1, STEP 2, etc.
                r'### STEP \d+',  # ### STEP 1, ### STEP 2, etc.
                r'STEP \d+ - \w+',  # STEP 1 - ANALYSIS, etc.
                r'### STEP \d+ - \w+',  # ### STEP 1 - ANALYSIS, etc.
            ]
            
            is_step_header = False
            for pattern in step_patterns:
                if re.match(pattern, line.upper()):
                    is_step_header = True
                    break
            
            if is_step_header:
                # Save previous step if exists
                if current_step and step_content:
                    reasoning.append(f"{current_step}: {' '.join(step_content)}")
                
                # Start new step
                current_step = line
                step_content = []
                continue
            
            # Skip FINAL ANSWER section
            if "FINAL ANSWER:" in line.upper():
                break
            
            # Collect content for current step
            if current_step and line:
                line = re.sub(r'^[-*]\s*', '', line)    # Remove bullets
                if line and not any(re.match(pattern, line.upper()) for pattern in step_patterns):
                    step_content.append(line)
        
        # Add the last step
        if current_step and step_content:
            reasoning.append(f"{current_step}: {' '.join(step_content)}")
        
        # If no structured steps found, create from content
        if not reasoning:
            reasoning = self._create_reasoning_from_content(lines)
        
        return reasoning
    
    def _create_reasoning_from_content(self, lines: List[str]) -> List[str]:
        """Create reasoning chain from unstructured content"""
        reasoning = []
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip FINAL ANSWER section
            if "FINAL ANSWER:" in line.upper():
                break
            
            # Skip bullets and formatting
            if line.startswith(('*', '-', '#')) or line.startswith('**'):
                continue
            
            # Collect substantial content
            if len(line) > 20:
                current_content.append(line)
        
        # Create reasoning steps from content
        if current_content:
            # Split content into logical steps
            content_text = ' '.join(current_content)
            
            # Look for natural break points
            if 'question' in content_text.lower() and 'asking' in content_text.lower():
                reasoning.append("Step 1 - Question Analysis: Identified the question type and requirements")
            
            if 'context' in content_text.lower() or 'snippet' in content_text.lower():
                reasoning.append("Step 2 - Information Gathering: Retrieved relevant information from provided context")
            
            if 'conclude' in content_text.lower() or 'based on' in content_text.lower():
                reasoning.append("Step 3 - Reasoning: Analyzed information and drew logical conclusions")
            
            if 'answer' in content_text.lower() or 'definition' in content_text.lower():
                reasoning.append("Step 4 - Synthesis: Synthesized findings into comprehensive answer")
        
        return reasoning
    
    def _extract_citations_streaming(self, response: str, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citations from streaming response"""
        citations = []
        
        # Look for explicit citation patterns like [1], [2], etc.
        citation_pattern = r'\[(\d+)\]'
        matches = re.findall(citation_pattern, response)
        
        for match in matches:
            try:
                index = int(match) - 1
                if 0 <= index < len(context):
                    item = context[index]
                    citations.append({
                        "file": item.get("file", "Unknown"),
                        "page": item.get("page"),
                        "text": item.get("text", "")[:200] + "..." if len(item.get("text", "")) > 200 else item.get("text", ""),
                        "relevance": 0.8  # Default relevance
                    })
            except (ValueError, IndexError):
                continue
        
        # If no explicit citations found, create citations from context
        if not citations and context:
            citations = self._create_context_citations_streaming(response, context)
        
        return citations
    
    def _create_context_citations_streaming(self, response: str, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create citations from context when no explicit citations are found"""
        citations = []
        
        # Take top 3 most relevant context items
        for i, item in enumerate(context[:3]):
            # Calculate relevance based on text similarity with response
            item_text = item.get("text", "").lower()
            response_lower = response.lower()
            
            # Simple relevance scoring based on keyword overlap
            relevance = 0.5  # Base relevance
            
            # Check for keyword matches
            keywords = ['classroom', 'management', 'teaching', 'learning', 'student', 'teacher']
            matches = sum(1 for keyword in keywords if keyword in item_text and keyword in response_lower)
            relevance += min(matches * 0.1, 0.3)
            
            # Check for text length (longer texts might be more informative)
            if len(item_text) > 100:
                relevance += 0.1
            
            # Ensure relevance is between 0.5 and 1.0
            relevance = min(max(relevance, 0.5), 1.0)
            
            citation = {
                "file": item.get("file", f"Document {i+1}"),
                "page": item.get("page"),
                "text": item.get("text", "")[:200] + "..." if len(item.get("text", "")) > 200 else item.get("text", ""),
                "relevance": relevance
            }
            citations.append(citation)
        
        return citations
    
    def _format_answer_with_citations(self, answer: str, source_citations: List[Dict[str, Any]]) -> str:
        """Format the final answer with beautiful source citations like the original project"""
        if not source_citations:
            return answer
        
        # Remove duplicate sources based on file path
        unique_sources = {}
        for citation in source_citations:
            file_path = citation.get("file", "Unknown")
            page = citation.get("page", "?")
            relevance = citation.get("relevance", 0.0)
            
            # Use file path as key to avoid duplicates
            if file_path not in unique_sources or relevance > unique_sources[file_path]['relevance']:
                unique_sources[file_path] = {
                    'file_path': file_path,
                    'page': page,
                    'relevance': relevance
                }
        
        # Create clean source citations section
        sources_html = []
        for i, (file_path, source_info) in enumerate(unique_sources.items(), 1):
            # Extract just the filename
            import os
            file_name = os.path.basename(file_path) if file_path != "Unknown" else "Unknown"
            
            # Create clickable "Open" link
            if file_path != "Unknown":
                try:
                    from pathlib import Path
                    from PyQt6.QtCore import QUrl
                    path = Path(file_path).resolve()
                    url = QUrl.fromLocalFile(str(path))
                    open_link = f"<a href='{url.toString()}' title='{path}' style='color: #007acc; text-decoration: none;'>Open</a>"
                except:
                    open_link = "<span style='color: #666;'>Open</span>"
            else:
                open_link = "<span style='color: #666;'>Open</span>"
            
            # Clean format for customer support: [1] filename.pdf • page 12 • Open
            source_text = f"[{i}] <span style='font-weight: bold; color: #2c3e50;'>{file_name}</span> • page {source_info['page']} • {open_link}"
            sources_html.append(source_text)
        
        # Combine answer with beautifully formatted sources
        formatted_answer = f"{answer}\n\n<b style='color: #34495e; font-size: 14px;'>Sources:</b><br>" + "<br>".join(sources_html)
        
        return formatted_answer
    
    def _generate_organized_answer_from_json(self, result) -> str:
        """Generate a comprehensive, detailed final answer from structured JSON reasoning data"""
        try:
            # Start with the main answer
            answer_parts = []
            
            # Add the main answer if available
            if result.answer and result.answer.strip():
                # Clean up the answer (remove any existing citations)
                clean_answer = result.answer.strip()
                if "Sources:" in clean_answer:
                    clean_answer = clean_answer.split("Sources:")[0].strip()
                
                # Enhance the answer with more detail and depth
                enhanced_answer = self._enhance_answer_with_context(clean_answer, result)
                answer_parts.append(enhanced_answer)
            
            # If no main answer, generate from supporting facts
            if not answer_parts and result.supporting_facts:
                synthesized = self._synthesize_answer_from_facts(result.supporting_facts)
                enhanced = self._enhance_answer_with_context(synthesized, result)
                answer_parts.append(enhanced)
            
            # If still no answer, generate from reasoning chain
            if not answer_parts and result.reasoning_chain:
                synthesized = self._synthesize_answer_from_reasoning(result.reasoning_chain)
                enhanced = self._enhance_answer_with_context(synthesized, result)
                answer_parts.append(enhanced)
            
            # Skip supporting evidence and alternative perspectives for customer support
            # Keep only the main answer for clean, concise responses
            
            # Combine all parts with proper formatting
            organized_answer = "\n\n".join(answer_parts)
            
            # Add source citations at the end
            if result.source_citations:
                organized_answer = self._format_answer_with_citations(organized_answer, result.source_citations)
            
            return organized_answer
            
        except Exception as e:
            logger.error(f"Error generating organized answer: {e}")
            # Fallback to original answer with citations
            return self._format_answer_with_citations(result.answer or "No answer generated", result.source_citations)
    
    def _enhance_answer_with_context(self, base_answer: str, result) -> str:
        """Enhance the base answer with additional context and depth - domain agnostic"""
        try:
            # Extract key information from the result
            has_high_confidence = result.confidence_score > 0.8
            has_multiple_sources = len(result.source_citations) > 1
            has_detailed_reasoning = len(result.reasoning_chain) > 2
            
            # Detect domain for context-appropriate enhancements
            domain = self._detect_domain_from_result(result)
            
            # Format the base answer properly
            formatted_answer = self._format_answer_structure(base_answer)
            
            # Start with the formatted answer
            enhanced_parts = [formatted_answer]
            
            # Add depth based on available information
            if has_high_confidence and has_multiple_sources:
                # Add context about the comprehensive nature
                enhanced_parts.append("This comprehensive understanding is supported by multiple sources and represents a well-established framework in this field.")
            
            # Add practical implications based on domain
            if any('practical' in fact.lower() or 'implementation' in fact.lower() or 'strategies' in fact.lower() 
                   for fact in result.supporting_facts):
                enhanced_parts.append(self._get_implementation_guidance(domain))
            
            # Add outcome information based on domain
            if any('outcome' in fact.lower() or 'result' in fact.lower() or 'achieve' in fact.lower() 
                   for fact in result.supporting_facts):
                enhanced_parts.append(self._get_outcome_information(domain))
            
            return "\n\n".join(enhanced_parts)
            
        except Exception as e:
            logger.error(f"Error enhancing answer: {e}")
            return base_answer
    
    def _format_answer_structure(self, answer: str) -> str:
        """Format the answer structure for better readability"""
        try:
            import re
            
            # First, clean up any existing formatting issues
            answer = answer.strip()
            
            # Handle bold formatting in steps (e.g., "1. **Check Driver Status**:")
            # Convert **text**: to **text:** with proper spacing
            answer = re.sub(r'\*\*([^*]+)\*\*:\s*', r'**\1:** ', answer)
            
            # Split by numbered steps to handle them separately
            # Look for patterns like "1. **Step Name**: Description"
            step_pattern = r'(\d+\.\s*\*\*[^*]+\*\*:[^*]+?)(?=\d+\.\s*\*\*|\Z)'
            steps = re.findall(step_pattern, answer, re.DOTALL)
            
            if steps:
                # Format each step properly
                formatted_steps = []
                for step in steps:
                    step = step.strip()
                    # Ensure proper line breaks and spacing
                    step = re.sub(r'\s+', ' ', step)  # Normalize whitespace
                    formatted_steps.append(step)
                
                # Join steps with proper spacing
                result = '\n\n'.join(formatted_steps)
            else:
                # Fallback: handle simple numbered lists
                # Split into sentences
                sentences = answer.split('. ')
                
                # Look for numbered steps and format them properly
                formatted_sentences = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    # Check if this looks like a numbered step
                    if re.match(r'^\d+\.', sentence):
                        formatted_sentences.append(sentence)
                    else:
                        formatted_sentences.append(sentence)
                
                # Join with proper spacing
                result = '. '.join(formatted_sentences)
                
                # Ensure proper line breaks for numbered lists
                result = re.sub(r'(\d+\.)', r'\n\1', result)
                result = re.sub(r'\n+', '\n', result)
                result = result.strip()
            
            # Final cleanup
            result = re.sub(r'\n\s*\n', '\n\n', result)  # Normalize paragraph breaks
            result = result.strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting answer structure: {e}")
            return answer
    
    def _detect_domain_from_result(self, result) -> str:
        """Detect domain from the reasoning result"""
        # Check supporting facts for domain indicators
        all_text = " ".join(result.supporting_facts + [result.answer or ""])
        return self._detect_domain(all_text)
    
    def _get_implementation_guidance(self, domain: str) -> str:
        """Get domain-specific implementation guidance"""
        guidance_map = {
            "education": " Effective implementation requires balancing structure with flexibility, authority with empathy, and discipline with encouragement.",
            "technology": " Successful implementation typically involves careful planning, testing, and gradual rollout to ensure system stability and user adoption.",
            "customer_support": " Effective implementation requires clear communication, proper training, and systematic follow-up to ensure customer satisfaction.",
            "business": " Successful implementation involves stakeholder buy-in, clear metrics, and iterative improvement based on feedback and results.",
            "legal": " Proper implementation requires careful review, compliance verification, and ongoing monitoring to ensure adherence to applicable regulations.",
            "medical": " Safe implementation requires thorough assessment, patient monitoring, and adherence to established protocols and safety guidelines.",
            "general": " Effective implementation requires careful planning, stakeholder engagement, and systematic evaluation to ensure desired outcomes."
        }
        return guidance_map.get(domain, guidance_map["general"])
    
    def _get_outcome_information(self, domain: str) -> str:
        """Get domain-specific outcome information"""
        outcome_map = {
            "education": " When implemented effectively, this approach leads to improved engagement, better learning outcomes, and a more positive environment.",
            "technology": " When implemented successfully, this approach results in improved efficiency, better user experience, and enhanced system performance.",
            "customer_support": " When implemented effectively, this approach leads to faster resolution times, higher customer satisfaction, and improved service quality.",
            "business": " When implemented successfully, this approach results in improved efficiency, better outcomes, and enhanced organizational performance.",
            "legal": " When implemented properly, this approach ensures compliance, reduces risk, and supports organizational objectives within legal frameworks.",
            "medical": " When implemented correctly, this approach leads to improved patient outcomes, better care quality, and enhanced safety measures.",
            "general": " When implemented effectively, this approach leads to improved results, better outcomes, and enhanced performance in the relevant context."
        }
        return outcome_map.get(domain, outcome_map["general"])
    
    def _synthesize_answer_from_facts(self, supporting_facts: List[str]) -> str:
        """Synthesize a comprehensive answer from supporting facts"""
        if not supporting_facts:
            return "No supporting facts available."
        
        # Extract key concepts and build a comprehensive answer
        key_concepts = []
        definitions = []
        purposes = []
        components = []
        
        for fact in supporting_facts:
            fact = fact.strip()
            if len(fact) < 20:
                continue
                
            # Look for definition patterns
            if any(keyword in fact.lower() for keyword in ['is', 'refers to', 'means', 'involves', 'encompasses', 'defined as']):
                definitions.append(fact)
            # Look for purpose/goal patterns
            elif any(keyword in fact.lower() for keyword in ['goal', 'purpose', 'aim', 'objective', 'maximize', 'achieve']):
                purposes.append(fact)
            # Look for component/strategy patterns
            elif any(keyword in fact.lower() for keyword in ['includes', 'strategies', 'components', 'elements', 'aspects']):
                components.append(fact)
            else:
                key_concepts.append(fact)
        
        # Build comprehensive answer
        answer_parts = []
        
        # Start with definition if available
        if definitions:
            answer_parts.append(definitions[0])
        elif key_concepts:
            answer_parts.append(key_concepts[0])
        
        # Add purpose/goal information
        if purposes:
            answer_parts.append(f" The primary goal is to {purposes[0].lower().split('goal')[1].split('.')[0].strip()}." if 'goal' in purposes[0].lower() else purposes[0])
        
        # Add components/strategies
        if components:
            answer_parts.append(f" This involves {components[0].lower().split('involves')[1].split('.')[0].strip()}." if 'involves' in components[0].lower() else components[0])
        
        # Add additional context if available
        if len(key_concepts) > 1:
            answer_parts.append(f" Additionally, {key_concepts[1].lower()}")
        
        return " ".join(answer_parts) if answer_parts else supporting_facts[0].strip()
    
    def _synthesize_answer_from_reasoning(self, reasoning_chain: List[str]) -> str:
        """Synthesize an answer from reasoning chain"""
        if not reasoning_chain:
            return "No reasoning available."
        
        # Look for synthesis or conclusion steps
        for step in reasoning_chain:
            if any(keyword in step.lower() for keyword in ['synthesis', 'conclusion', 'answer', 'therefore', 'thus']):
                return step
        
        # If no synthesis found, use the last step
        return reasoning_chain[-1] if reasoning_chain else "No reasoning available."
    
    def _extract_supporting_facts_streaming(self, response: str) -> List[str]:
        """Extract supporting facts from streaming response"""
        facts = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('STEP') and 
                not line.startswith('FINAL ANSWER') and
                not line.startswith('**') and
                len(line) > 30):
                facts.append(line)
        
        return facts[:5]  # Limit to 5 facts
    
    def _extract_alternatives_streaming(self, response: str) -> List[str]:
        """Extract alternative interpretations from streaming response"""
        alternatives = []
        
        # Look for alternative indicators
        alt_patterns = [
            r'alternative(?:ly)?',
            r'on the other hand',
            r'however',
            r'it could also be',
            r'another interpretation'
        ]
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if any(pattern in line.lower() for pattern in alt_patterns):
                alternatives.append(line)
        
        # If no alternatives found in response, generate some based on common educational perspectives
        if not alternatives:
            alternatives = self._generate_default_alternatives(response)
        
        return alternatives[:2]  # Limit to 2 alternatives
    
    def _generate_default_alternatives(self, response: str) -> List[str]:
        """Generate default alternative interpretations based on response content - domain agnostic"""
        alternatives = []
        
        # Detect domain and generate appropriate alternatives
        domain = self._detect_domain(response)
        
        if domain == "education":
            alternatives.append("Some traditional perspectives emphasize structured, teacher-directed approaches, while others advocate for more flexible, student-centered methodologies.")
            alternatives.append("Different educational philosophies may prioritize different outcomes, such as academic achievement versus holistic development or individual growth versus standardized benchmarks.")
        
        elif domain == "technology":
            alternatives.append("Some approaches favor established, proven technologies and methodologies, while others prioritize cutting-edge solutions and rapid innovation.")
            alternatives.append("Different organizations may emphasize different priorities, such as security and stability versus agility and rapid deployment.")
        
        elif domain == "customer_support":
            alternatives.append("Some support strategies focus on quick resolution and efficiency, while others prioritize comprehensive understanding and relationship building.")
            alternatives.append("Different support philosophies may emphasize self-service options versus personalized assistance, or reactive support versus proactive guidance.")
        
        elif domain == "business":
            alternatives.append("Some business approaches emphasize traditional, hierarchical structures and processes, while others favor agile, collaborative methodologies.")
            alternatives.append("Different business philosophies may prioritize different metrics, such as short-term profitability versus long-term sustainability or growth.")
        
        elif domain == "legal":
            alternatives.append("Some legal interpretations may emphasize strict adherence to established precedents, while others consider evolving societal norms and contemporary applications.")
            alternatives.append("Different jurisdictions or legal traditions may approach similar issues with varying frameworks and considerations.")
        
        elif domain == "medical":
            alternatives.append("Some medical approaches may emphasize evidence-based, standardized protocols, while others consider individualized treatment plans and patient-specific factors.")
            alternatives.append("Different medical specialties or schools of thought may prioritize different aspects of care, such as symptom management versus root cause treatment.")
        
        else:
            # Generic alternatives for any domain
            alternatives.append("Some approaches may emphasize established, traditional methods and practices, while others favor innovative, contemporary solutions.")
            alternatives.append("Different perspectives may prioritize different aspects, such as efficiency and standardization versus customization and flexibility.")
        
        return alternatives
    
    def _detect_domain(self, response: str) -> str:
        """Detect the domain/topic area from response content"""
        response_lower = response.lower()
        
        # Education keywords
        if any(keyword in response_lower for keyword in ['classroom', 'teaching', 'learning', 'education', 'student', 'teacher', 'pedagogy', 'curriculum', 'instruction']):
            return "education"
        
        # Technology keywords
        elif any(keyword in response_lower for keyword in ['software', 'system', 'application', 'database', 'api', 'code', 'programming', 'technical', 'server', 'network']):
            return "technology"
        
        # Customer support keywords
        elif any(keyword in response_lower for keyword in ['customer', 'support', 'help', 'ticket', 'issue', 'problem', 'service', 'assistance', 'resolution']):
            return "customer_support"
        
        # Business keywords
        elif any(keyword in response_lower for keyword in ['business', 'company', 'organization', 'management', 'strategy', 'process', 'workflow', 'operations']):
            return "business"
        
        # Legal keywords
        elif any(keyword in response_lower for keyword in ['legal', 'law', 'regulation', 'compliance', 'contract', 'agreement', 'policy', 'rights', 'liability']):
            return "legal"
        
        # Medical keywords
        elif any(keyword in response_lower for keyword in ['medical', 'health', 'patient', 'treatment', 'diagnosis', 'therapy', 'clinical', 'healthcare', 'medicine']):
            return "medical"
        
        # Default to general
        return "general"
    
    def _calculate_confidence_score(self, result: StreamingReasoningResult) -> float:
        """Calculate confidence score based on available information"""
        score = 0.3  # Base score (more conservative)
        
        # Factor 1: Source citations quality
        if result.source_citations:
            avg_relevance = sum(c.get("relevance", 0.8) for c in result.source_citations) / len(result.source_citations)
            score += min(avg_relevance * 0.25, 0.25)
        
        # Factor 2: Supporting facts quality
        if result.supporting_facts:
            score += 0.15
            if len(result.supporting_facts) >= 3:
                score += 0.05
        
        # Factor 3: Reasoning chain completeness
        if result.reasoning_chain and len(result.reasoning_chain) >= 3:
            score += 0.15
        
        # Factor 4: Answer completeness
        if len(result.answer) > 100:
            score += 0.10
        elif len(result.answer) > 50:
            score += 0.05
        
        # Factor 5: Alternative interpretations (shows thoroughness)
        if result.alternative_interpretations:
            score += 0.05
        
        return min(score, 1.0)
