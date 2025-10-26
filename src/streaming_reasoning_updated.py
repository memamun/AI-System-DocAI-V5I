# This file shows the changes needed for streaming_reasoning.py _generate_organized_answer_from_json method

# CURRENT (lines 511-555): Always enhances short answers
# UPDATED: Only enhance if answer is <150 chars, otherwise use directly

def _generate_organized_answer_from_json(self, result) -> str:
    """Generate a well-organized final answer from structured JSON reasoning data"""
    try:
        # Start with the main answer
        answer_parts = []

        # Strategy 1: Use the extracted answer if it's good quality
        if result.answer and result.answer.strip() and result.answer != "No clear answer found in response.":
            # Clean up the answer (remove any existing citations)
            clean_answer = result.answer.strip()
            if "Sources:" in clean_answer:
                clean_answer = clean_answer.split("Sources:")[0].strip()

            # Only enhance if the answer is short (indicating it needs more detail)
            if len(clean_answer) < 150:
                enhanced_answer = self._enhance_answer_with_context(clean_answer, result)
                answer_parts.append(enhanced_answer)
            else:
                # Use the good answer directly with proper formatting
                answer_parts.append(self._format_answer_structure(clean_answer))

        # Strategy 2: Generate comprehensive synthesis from supporting facts
        if not answer_parts and result.supporting_facts:
            synthesized = self._synthesize_comprehensive_answer(result.supporting_facts, result.reasoning_chain, result)
            if synthesized and synthesized.strip():
                answer_parts.append(synthesized)

        # Strategy 3: Generate from reasoning chain if no other good answer
        if not answer_parts and result.reasoning_chain:
            synthesized = self._synthesize_answer_from_reasoning(result.reasoning_chain)
            if synthesized and synthesized.strip():
                enhanced = self._enhance_answer_with_context(synthesized, result)
                answer_parts.append(enhanced)

        # Strategy 4: Fallback to basic synthesis
        if not answer_parts:
            if result.supporting_facts:
                answer_parts.append(self._synthesize_answer_from_facts(result.supporting_facts))
            else:
                answer_parts.append("Based on the available information, I can provide the following analysis:")

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


# Also update _enhance_answer_with_context to be more conservative (lines 557-593)
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
        
        # Only enhance if the answer is very short and we have substantial additional information
        if len(formatted_answer) < 80 and (has_high_confidence or len(result.supporting_facts) > 2):
            # Add depth based on available information - but only if it adds real value

            # Only add comprehensive context if we have multiple high-quality sources
            if has_high_confidence and has_multiple_sources and len(result.source_citations) >= 2:
                enhanced_parts.append("This analysis is based on multiple reliable sources and established practices.")

            # Add practical guidance only if the supporting facts clearly mention practical steps
            practical_keywords = ['steps to', 'how to', 'you should', 'you can', 'recommended', 'best practice', 'solution']
            if any(any(keyword in fact.lower() for keyword in practical_keywords) for fact in result.supporting_facts):
                enhanced_parts.append(self._get_implementation_guidance(domain))

            # Add outcome information only if clearly mentioned in facts
            outcome_keywords = ['result', 'outcome', 'benefit', 'improvement', 'success', 'effective']
            if any(any(keyword in fact.lower() for keyword in outcome_keywords) for fact in result.supporting_facts):
                enhanced_parts.append(self._get_outcome_information(domain))
        
        return "\n\n".join(enhanced_parts)
        
    except Exception as e:
        logger.error(f"Error enhancing answer: {e}")
        return base_answer


# Add the _synthesize_comprehensive_answer method (from non-streaming reasoning.py lines 713-793)
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

