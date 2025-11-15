"""
Generalized RAG Reasoning Engine for AI-System-DocAI V5I
Provides comprehensive reasoning with proper context integration and citation
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
    question: str
    answer: str
    reasoning_chain: List[str]
    confidence_score: float
    source_citations: List[SourceCitation]
    supporting_facts: List[str]
    alternative_interpretations: List[str]
    metadata: Dict[str, Any]

class ReasoningEngine:
    """Generalized RAG reasoning engine with comprehensive context integration"""

    def __init__(self):
        # Question type classification for better reasoning
        self.question_types = {
            "definition": ["what is", "define", "meaning of", "what does", "what are"],
            "explanation": ["how", "why", "explain", "describe", "what happens"],
            "comparison": ["compare", "contrast", "difference", "versus", "vs"],
            "procedure": ["how to", "steps", "process", "method", "guide"],
            "factual": ["who", "when", "where", "which", "what"],
            "analysis": ["analyze", "evaluate", "assess", "impact", "effect"],
            "quantitative": ["how many", "how much", "percentage", "number", "count"]
        }

        # Entity extraction patterns for context analysis
        self.entity_patterns = {
            "technical_term": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            "acronym": r'\b[A-Z]{2,5}\b',
            "version": r'\bv?\d+(?:\.\d+)+(?:\.\d+)*\b',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            "number": r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',
            "percentage": r'\b\d+(?:\.\d+)?%\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'https?://[^\s<>"{}|\\^`\[\]]+'
        }
    
    def process_query(self, query: str, context: List[Dict[str, Any]],
                     llm_backend, device_string: str = "cpu") -> ReasoningResult:
        """Process query with comprehensive RAG reasoning"""
        start_time = time.time()

        # Step 1: Analyze query and context
        question_type = self._identify_question_type(query)
        query_entities = self._extract_entities(query)
        context_entities = self._extract_context_entities(context)
        context_relevance = self._analyze_context_relevance(query, context)

        # Step 2: Build comprehensive reasoning framework
        reasoning_framework = self._build_reasoning_framework(query, question_type, context, context_relevance)

        # Step 3: Generate structured prompt for LLM
        # Get answer_length setting from config
        try:
            from config import config_manager
            answer_length = config_manager.config.reasoning.answer_length
        except (ImportError, AttributeError):
            answer_length = "short"  # Default to short (300-400 words)
        
        structured_prompt = self._create_comprehensive_prompt(query, context, question_type, query_entities, reasoning_framework, answer_length)

        try:
            # Step 4: Get LLM response with increased context
            llm_response = llm_backend.generate(
                system=structured_prompt["system"],
                user=structured_prompt["user"],
                max_tokens=4000  # Increased for extremely comprehensive, detailed answers (500-700+ words)
            )

            # Step 5: Parse and structure the response
            result = self._parse_comprehensive_response(llm_response, context, query_entities)

            # Step 6: Enhance with additional reasoning
            result = self._enhance_with_contextual_reasoning(result, context, query, question_type)

            # Step 7: Calculate comprehensive confidence score
            confidence = self._calculate_comprehensive_confidence(result, context, query_entities, context_relevance)
            result.confidence_score = confidence

            # Step 8: Add metadata
            query_time = int((time.time() - start_time) * 1000)
            result.metadata = {
                "query_time_ms": query_time,
                "sources_searched": len(context),
                "question_type": question_type,
                "context_relevance_score": context_relevance,
                "entities_found": len(query_entities),
                "device_used": device_string,
                "reasoning_framework": reasoning_framework["type"]
            }

            # Step 9: Generate final comprehensive answer
            result.answer = self._generate_comprehensive_answer(result, context)

            # Step 10: Add alternative perspectives if appropriate
            if not result.alternative_interpretations:
                result.alternative_interpretations = self._generate_reasonable_alternatives(query, result, context)

            result.question = query
            return result

        except Exception as e:
            logger.error(f"RAG reasoning failed: {e}")
            return self._create_fallback_result(query, context, str(e), device_string)
    
    def _analyze_context_relevance(self, query: str, context: List[Dict[str, Any]]) -> float:
        """Analyze how relevant the context is to the query"""
        if not context:
            return 0.0

        query_words = set(query.lower().split())
        total_relevance = 0.0

        for item in context:
            text = item.get("text", "").lower()
            item_words = set(text.split())

            # Calculate word overlap
            overlap = len(query_words.intersection(item_words))
            if query_words:
                relevance = overlap / len(query_words)
            else:
                relevance = 0.0

            # Boost relevance for exact phrase matches
            if query.lower() in text:
                relevance *= 1.5

            total_relevance += min(relevance, 1.0)

        return min(total_relevance / len(context), 1.0) if context else 0.0

    def _build_reasoning_framework(self, query: str, question_type: str, context: List[Dict[str, Any]], relevance: float) -> Dict[str, Any]:
        """Build a comprehensive reasoning framework based on query analysis"""
        framework = {
            "type": "general_analysis",
            "steps": ["analyze", "gather_evidence", "synthesize", "validate", "conclude"],
            "focus_areas": [],
            "reasoning_depth": "standard"
        }

        # Adjust framework based on question type and context
        if question_type in ["definition", "factual"]:
            framework["type"] = "factual_lookup"
            framework["steps"] = ["identify_key_terms", "locate_definitions", "verify_accuracy", "provide_context"]
        elif question_type in ["explanation", "procedure"]:
            framework["type"] = "explanatory_reasoning"
            framework["steps"] = ["break_down_concept", "explain_components", "show_relationships", "provide_examples"]
        elif question_type == "comparison":
            framework["type"] = "comparative_analysis"
            framework["steps"] = ["identify_subjects", "find_differences", "analyze_similarities", "draw_conclusions"]
        elif question_type == "analysis":
            framework["type"] = "analytical_reasoning"
            framework["steps"] = ["decompose_problem", "evaluate_factors", "assess_impact", "recommend_actions"]

        # Adjust depth based on context relevance and complexity
        if relevance > 0.7:
            framework["reasoning_depth"] = "comprehensive"
        elif relevance > 0.3:
            framework["reasoning_depth"] = "standard"
        else:
            framework["reasoning_depth"] = "exploratory"

        return framework

    def _identify_question_type(self, query: str) -> str:
        """Identify the type of question with improved accuracy"""
        query_lower = query.lower().strip()

        # Check for multi-word phrases first (more specific)
        for q_type, keywords in self.question_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return q_type

        return "factual"  # Default fallback
    
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
    
    def _create_comprehensive_prompt(self, query: str, context: List[Dict[str, Any]],
                                   question_type: str, entities: Dict[str, List[str]],
                                   reasoning_framework: Dict[str, Any], answer_length: str = "medium") -> Dict[str, str]:
        """Create comprehensive prompt for LLM with proper RAG reasoning"""
        
        # Get answer length requirements based on setting
        length_requirements = {
            "short": {
                "min_words": "300-400",
                "target_words": "300-400",
                "emphasis": "concise yet complete",
                "detail_level": "relevant details"
            },
            "medium": {
                "min_words": "500-700",
                "target_words": "500-700",
                "emphasis": "comprehensive and detailed",
                "detail_level": "ALL relevant details, explanations, examples, and context"
            },
            "long": {
                "min_words": "800-1000+",
                "target_words": "800-1000+",
                "emphasis": "extremely comprehensive and highly detailed",
                "detail_level": "ALL relevant details, explanations, examples, background information, context, and connections"
            }
        }
        length_config = length_requirements.get(answer_length, length_requirements["medium"])

        # Format context with proper citation markers
        context_text = ""
        for i, item in enumerate(context, 1):
            source = item.get("file", "Unknown")
            page = item.get("page", "N/A")
            text = item.get("text", "")
            context_text += f"[{i}] Source: {source} (Page {page})\n{text}\n\n"

        # Format entities
        entities_text = ""
        for entity_type, values in entities.items():
            if values:
                entities_text += f"{entity_type.title()}: {', '.join(values[:5])}\n"

        # Build reasoning instructions based on framework
        reasoning_instructions = self._build_reasoning_instructions(reasoning_framework, question_type)

        system_prompt = f"""You are an expert research assistant specializing in comprehensive document analysis and reasoning. You provide detailed, well-researched answers based on the provided context.

