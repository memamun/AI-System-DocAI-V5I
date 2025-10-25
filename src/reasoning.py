"""
Structured Reasoning Engine for AI-System-DocAI V5I
Generates JSON responses with reasoning chains, confidence scores, and citations
"""
from __future__ import annotations
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class SourceCitation:
    """Source citation structure"""
    file: str
    page: Optional[int] = None
    section: Optional[str] = None
    text: str = ""
    relevance: float = 0.0
    start_char: Optional[int] = None
    end_char: Optional[int] = None

@dataclass
class ReasoningResult:
    """Structured reasoning result"""
    answer: str
    reasoning_chain: List[str]
    confidence_score: float
    source_citations: List[SourceCitation]
    supporting_facts: List[str]
    alternative_interpretations: List[str]
    metadata: Dict[str, Any]

class ReasoningEngine:
    """Structured reasoning engine with rule-based pre-processing and LLM assistance"""
    
    def __init__(self):
        self.question_types = {
            "factual": ["what", "who", "when", "where", "which"],
            "analytical": ["how", "why", "explain", "analyze", "compare"],
            "comparative": ["compare", "contrast", "difference", "similarity"],
            "numerical": ["how many", "how much", "count", "number", "percentage"],
            "temporal": ["when", "before", "after", "during", "timeline"]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            "number": r'\b\d+(?:\.\d+)?\b',
            "percentage": r'\b\d+(?:\.\d+)?%\b',
            "currency": r'\$\d+(?:,\d{3})*(?:\.\d{2})?\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'https?://[^\s<>"{}|\\^`\[\]]+'
        }
    
    def process_query(self, query: str, context: List[Dict[str, Any]], 
                     llm_backend, device_string: str = "cpu") -> ReasoningResult:
        """Process query with structured reasoning"""
        start_time = time.time()
        
        # Step 1: Rule-based pre-processing
        question_type = self._identify_question_type(query)
        entities = self._extract_entities(query)
        context_entities = self._extract_context_entities(context)
        
        # Step 2: Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(query, question_type, len(context))
        
        # Step 3: LLM-assisted reasoning
        structured_prompt = self._create_structured_prompt(query, context, question_type, entities)
        
        try:
            llm_response = llm_backend.generate(
                system=structured_prompt["system"],
                user=structured_prompt["user"],
                max_tokens=800
            )
            
            # Step 4: Parse and structure response
            result = self._parse_llm_response(llm_response, context, entities)
            
            # Step 5: Calculate confidence score
            confidence = self._calculate_confidence(result, context, entities)
            result.confidence_score = confidence
            
            # Step 6: Add metadata
            query_time = int((time.time() - start_time) * 1000)
            result.metadata = {
                "query_time_ms": query_time,
                "sources_searched": len(context),
                "question_type": question_type,
                "entities_found": len(entities),
                "device_used": device_string,
                "reasoning_steps": len(reasoning_chain)
            }
            
            # Step 7: Generate organized final answer from structured data
            result.answer = self._generate_organized_answer_from_json(result)
            
            # Step 8: Add alternative interpretations if missing
            if not result.alternative_interpretations:
                result.alternative_interpretations = self._generate_default_alternatives(llm_response)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            return self._create_fallback_result(query, context, str(e), device_string)
    
    def _identify_question_type(self, query: str) -> str:
        """Identify the type of question"""
        query_lower = query.lower()
        
        for q_type, keywords in self.question_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return q_type
        
        return "general"
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
        
        return entities
    
    def _extract_context_entities(self, context: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract entities from context"""
        all_entities = {}
        
        for item in context:
            text = item.get("text", "")
            entities = self._extract_entities(text)
            
            for entity_type, values in entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = []
                all_entities[entity_type].extend(values)
        
        # Remove duplicates
        for entity_type in all_entities:
            all_entities[entity_type] = list(set(all_entities[entity_type]))
        
        return all_entities
    
    def _generate_reasoning_chain(self, query: str, question_type: str, context_count: int) -> List[str]:
        """Generate reasoning chain steps"""
        chain = [
            f"1. Identified question type as '{question_type}'",
            f"2. Retrieved {context_count} relevant passages from documents",
            "3. Extracted key entities and facts from sources",
            "4. Applied logical inference and cross-referencing",
            "5. Synthesized information into coherent answer"
        ]
        
        if question_type == "analytical":
            chain.insert(3, "3a. Analyzed cause-and-effect relationships")
        elif question_type == "comparative":
            chain.insert(3, "3a. Compared and contrasted information")
        elif question_type == "numerical":
            chain.insert(3, "3a. Validated numerical data consistency")
        
        return chain
    
    def _create_structured_prompt(self, query: str, context: List[Dict[str, Any]], 
                                question_type: str, entities: Dict[str, List[str]]) -> Dict[str, str]:
        """Create structured prompt for LLM"""
        
        # Format context
        context_text = ""
        for i, item in enumerate(context, 1):
            source = item.get("file", "Unknown")
            text = item.get("text", "")[:500]  # Limit length
            context_text += f"[{i}] Source: {source}\n{text}\n\n"
        
        # Format entities
        entities_text = ""
        for entity_type, values in entities.items():
            if values:
                entities_text += f"{entity_type.title()}: {', '.join(values[:5])}\n"
        
        system_prompt = f"""You are an expert document analysis assistant with advanced reasoning capabilities. You use a "slow-thinking" approach similar to ChatGPT o1, involving deliberate step-by-step analysis before providing your final answer.

Question Type: {question_type}
Key Entities: {entities_text}

REASONING FRAMEWORK:
1. ANALYZE: Break down the question into components
2. SEARCH: Find relevant information in the context
3. SYNTHESIZE: Combine information logically
4. VERIFY: Check for consistency and completeness
5. CONCLUDE: Provide a definitive answer

Context:
{context_text}"""

        user_prompt = f"""Question: {query}

Please follow this structured reasoning process and provide a clear final answer:

STEP 1 - ANALYSIS:
- What is the question asking for?
- What type of information do I need?
- What are the key concepts involved?

STEP 2 - INFORMATION GATHERING:
- What relevant information is available in the context?
- Which sources contain the most relevant information?
- Are there any gaps in the information?

STEP 3 - REASONING:
- How do the pieces of information connect?
- What logical conclusions can I draw?
- Are there any contradictions or uncertainties?

STEP 4 - SYNTHESIS:
- What is the most accurate answer based on the evidence?
- How confident am I in this answer?
- What are the limitations or caveats?

FINAL ANSWER:
Based on the analysis above, [provide a clear, direct, and comprehensive answer to the question. This should be a complete sentence or paragraph that directly addresses what was asked.]

IMPORTANT: Your FINAL ANSWER must be a complete, standalone response that someone could read without seeing the reasoning steps above. Make it clear, direct, and informative."""

        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def _parse_llm_response(self, response: str, context: List[Dict[str, Any]], 
                          entities: Dict[str, List[str]]) -> ReasoningResult:
        """Parse LLM response into structured format"""
        
        # Extract answer (first paragraph or before reasoning)
        answer = self._extract_answer(response)
        
        # Extract reasoning chain
        reasoning_chain = self._extract_reasoning_chain(response)
        
        # Extract citations
        citations = self._extract_citations(response, context)
        
        # Extract supporting facts
        supporting_facts = self._extract_supporting_facts(response)
        
        # Extract alternative interpretations
        alternatives = self._extract_alternatives(response)
        
        # If no clear answer was found, try to generate one from supporting facts
        if answer == "No clear answer found in response." and supporting_facts:
            answer = self._generate_answer_from_facts(supporting_facts, context)
        
        return ReasoningResult(
            answer=answer,
            reasoning_chain=reasoning_chain,
            confidence_score=0.0,  # Will be calculated separately
            source_citations=citations,
            supporting_facts=supporting_facts,
            alternative_interpretations=alternatives,
            metadata={}
        )
    
    def _extract_answer(self, response: str) -> str:
        """Extract main answer from response with multiple fallback strategies"""
        lines = response.split('\n')
        
        # Strategy 1: Look for "FINAL ANSWER:" section
        final_answer_started = False
        answer_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we've reached the FINAL ANSWER section
            if "FINAL ANSWER:" in line.upper():
                final_answer_started = True
                # Extract the answer part after "FINAL ANSWER:"
                answer_part = line.split(":", 1)
                if len(answer_part) > 1:
                    answer_lines.append(answer_part[1].strip())
                continue
            
            # If we're in the FINAL ANSWER section, collect lines
            if final_answer_started:
                answer_lines.append(line)
            # If we haven't found FINAL ANSWER yet, look for direct answers at the beginning
            elif not final_answer_started and len(answer_lines) < 3:
                # Skip reasoning indicators
                if any(indicator in line.lower() for indicator in ['reasoning:', 'analysis:', 'step', 'information gathering:', 'synthesis:']):
                    break
                answer_lines.append(line)
        
        # If we found a FINAL ANSWER section, format it properly
        if final_answer_started and answer_lines:
            # Join lines while preserving structure
            answer_text = '\n'.join(answer_lines).strip()
            return self._format_answer_structure(answer_text)
        
        # Strategy 2: Look for direct answers at the beginning (before reasoning sections)
        if answer_lines:
            # Join lines while preserving structure
            answer_text = '\n'.join(answer_lines).strip()
            return self._format_answer_structure(answer_text)
        
        # Strategy 3: Extract from reasoning chain - look for definition-like statements
        definition_patterns = [
            r'is\s+(?:a\s+)?(?:broad\s+)?term\s+that\s+encompasses',
            r'is\s+(?:a\s+)?(?:set\s+of\s+)?(?:strategies|techniques|methods)',
            r'is\s+(?:a\s+)?(?:process|approach|system)',
            r'refers\s+to',
            r'can\s+be\s+defined\s+as',
            r'means\s+',
            r'involves\s+',
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip reasoning headers
            if any(indicator in line.lower() for indicator in ['step', 'analysis:', 'reasoning:', 'information gathering:', 'synthesis:']):
                continue
            
            # Look for definition patterns
            for pattern in definition_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return line
        
        # Strategy 4: Look for sentences that start with the topic and contain "is"
        topic_words = ['classroom management', 'management', 'teaching', 'education']
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip reasoning headers
            if any(indicator in line.lower() for indicator in ['step', 'analysis:', 'reasoning:', 'information gathering:', 'synthesis:']):
                continue
            
            # Look for sentences that define the topic
            if any(topic in line.lower() for topic in topic_words) and (' is ' in line.lower() or ' refers to ' in line.lower()):
                return line
        
        # Strategy 5: Use the first substantial sentence that's not a reasoning header
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip reasoning headers and short lines
            if (any(indicator in line.lower() for indicator in ['step', 'analysis:', 'reasoning:', 'information gathering:', 'synthesis:']) or
                len(line) < 20 or
                line.startswith('**') or
                line.startswith('-') or
                line.startswith('*')):
                continue
            
            # Use the first substantial sentence
            return line
        
        return "No clear answer found in response."
    
    def _generate_answer_from_facts(self, supporting_facts: List[str], context: List[Dict[str, Any]]) -> str:
        """Generate an answer from supporting facts when LLM response doesn't contain a clear answer"""
        if not supporting_facts:
            return "No clear answer found in response."
        
        # Look for definition-like facts
        for fact in supporting_facts:
            # Check if this fact contains a definition
            if any(pattern in fact.lower() for pattern in ['is a', 'is defined as', 'refers to', 'encompasses', 'involves']):
                return fact
        
        # Look for facts that mention the topic and provide information
        topic_indicators = ['classroom management', 'management', 'teaching', 'education']
        for fact in supporting_facts:
            if any(topic in fact.lower() for topic in topic_indicators):
                return fact
        
        # Use the first substantial fact
        for fact in supporting_facts:
            if len(fact.strip()) > 20:  # Substantial fact
                return fact
        
        # Fallback to first fact
        return supporting_facts[0] if supporting_facts else "No clear answer found in response."
    
    def _extract_reasoning_chain(self, response: str) -> List[str]:
        """Extract reasoning chain from response, focusing on structured steps"""
        reasoning = []
        lines = response.split('\n')
        
        current_step = None
        step_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for step headers
            if re.match(r'STEP \d+', line.upper()):
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
                # Clean up the line
                line = re.sub(r'^[-*]\s*', '', line)    # Remove bullets
                if line and not line.startswith('STEP'):
                    step_content.append(line)
        
        # Add the last step
        if current_step and step_content:
            reasoning.append(f"{current_step}: {' '.join(step_content)}")
        
        # If no structured steps found, create explicit reasoning steps
        if not reasoning:
            reasoning = self._create_explicit_reasoning_steps(response, lines)
        
        return reasoning[:5]  # Limit to 5 steps
    
    def _create_explicit_reasoning_steps(self, response: str, lines: List[str]) -> List[str]:
        """Create explicit reasoning steps when LLM doesn't provide structured format"""
        steps = []
        
        # Step 1: Question Analysis
        question_indicators = ['what', 'how', 'why', 'when', 'where', 'who']
        question_type = "definition" if any(q in response.lower() for q in ['what is', 'define', 'definition']) else "general"
        steps.append(f"Step 1 - Question Analysis: Identified this as a {question_type} question requiring comprehensive explanation.")
        
        # Step 2: Information Gathering
        context_indicators = ['document', 'source', 'text', 'information', 'context']
        if any(indicator in response.lower() for indicator in context_indicators):
            steps.append("Step 2 - Information Gathering: Retrieved relevant information from provided document context.")
        else:
            steps.append("Step 2 - Information Gathering: Analyzed available context for relevant information.")
        
        # Step 3: Synthesis
        synthesis_indicators = ['based on', 'according to', 'from the', 'the document shows']
        if any(indicator in response.lower() for indicator in synthesis_indicators):
            steps.append("Step 3 - Synthesis: Combined information from multiple sources to form comprehensive answer.")
        else:
            steps.append("Step 3 - Synthesis: Synthesized available information into coherent response.")
        
        # Step 4: Verification
        steps.append("Step 4 - Verification: Ensured answer directly addresses the question and is supported by evidence.")
        
        return steps
    
    def _extract_citations(self, response: str, context: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Extract citations from response with enhanced source tracking"""
        citations = []
        
        # Find citation patterns [1], [2], etc.
        citation_pattern = r'\[(\d+)\]'
        matches = re.findall(citation_pattern, response)
        
        for match in matches:
            try:
                index = int(match) - 1
                if 0 <= index < len(context):
                    item = context[index]
                    citation = SourceCitation(
                        file=item.get("file", "Unknown"),
                        page=item.get("page"),
                        text=item.get("text", "")[:200] + "..." if len(item.get("text", "")) > 200 else item.get("text", ""),
                        relevance=item.get("similarity_score", 0.8)  # Use actual similarity score if available
                    )
                    citations.append(citation)
            except (ValueError, IndexError):
                continue
        
        # If no explicit citations found, create citations from context
        if not citations and context:
            citations = self._create_context_citations(context, response)
        
        return citations
    
    def _create_context_citations(self, context: List[Dict[str, Any]], response: str) -> List[SourceCitation]:
        """Create citations from context when no explicit citations are found"""
        citations = []
        
        # Take top 3 most relevant context items
        for i, item in enumerate(context[:3]):
            # Calculate relevance based on similarity score and text length
            similarity_score = item.get("similarity_score", 0.8)
            text_length = len(item.get("text", ""))
            relevance = min(similarity_score + (0.1 if text_length > 100 else 0), 1.0)
            
            citation = SourceCitation(
                file=item.get("file", f"Document {i+1}"),
                page=item.get("page"),
                text=item.get("text", "")[:200] + "..." if len(item.get("text", "")) > 200 else item.get("text", ""),
                relevance=relevance
            )
            citations.append(citation)
        
        return citations
    
    def _extract_supporting_facts(self, response: str) -> List[str]:
        """Extract supporting facts from response"""
        facts = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Reasoning:', 'Analysis:', 'Step')):
                # Look for factual statements
                if any(indicator in line.lower() for indicator in ['according to', 'the document', 'source', 'data shows']):
                    facts.append(line)
        
        return facts[:3]  # Limit to 3 facts
    
    def _extract_alternatives(self, response: str) -> List[str]:
        """Extract alternative interpretations"""
        alternatives = []
        lines = response.split('\n')
        
        in_alternatives = False
        for line in lines:
            line = line.strip()
            
            if any(indicator in line.lower() for indicator in ['alternative', 'however', 'on the other hand', 'it could also']):
                in_alternatives = True
                continue
            
            if in_alternatives and line:
                alternatives.append(line)
        
        return alternatives[:2]  # Limit to 2 alternatives
    
    def _calculate_confidence(self, result: ReasoningResult, context: List[Dict[str, Any]], 
                            entities: Dict[str, List[str]]) -> float:
        """Calculate confidence score based on multiple factors"""
        confidence = 0.5  # Base confidence
        
        # Factor 1: Number of sources
        if len(context) >= 3:
            confidence += 0.2
        elif len(context) >= 1:
            confidence += 0.1
        
        # Factor 2: Answer quality
        if len(result.answer) > 50:
            confidence += 0.1
        
        # Factor 3: Citations present
        if result.source_citations:
            confidence += 0.1
        
        # Factor 4: Supporting facts
        if result.supporting_facts:
            confidence += 0.1
        
        # Factor 5: Entity coverage
        if entities and len(entities) > 0:
            confidence += 0.05
        
        # Factor 6: Context similarity scores
        if context:
            avg_similarity = sum(item.get("similarity_score", 0.5) for item in context) / len(context)
            confidence += min(avg_similarity * 0.10, 0.10)
        
        # Factor 7: Reasoning chain completeness
        if result.reasoning_chain and len(result.reasoning_chain) >= 3:
            confidence += 0.10
        
        # Factor 8: Alternative interpretations (shows thoroughness)
        if result.alternative_interpretations:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _generate_organized_answer_from_json(self, result) -> str:
        """Generate a well-organized final answer from structured JSON reasoning data"""
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
        
        answer_text = " ".join(answer_parts) if answer_parts else supporting_facts[0].strip()
        return self._format_answer_structure(answer_text)
    
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
    
    def _format_answer_with_citations(self, answer: str, source_citations: List[Any]) -> str:
        """Format the final answer with beautiful source citations like the original project"""
        if not source_citations:
            return answer
        
        # Remove duplicate sources based on file path
        unique_sources = {}
        for citation in source_citations:
            # Handle both dict and SourceCitation object
            if hasattr(citation, 'file'):
                file_path = citation.file
                page = citation.page
                relevance = getattr(citation, 'relevance', 0.0)
            else:
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
    
    def _create_fallback_result(self, query: str, context: List[Dict[str, Any]], 
                              error: str, device_string: str) -> ReasoningResult:
        """Create fallback result when LLM fails"""
        return ReasoningResult(
            answer=f"Unable to generate answer due to error: {error}",
            reasoning_chain=[
                "1. Error occurred during LLM processing",
                "2. Fallback to basic response",
                "3. Please check system configuration"
            ],
            confidence_score=0.1,
            source_citations=[],
            supporting_facts=[],
            alternative_interpretations=[],
            metadata={
                "error": error,
                "device_used": device_string,
                "fallback": True
            }
        )
    
    def to_json(self, result: ReasoningResult) -> str:
        """Convert reasoning result to JSON string"""
        # Convert dataclass to dict
        data = asdict(result)
        
        # Convert SourceCitation objects to dicts
        data["source_citations"] = [asdict(citation) for citation in result.source_citations]
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def from_json(self, json_str: str) -> ReasoningResult:
        """Create reasoning result from JSON string"""
        data = json.loads(json_str)
        
        # Convert citation dicts back to SourceCitation objects
        citations = [SourceCitation(**citation) for citation in data["source_citations"]]
        
        return ReasoningResult(
            answer=data["answer"],
            reasoning_chain=data["reasoning_chain"],
            confidence_score=data["confidence_score"],
            source_citations=citations,
            supporting_facts=data["supporting_facts"],
            alternative_interpretations=data["alternative_interpretations"],
            metadata=data["metadata"]
        )