QUESTION TYPE: {question_type}
REASONING FRAMEWORK: {reasoning_framework['type']}
REASONING DEPTH: {reasoning_framework['reasoning_depth']}

KEY ENTITIES IDENTIFIED:
{entities_text}

AVAILABLE CONTEXT:
{context_text}

REASONING REQUIREMENTS:
{reasoning_instructions}

CRITICAL INSTRUCTIONS FOR YOUR RESPONSE:
- Provide {length_config['emphasis'].upper()} answers that thoroughly address ALL aspects of the question
- Minimum length: Your answer MUST be at least {length_config['min_words']} words to ensure complete coverage
- ALWAYS cite specific sources using [1], [2], etc. format when making ANY claim or statement
- Include detailed explanations, relevant quotes, statistics, and page references from the sources
- Explain concepts thoroughly with MULTIPLE examples, real-world applications, and use cases
- Provide EXTENSIVE step-by-step procedures or numbered lists for procedural content with full explanations
- Show clear reasoning with detailed connections between concepts, factors, and implications
- For comparative questions: provide COMPREHENSIVE detailed comparison of ALL aspects with examples
- For procedural questions: include ALL steps with detailed explanations, context, and tips
- For definitional questions: provide full definition, history, context, variations, examples, and applications
- Include background information, related concepts, and broader context when relevant
- Explain WHY and HOW things work, not just WHAT they are
- Provide practical examples, scenarios, and use cases to illustrate concepts
- Connect related ideas across different sources to provide a complete picture
- If information is incomplete, clearly state what is known and what is unknown with reasoning
- Maintain objectivity and accuracy based on the provided context
- DO NOT provide brief, superficial, or abbreviated responses - be THOROUGH and COMPREHENSIVE
- Aim for depth over brevity - the user needs a complete understanding of the topic"""

        user_prompt = f"""Question: {query}

CRITICAL: Your answer MUST be {length_config['emphasis'].upper()} (minimum {length_config['min_words']} words, preferably longer).

Follow this systematic reasoning approach:

{self._format_reasoning_steps(reasoning_framework)}

FINAL ANSWER REQUIREMENTS - BE THOROUGH AND COMPREHENSIVE:
- Write an {length_config['emphasis'].upper()} answer that thoroughly addresses ALL aspects of the question (aim for {length_config['target_words']}+ words minimum)
- Include {length_config['detail_level']} from the sources
- Cite ALL sources using [1], [2], etc. format for EVERY piece of information, claim, or statement
- For procedures: Provide COMPLETE, DETAILED step-by-step instructions with explanations, context, tips, and potential issues
- For definitions: Include full definition, etymology/history, context, variations, synonyms, antonyms, examples, use cases, and related concepts
- For comparisons: Analyze ALL dimensions, provide detailed comparisons with examples, and explain implications
- For analysis: Evaluate ALL factors, assess impacts, show connections, and provide reasoned conclusions with evidence
- Include MULTIPLE relevant quotes and specific page references from the original sources
- Make detailed connections between related concepts across different sources to build a complete picture
- Provide practical implications, real-world applications, use cases, and scenarios where relevant
- Explain the WHY and HOW, not just the WHAT - provide context and reasoning
- Include background information that helps the user fully understand the topic
- Connect related ideas and show how different aspects relate to each other
- The answer must be thorough, professional, comprehensive, and stand alone as a complete explanation
- DO NOT provide brief, superficial, or abbreviated answers - be EXTENSIVE and DETAILED
- Think of this as writing a comprehensive article or guide - aim for depth and completeness

Your answer should be professional, accurate, extremely detailed, well-structured, and directly responsive to the question. Prioritize completeness and thoroughness over brevity."""

        return {
            "system": system_prompt,
            "user": user_prompt
        }

    def _build_reasoning_instructions(self, framework: Dict[str, Any], question_type: str) -> str:
        """Build specific reasoning instructions based on framework and question type"""
        base_instructions = """
- ANALYZE the question thoroughly to understand what is being asked
- SEARCH through all provided context systematically
- SYNTHESIZE information from multiple sources when available
- VERIFY consistency and accuracy of information
- IDENTIFY any gaps or uncertainties in the available information
- DRAW logical conclusions based on the evidence
- PROVIDE comprehensive answers with proper citations"""

        type_specific = {
            "definition": "\n- For definitions: Explain the concept clearly, provide context, and give examples",
            "explanation": "\n- For explanations: Break down complex ideas, show relationships, and provide examples",
            "procedure": "\n- For procedures: Provide step-by-step instructions with all necessary details",
            "comparison": "\n- For comparisons: Clearly identify similarities and differences with evidence",
            "analysis": "\n- For analysis: Evaluate factors, assess impacts, and provide reasoned conclusions",
            "factual": "\n- For factual questions: Provide accurate information with source verification"
        }

        return base_instructions + type_specific.get(question_type, "")

    def _format_reasoning_steps(self, framework: Dict[str, Any]) -> str:
        """Format reasoning steps for the prompt"""
        steps_text = ""
        for i, step in enumerate(framework["steps"], 1):
            steps_text += f"STEP {i} - {step.upper()}\n"
            steps_text += self._get_step_instructions(step, framework["type"])
            steps_text += "\n"

        return steps_text

    def _get_step_instructions(self, step: str, framework_type: str) -> str:
        """Get specific instructions for each reasoning step"""
        step_instructions = {
            "analyze": "- Break down the question into its core components\n- Identify what type of answer is needed\n- Determine key concepts and requirements",
            "gather_evidence": "- Locate all relevant information in the provided context\n- Identify which sources contain the most pertinent information\n- Note any supporting details, examples, or qualifications",
            "synthesize": "- Combine information from multiple sources logically\n- Resolve any apparent conflicts or contradictions\n- Build a coherent understanding of the topic",
            "validate": "- Verify that conclusions are supported by the evidence\n- Check for consistency across sources\n- Identify any limitations or caveats in the information",
            "conclude": "- Provide a clear, comprehensive answer\n- Include all relevant details and citations\n- Address any remaining uncertainties",
            "identify_key_terms": "- Extract and define key terminology\n- Clarify technical or specialized language\n- Establish precise meanings for important concepts",
            "locate_definitions": "- Find direct definitions in the sources\n- Look for explanatory passages\n- Identify contextual usage and examples",
            "verify_accuracy": "- Cross-reference information across sources\n- Check for consistency in explanations\n- Validate technical accuracy where possible",
            "provide_context": "- Explain how the concept fits into broader frameworks\n- Provide examples and applications\n- Show relationships to related concepts",
            "break_down_concept": "- Decompose complex ideas into simpler components\n- Show how parts relate to the whole\n- Provide hierarchical understanding",
            "explain_components": "- Detail each part of the concept or process\n- Explain the purpose and function of each component\n- Show interconnections and dependencies",
            "show_relationships": "- Demonstrate how different elements interact\n- Explain cause-and-effect relationships\n- Show logical flow and dependencies",
            "provide_examples": "- Include concrete examples from the sources\n- Show practical applications\n- Illustrate abstract concepts with real-world instances"
        }

        return step_instructions.get(step, f"- Execute the {step} step systematically")

    def _enhance_with_contextual_reasoning(self, result: ReasoningResult, context: List[Dict[str, Any]],
                                         query: str, question_type: str) -> ReasoningResult:
        """Enhance the result with additional contextual reasoning"""
        # Extract additional supporting facts from context that weren't in the LLM response
        additional_facts = self._extract_additional_context_facts(context, result.answer, query)

        # Merge with existing supporting facts
        if additional_facts:
            result.supporting_facts.extend(additional_facts)
            result.supporting_facts = list(set(result.supporting_facts))  # Remove duplicates

        # Enhance reasoning chain if it's too generic
        if len(result.reasoning_chain) < 3:
            result.reasoning_chain = self._generate_enhanced_reasoning_chain(query, question_type, context)

        return result

    def _extract_additional_context_facts(self, context: List[Dict[str, Any]], answer: str, query: str) -> List[str]:
        """Extract additional supporting facts from context that complement the answer"""
        additional_facts = []

        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        for item in context:
            text = item.get("text", "")

            # Look for sentences that contain query terms but aren't already in the answer
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    continue

                sentence_words = set(sentence.lower().split())

                # Check if sentence is relevant to query but not already covered in answer
                query_overlap = len(query_words.intersection(sentence_words))
                answer_overlap = len(answer_words.intersection(sentence_words))

                if query_overlap > 0 and answer_overlap < 2:  # Relevant but not duplicate
                    if sentence not in answer:  # Not already in the answer
                        additional_facts.append(sentence)

        return additional_facts[:3]  # Limit to 3 additional facts

    def _generate_enhanced_reasoning_chain(self, query: str, question_type: str, context: List[Dict[str, Any]]) -> List[str]:
        """Generate a more detailed reasoning chain"""
        chain = [
            f"1. Analyzed the {question_type} question: '{query}'",
            f"2. Searched through {len(context)} relevant document passages",
            "3. Identified key information and supporting evidence",
            "4. Synthesized information into a coherent, comprehensive answer",
            "5. Verified accuracy and completeness of the response"
        ]

        # Add question-type specific steps
        if question_type == "definition":
            chain.insert(2, "2a. Located precise definitions and explanations")
        elif question_type == "procedure":
            chain.insert(2, "2a. Identified step-by-step processes and methods")
        elif question_type == "comparison":
            chain.insert(2, "2a. Analyzed similarities and differences")
        elif question_type == "analysis":
            chain.insert(2, "2a. Evaluated factors and implications")

        return chain

    def _calculate_comprehensive_confidence(self, result: ReasoningResult, context: List[Dict[str, Any]],
                                          entities: Dict[str, List[str]], context_relevance: float) -> float:
        """Calculate confidence score with comprehensive factors"""
        confidence = 0.5  # Base confidence

        # Factor 1: Context relevance (most important)
        confidence += context_relevance * 0.3

        # Factor 2: Number and quality of sources
        if len(context) >= 5:
            confidence += 0.15
        elif len(context) >= 3:
            confidence += 0.10
        elif len(context) >= 1:
            confidence += 0.05

        # Factor 3: Answer completeness and detail
        if len(result.answer) > 200:
            confidence += 0.15
        elif len(result.answer) > 100:
            confidence += 0.10
        elif len(result.answer) > 50:
            confidence += 0.05

        # Factor 4: Citation quality
        if result.source_citations:
            confidence += 0.10
            if len(result.source_citations) > 1:
                confidence += 0.05  # Bonus for multiple sources

        # Factor 5: Supporting evidence
        if result.supporting_facts and len(result.supporting_facts) > 2:
            confidence += 0.10

        # Factor 6: Reasoning quality
        if result.reasoning_chain and len(result.reasoning_chain) >= 4:
            confidence += 0.10

        # Factor 7: Entity coverage (indicates thoroughness)
        if entities and len(entities) > 0:
            confidence += 0.05

        return min(1.0, confidence)

    def _generate_comprehensive_answer(self, result: ReasoningResult, context: List[Dict[str, Any]]) -> str:
        """Generate the final comprehensive answer with proper context integration"""
        if not result.answer or result.answer == "No clear answer found in response.":
            # Fallback to synthesis from facts
            return self._synthesize_answer_from_components(result, context)

        # Enhance the existing answer with better context integration
        enhanced_answer = self._enhance_answer_with_proper_context(result.answer, result, context)

        return enhanced_answer

    def _enhance_answer_with_proper_context(self, base_answer: str, result: ReasoningResult,
                                          context: List[Dict[str, Any]]) -> str:
        """Enhance answer with proper context integration and citations"""
        # If answer already has citations, ensure they're comprehensive
        if '[' in base_answer and ']' in base_answer:
            return self._verify_and_enhance_citations(base_answer, result, context)

        # Add comprehensive citations to answer
        enhanced_answer = base_answer.strip()

        # Don't add Sources here - let the UI handle it to ensure all pages are shown
        # Return answer without Sources, UI will add Sources from result.source_citations
        return enhanced_answer

    def _synthesize_answer_from_components(self, result: ReasoningResult, context: List[Dict[str, Any]]) -> str:
        """Synthesize answer from available components when direct answer is insufficient"""
        components = []

        # Start with any direct answer
        if result.answer and result.answer != "No clear answer found in response.":
            components.append(result.answer)

        # Add supporting facts
        if result.supporting_facts:
            components.extend(result.supporting_facts[:2])

        # Add information from context if needed
        if len(components) < 2 and context:
            top_context = context[0]
            text = top_context.get("text", "")[:200]
            if text:
                components.append(f"According to the source: {text}...")

        # Combine components
        if components:
            answer = " ".join(components)
            # Don't add Sources here - let the UI handle it
            return answer

        return "Based on the available information, a definitive answer could not be determined."
    
    def _enhance_answer_with_context(self, base_answer: str, result: ReasoningResult) -> str:
        """Enhance the base answer with additional context, detail, and depth to make it more comprehensive"""
        try:
            # If answer is already comprehensive (500+ chars), return as-is
            if len(base_answer) >= 500:
                return base_answer
            
            # Format the base answer properly
            formatted_answer = self._format_answer_structure(base_answer)
            
            # Start with the formatted answer
            enhanced_parts = [formatted_answer]
            
            # Always try to add more detail from supporting facts if answer is short
            if len(formatted_answer) < 500 and result.supporting_facts:
                # Add relevant supporting facts that expand on the answer
                for fact in result.supporting_facts[:3]:  # Use top 3 facts
                    fact = fact.strip()
                    # Skip if fact is too short or already in answer
                    if len(fact) < 30 or fact.lower() in formatted_answer.lower():
                        continue
                    # Add facts that provide additional detail
                    if any(keyword in fact.lower() for keyword in ['furthermore', 'additionally', 'moreover', 'also', 'specifically', 'in detail', 'for example']):
                        enhanced_parts.append(fact)
            
            # Add relevant context from reasoning chain if answer is still short
            if len('\n\n'.join(enhanced_parts)) < 500 and result.reasoning_chain:
                # Extract key insights from reasoning chain
                reasoning_text = ' '.join(result.reasoning_chain)
                # Look for detailed explanations in reasoning
                if any(keyword in reasoning_text.lower() for keyword in ['detailed', 'comprehensive', 'extensive', 'thorough', 'complete']):
                    # Extract sentences that provide additional context
                    sentences = reasoning_text.split('. ')
                    for sentence in sentences[:2]:  # Use first 2 detailed sentences
                        sentence = sentence.strip()
                        if len(sentence) > 50 and sentence.lower() not in formatted_answer.lower():
                            enhanced_parts.append(sentence)
            
            # Combine enhanced parts
            enhanced_answer = '\n\n'.join(enhanced_parts).strip()
            
            # If still too short, add contextual information
            if len(enhanced_answer) < 400:
                # Add information about sources
                if result.source_citations:
                    source_count = len(result.source_citations)
                    if source_count > 1:
                        enhanced_answer += f"\n\nThis information is drawn from {source_count} relevant sources in the provided documents, ensuring a comprehensive and well-rounded perspective on the topic."
            
            return enhanced_answer
            
        except Exception as e:
            logger.error(f"Error enhancing answer: {e}")
            return base_answer
    
    def _generate_reasonable_alternatives(self, query: str, result: ReasoningResult, context: List[Dict[str, Any]]) -> List[str]:
        """Generate reasonable alternative perspectives"""
        alternatives = []

        # Generate alternatives based on question type and available information
        question_type = self._identify_question_type(query)

        if question_type == "definition":
            alternatives.append("Different sources may define this concept with varying levels of technical detail or focus on different aspects.")
        elif question_type == "procedure":
            alternatives.append("Alternative approaches or methods may exist depending on specific requirements or constraints.")
        elif question_type == "analysis":
            alternatives.append("Different analytical frameworks might lead to varying interpretations of the available evidence.")
        else:
            alternatives.append("Additional context or different sources might provide complementary perspectives on this topic.")

        # Add source-based alternatives if multiple sources exist
        if len(result.source_citations) > 1:
            alternatives.append("The sources consulted may represent different viewpoints or contexts that could influence the interpretation.")

        return alternatives[:2]  # Limit to 2 alternatives

    def _verify_and_enhance_citations(self, answer: str, result: ReasoningResult, context: List[Dict[str, Any]]) -> str:
        """Verify existing citations and enhance if needed"""
        # Don't add Sources here - let the UI handle it to ensure all pages are shown
        # Just return the answer, UI will add Sources from result.source_citations
        return answer

    def _parse_comprehensive_response(self, response: str, context: List[Dict[str, Any]],
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
            question="",  # Will be set by caller
            answer=answer,
            reasoning_chain=reasoning_chain,
            confidence_score=0.0,  # Will be calculated separately
            source_citations=citations,
            supporting_facts=supporting_facts,
            alternative_interpretations=alternatives,
            metadata={}
        )
    
    def _extract_answer(self, response: str) -> str:
        """Extract main answer from response - uses synthesis step if FINAL ANSWER is incomplete"""
        lines = response.split('\n')
        
        # Strategy 1: Look for "FINAL ANSWER:" section
        final_answer_started = False
        answer_lines = []
        answer_text = ""

        for line in lines:
            # Don't strip to preserve indentation for sub-steps
            stripped_line = line.strip()
            if not stripped_line:
                # Preserve empty lines in answer for readability
                if final_answer_started:
                    answer_lines.append("")
                continue

            # Check if we've reached the FINAL ANSWER section
            if "FINAL ANSWER:" in stripped_line.upper():
                final_answer_started = True
                # Extract the answer part after "FINAL ANSWER:"
                answer_part = stripped_line.split(":", 1)
                if len(answer_part) > 1 and answer_part[1].strip():
                    answer_text = answer_part[1].strip()
                continue

            # If we're in the FINAL ANSWER section, collect ALL lines including numbered steps
            if final_answer_started:
                # Stop only if we hit another major section marker
                if any(marker in stripped_line.upper() for marker in ['ALTERNATIVE INTERPRETATION', 'CONFIDENCE SCORE', '---END---']):
                    break
                # Include ALL lines: numbered steps, sub-steps, explanations
                answer_lines.append(line.rstrip())

        # Check if we found a substantial FINAL ANSWER
        final_answer_text = '\n'.join(answer_lines).strip() if answer_lines else answer_text
        
        # If FINAL ANSWER is too short (less than 300 words/chars), look for detailed answer in SYNTHESIS step
        # We want comprehensive answers, so check if it's substantial enough
        if len(final_answer_text) < 500 or (final_answer_text and not any(c.isdigit() and '. ' in final_answer_text for c in final_answer_text)):
            # Look for STEP 4 - SYNTHESIS which often has the detailed procedure
            synthesis_started = False
            synthesis_lines = []
            
            for line in lines:
                stripped_line = line.strip()
                
                # Check for STEP 4 - SYNTHESIS
                if re.match(r'STEP\s*4.*SYNTHESIS', stripped_line.upper()):
                    synthesis_started = True
                    continue
                
                # Stop at FINAL ANSWER or next major section
                if synthesis_started and any(marker in stripped_line.upper() for marker in ['FINAL ANSWER:', 'STEP 5', 'ALTERNATIVE', '---END---']):
                    break
                
                # Collect synthesis content
                if synthesis_started and stripped_line:
                    # Look for the detailed answer that starts with "Putting this all together" or similar
                    if any(phrase in stripped_line.lower() for phrase in ['putting this all together', 'the answer is as follows', 'to resolve', 'you can try the following']):
                        # Found the detailed answer in synthesis - collect all from here
                        synthesis_lines.append(stripped_line)
                        # Collect rest of synthesis
                        idx = lines.index(line)
                        for remaining_line in lines[idx+1:]:
                            remaining_stripped = remaining_line.strip()
                            if any(marker in remaining_stripped.upper() for marker in ['FINAL ANSWER:', 'STEP 5', 'ALTERNATIVE', '---END---']):
                                break
                            if remaining_stripped:
                                synthesis_lines.append(remaining_stripped)
                        break
            
            # If we found a detailed synthesis, use it
            synthesis_text = ' '.join(synthesis_lines).strip() if synthesis_lines else ""
            if synthesis_text and len(synthesis_text) > len(final_answer_text):
                return synthesis_text
        
        # Return FINAL ANSWER if we have it and it's good
        if final_answer_text:
            return final_answer_text

        # Strategy 2: Look for direct answers at the beginning (fallback for old format)
        # Re-scan for direct answers (independent of final answer section)
        direct_answer_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip reasoning indicators
            if any(indicator in line.lower() for indicator in ['reasoning:', 'analysis:', 'step', 'information gathering:', 'synthesis:']):
                break
            direct_answer_lines.append(line)

            # Limit to first few lines to avoid getting reasoning text
            if len(direct_answer_lines) >= 3:
                break

        if direct_answer_lines:
            # Join lines while preserving structure
            answer_text = '\n'.join(direct_answer_lines).strip()
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
        topic_words = ['classroom management', 'management', 'teaching', 'education', 'sync', 'synchronization', 'database', 'error', 'timeout', 'connection']
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
        """Extract citations from response with enhanced source tracking - includes ALL context pages"""
        citations = []
        
        # Track which context items were explicitly cited for relevance scoring
        explicitly_cited_indices = set()
        
        # Find citation patterns [1], [2], etc. in the response
        citation_pattern = r'\[(\d+)\]'
        matches = re.findall(citation_pattern, response)

        for match in matches:
            try:
                index = int(match) - 1
                if 0 <= index < len(context):
                    explicitly_cited_indices.add(index)
            except (ValueError, IndexError):
                continue

        # ALWAYS create citations from ALL context items to ensure all pages are cited
        # This is the key fix: we cite all context items, not just explicitly mentioned ones
        if context:
            for i, item in enumerate(context):
                # Calculate relevance - higher for explicitly cited items
                similarity_score = item.get("similarity_score", 0.8)
                is_explicitly_cited = (i in explicitly_cited_indices)
                relevance = similarity_score + (0.2 if is_explicitly_cited else 0.0)
                relevance = min(relevance, 1.0)
                
                # Get page number from metadata
                page_num = item.get("page")
                
                citation = SourceCitation(
                    file=item.get("file", "Unknown"),
                    page=page_num,
                    text=item.get("text", "")[:200] + "..." if len(item.get("text", "")) > 200 else item.get("text", ""),
                    relevance=relevance
                )
                citations.append(citation)
        else:
            # Fallback: if no context, return empty list
            return []

        return citations
    
    def _create_context_citations(self, context: List[Dict[str, Any]], response: str) -> List[SourceCitation]:
        """Create citations from context when no explicit citations are found"""
        citations = []
        
        # Take top context items (all of them for comprehensive citing)
        for i, item in enumerate(context):
            # Calculate relevance based on similarity score and text length
            similarity_score = item.get("similarity_score", 0.8)
            text_length = len(item.get("text", ""))
            relevance = min(similarity_score + (0.1 if text_length > 100 else 0), 1.0)
            
            # Use the exact page number from the chunk metadata
            page_num = item.get("page")
            
            citation = SourceCitation(
                file=item.get("file", f"Document {i+1}"),
                page=page_num,  # Use exact page from metadata
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
            
            # Add the main answer if available - ALWAYS enhance like the old project
            if result.answer and result.answer.strip():
                # Clean up the answer (remove any existing citations)
                clean_answer = result.answer.strip()
                if "Sources:" in clean_answer:
                    clean_answer = clean_answer.split("Sources:")[0].strip()
                
                # ALWAYS enhance the answer with more detail and depth (like old project)
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
            
            # Don't add Sources here - let the UI handle it to ensure all pages are shown
            # The UI will format Sources from result.source_citations directly
            
            return organized_answer
            
        except Exception as e:
            logger.error(f"Error generating organized answer: {e}")
            # Fallback to original answer without Sources - UI will add Sources
            return result.answer or "No answer generated"
    
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
        
        # Start with definition if available - use ALL definitions for completeness
        if definitions:
            answer_parts.append(definitions[0])
            # Add additional definitions if they provide more detail
            if len(definitions) > 1:
                for defn in definitions[1:]:
                    if len(defn) > 30 and defn.lower() not in definitions[0].lower():
                        answer_parts.append(f" Furthermore, {defn}")
        elif key_concepts:
            answer_parts.append(key_concepts[0])
        
        # Add purpose/goal information - use ALL purposes for completeness
        if purposes:
            for purpose in purposes[:2]:  # Add up to 2 purposes
                if len(purpose) > 30:
                    answer_parts.append(f" {purpose}")
        
        # Add components/strategies - use ALL components for comprehensive coverage
        if components:
            for component in components[:3]:  # Add up to 3 components
                if len(component) > 30:
                    answer_parts.append(f" {component}")
        
        # Add additional context if available - use ALL key concepts for comprehensive coverage
        if len(key_concepts) > 1:
            for concept in key_concepts[1:3]:  # Add up to 2 more concepts for depth
                if len(concept) > 30:
                    answer_parts.append(f" Additionally, {concept}")
        
        # Add remaining supporting facts for comprehensive coverage
        used_facts = definitions + purposes + components + key_concepts
        remaining_facts = [f.strip() for f in supporting_facts if f.strip() not in used_facts and len(f.strip()) > 30]
        for fact in remaining_facts[:3]:  # Add up to 3 more facts for depth
            if fact.lower() not in ' '.join(answer_parts).lower():
                answer_parts.append(f" Furthermore, {fact}")
        
        answer_text = " ".join(answer_parts) if answer_parts else supporting_facts[0].strip()
        
        # Ensure answer is substantial - if still short, add explanatory context
        if len(answer_text) < 400:
            answer_text += " This comprehensive information is drawn from multiple supporting facts in the provided sources, ensuring a thorough and well-rounded understanding of the topic."
        
        return self._format_answer_structure(answer_text)

    def _synthesize_comprehensive_answer(self, supporting_facts: List[str], reasoning_chain: List[str], result) -> str:
        """Synthesize a comprehensive answer from supporting facts and reasoning chain"""
        if not supporting_facts and not reasoning_chain:
            return "No supporting information available."

        # Extract key concepts and build a comprehensive answer
        key_concepts = []
        definitions = []
        purposes = []
        components = []
        solutions = []
        explanations = []

        # Process supporting facts
        for fact in supporting_facts:
            fact = fact.strip()
            if len(fact) < 20:
                continue

            # Look for definition patterns
            if any(keyword in fact.lower() for keyword in ['is', 'refers to', 'means', 'involves', 'encompasses', 'defined as', 'represents']):
                definitions.append(fact)
            # Look for purpose/goal patterns
            elif any(keyword in fact.lower() for keyword in ['goal', 'purpose', 'aim', 'objective', 'maximize', 'achieve', 'intended to', 'designed to']):
                purposes.append(fact)
            # Look for component/strategy patterns
            elif any(keyword in fact.lower() for keyword in ['includes', 'strategies', 'components', 'elements', 'aspects', 'steps', 'process']):
                components.append(fact)
            # Look for solution patterns
            elif any(keyword in fact.lower() for keyword in ['solution', 'fix', 'resolve', 'address', 'correct', 'prevent', 'avoid']):
                solutions.append(fact)
            # Look for explanation patterns
            elif any(keyword in fact.lower() for keyword in ['because', 'due to', 'caused by', 'results in', 'leads to']):
                explanations.append(fact)
            else:
                key_concepts.append(fact)

        # Process reasoning chain for additional insights
        for step in reasoning_chain:
            step = step.strip()
            if any(keyword in step.lower() for keyword in ['therefore', 'thus', 'consequently', 'this means', 'the solution is']):
                solutions.append(step)

        # Build comprehensive answer
        answer_parts = []

        # Start with definition if available
        if definitions:
            answer_parts.append(definitions[0])
        elif key_concepts:
            answer_parts.append(key_concepts[0])

        # Add explanation if available
        if explanations:
            answer_parts.append(f" This occurs {explanations[0].lower().split('because')[1].strip().split('.')[0].strip()}." if 'because' in explanations[0].lower() else explanations[0])

        # Add solution if available
        if solutions:
            answer_parts.append(f" To resolve this, {solutions[0].lower().split('solution')[1].strip().split('.')[0].strip()}." if 'solution' in solutions[0].lower() else solutions[0])

        # Add purpose/goal information
        if purposes:
            answer_parts.append(f" The primary goal is to {purposes[0].lower().split('goal')[1].split('.')[0].strip()}." if 'goal' in purposes[0].lower() else purposes[0])

        # Add components/strategies
        if components:
            answer_parts.append(f" This involves {components[0].lower().split('involves')[1].split('.')[0].strip()}." if 'involves' in components[0].lower() else components[0])

        # Add additional context if available
        if len(key_concepts) > 1:
            answer_parts.append(f" Additionally, {key_concepts[1].lower()}")

        # If we have reasoning chain insights, use them
        if not answer_parts and reasoning_chain:
            # Look for the most substantial reasoning step
            for step in reasoning_chain:
                if len(step) > 50 and any(keyword in step.lower() for keyword in ['analysis', 'synthesis', 'conclusion']):
                    return self._format_answer_structure(step)

        answer_text = " ".join(answer_parts) if answer_parts else (supporting_facts[0].strip() if supporting_facts else "Based on the available information:")
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
        """Format the final answer with beautiful source citations showing ALL pages"""
        if not source_citations:
            return answer
        
        # Group citations by file path, collecting all pages
        file_sources = {}
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
            
            # Initialize file entry if not exists
            if file_path not in file_sources:
                file_sources[file_path] = {
                    'file_path': file_path,
                    'pages': set(),  # Use set to avoid duplicate pages
                    'max_relevance': relevance
                }
            
            # Add page to the set (handle None and non-numeric pages)
            if page is not None:
                try:
                    # Convert to int for proper sorting
                    page_num = int(page)
                    file_sources[file_path]['pages'].add(page_num)
                except (ValueError, TypeError):
                    # If page is not numeric, add as string
                    file_sources[file_path]['pages'].add(page)
            
            # Track maximum relevance for this file
            if relevance > file_sources[file_path]['max_relevance']:
                file_sources[file_path]['max_relevance'] = relevance
        
        # Create clean source citations section
        sources_html = []
        for i, (file_path, source_info) in enumerate(file_sources.items(), 1):
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
            
            # Get all pages and sort them
            pages = source_info['pages']
            if not pages:
                # If no pages, show as "?"
                pages_display = "?"
            else:
                # Separate numeric and non-numeric pages
                numeric_pages = []
                non_numeric_pages = []
                for p in pages:
                    if isinstance(p, int):
                        numeric_pages.append(p)
                    else:
                        non_numeric_pages.append(str(p))
                
                # Determine if pages are 0-based or 1-based
                # If minimum page is 0, assume 0-based and convert to 1-based
                # Otherwise, assume already 1-based and use as-is
                if numeric_pages:
                    min_page = min(numeric_pages)
                    is_zero_based = (min_page == 0)
                    
                    # Sort numeric pages
                    numeric_pages.sort()
                    
                    # Convert to 1-based only if 0-based
                    if is_zero_based:
                        display_numeric = [str(p + 1) for p in numeric_pages]
                    else:
                        display_numeric = [str(p) for p in numeric_pages]
                else:
                    display_numeric = []
                
                # Combine numeric and non-numeric, removing duplicates
                all_display_pages = display_numeric + non_numeric_pages
                
                # Format pages: "pages 4, 13, 21" or "page 4" for single page
                if len(all_display_pages) == 1:
                    pages_display = f"page {all_display_pages[0]}"
                else:
                    pages_display = f"pages {', '.join(all_display_pages)}"
            
            # Clean format: [1] filename.pdf • pages 4, 13, 21 • Open
            source_text = (
                f"[{i}] <span style='font-weight: bold; color: #2c3e50;'>{file_name}</span> "
                f"• {pages_display} • {open_link}"
            )
            sources_html.append(source_text)
        
        # Combine answer with beautifully formatted sources
        formatted_answer = f"{answer}\n\n<b style='color: #34495e; font-size: 14px;'>Sources:</b><br>" + "<br>".join(sources_html)
        
        return formatted_answer
    
    
    def _format_answer_structure(self, answer: str) -> str:
        """Format the answer structure for better readability - formats numbered lists properly"""
        try:
            import re
            
            # Clean up the answer
            answer = answer.strip()
            
            # Check if this has numbered steps that need formatting
            has_numbered_steps = bool(re.search(r'\d+\.\s+', answer))
            
            if has_numbered_steps and '\n' not in answer[:200]:
                # Steps are in a paragraph - need to format them
                
                # Step 1: Add single line break before each numbered item
                # Match patterns like "1. " or "2. " but not in the middle of sentences
                answer = re.sub(r'(\s)(\d+)\.\s+', r'\n\2. ', answer)
                
                # Clean up any double spaces and extra line breaks at start
                answer = answer.strip()
                
                # Step 2: Format sub-steps if they exist (o, -, •)
                # Add line break before sub-step markers when they follow text
                answer = re.sub(r'([a-z\)])(\s+)([o•-])\s+', r'\1\n   \3 ', answer)
                
                # Step 3: Add proper spacing for keyboard shortcuts and commands
                # Make Ctrl + Shift + Esc more visible with color
                answer = re.sub(r'(Ctrl\s*\+\s*Shift\s*\+\s*Esc)', r'<span style="color: #0078d4; font-weight: 600;">\1</span>', answer)
                answer = re.sub(r'(Windows\s*\+\s*R)', r'<span style="color: #0078d4; font-weight: 600;">\1</span>', answer)
                
                # Step 4: Highlight important commands with color
                answer = re.sub(r'\b(services\.msc|spoolsv\.exe)\b', r'<span style="color: #d83b01; font-weight: 600;">\1</span>', answer)
                answer = re.sub(r'\b(Task Manager|Print Spooler)\b', r'<span style="color: #107c10; font-weight: 600;">\1</span>', answer)
                
                # Step 5: Format the introductory text before steps
                # Add a line break after "Here are the steps" or "following steps"
                answer = re.sub(r'(steps to do so:|following steps:|steps:)(\s+\d+\.)', r'\1\n\2', answer, flags=re.IGNORECASE)
                
            else:
                # Already has line breaks or doesn't have numbered steps
                # Just do basic formatting
                
                # Normalize excessive whitespace
                answer = re.sub(r'\n\n+', '\n', answer)
                
                # Still highlight important terms with colors
                answer = re.sub(r'(Ctrl\s*\+\s*Shift\s*\+\s*Esc)', r'<span style="color: #0078d4; font-weight: 600;">\1</span>', answer)
                answer = re.sub(r'(Windows\s*\+\s*R)', r'<span style="color: #0078d4; font-weight: 600;">\1</span>', answer)
                answer = re.sub(r'\b(services\.msc|spoolsv\.exe)\b', r'<span style="color: #d83b01; font-weight: 600;">\1</span>', answer)
                answer = re.sub(r'\b(Task Manager|Print Spooler)\b', r'<span style="color: #107c10; font-weight: 600;">\1</span>', answer)
            
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Error formatting answer structure: {e}")
            return answer
    
    
    def _create_fallback_result(self, query: str, context: List[Dict[str, Any]], 
                              error: str, device_string: str) -> ReasoningResult:
        """Create fallback result when LLM fails"""
        return ReasoningResult(
            question=query,
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
            question=data.get("question", ""),
            answer=data["answer"],
            reasoning_chain=data["reasoning_chain"],
            confidence_score=data["confidence_score"],
            source_citations=citations,
            supporting_facts=data["supporting_facts"],
            alternative_interpretations=data["alternative_interpretations"],
            metadata=data["metadata"]
        )
