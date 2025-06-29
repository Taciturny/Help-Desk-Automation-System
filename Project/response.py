"""
Optimized Response Generation System with Higher Confidence
"""

import logging
import os
from typing import Dict, List

import cohere

from data_models import KnowledgeResponse, RetrievalResult
from retrieval import KnowledgeRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Enhanced response generation system with confidence boosting."""

    def __init__(self, cohere_api_key: str, retriever: KnowledgeRetriever = None):
        self.cohere_client = cohere.Client(cohere_api_key)
        self.retriever = retriever

        # Response quality indicators
        self.quality_indicators = {
            "step_by_step": [
                "step",
                "steps",
                "follow",
                "first",
                "then",
                "next",
                "finally",
            ],
            "specific_urls": ["http", "www", ".com", "portal", "website"],
            "escalation_guidance": [
                "contact",
                "escalate",
                "support",
                "help desk",
                "if",
                "when",
            ],
        }

    def _analyze_context_quality(
        self, context_docs: List[RetrievalResult]
    ) -> Dict[str, float]:
        """Analyze the quality of retrieved context."""
        if not context_docs:
            return {"relevance": 0.0, "completeness": 0.0, "specificity": 0.0}

        # Check relevance (average of top 3 scores)
        top_3_scores = [doc.relevance_score for doc in context_docs[:3]]
        avg_relevance = sum(top_3_scores) / len(top_3_scores)

        # Check completeness (content diversity)
        content_types = set()
        for doc in context_docs:
            content_types.add(doc.metadata.get("type", "unknown"))
        completeness = min(1.0, len(content_types) / 3)  # Normalize to 3 types

        # Check specificity (detailed content)
        total_length = sum(len(doc.content) for doc in context_docs[:3])
        specificity = min(1.0, total_length / 1000)  # Normalize to 1000 chars

        return {
            "relevance": avg_relevance,
            "completeness": completeness,
            "specificity": specificity,
        }

    def _enhance_prompt_with_context(
        self,
        query: str,
        context_docs: List[RetrievalResult],
        template_type: str = "standard",
    ) -> str:
        """Create enhanced prompt with better context organization."""

        # Organize context by type for better structure
        context_by_type = {}
        for doc in context_docs[:5]:  # Use top 5 for richer context
            doc_type = doc.metadata.get("type", "general")
            if doc_type not in context_by_type:
                context_by_type[doc_type] = []
            context_by_type[doc_type].append(doc)

        # Build structured context
        context_sections = []
        for doc_type, docs in context_by_type.items():
            section = f"\n=== {doc_type.upper()} INFORMATION ===\n"
            for doc in docs:
                section += f"Source: {doc.source}\n{doc.content}\n\n"
            context_sections.append(section)

        structured_context = "".join(context_sections)

        # Get template with enhanced instructions
        prompt_template = self._get_enhanced_template(template_type)

        return prompt_template.format(
            context=structured_context,
            query=query,
            context_quality=self._analyze_context_quality(context_docs),
        )

    def _get_enhanced_template(self, template_type: str) -> str:
        """Get enhanced templates with better instructions."""

        templates = {
            "standard": """You are an expert IT support assistant. Based on the knowledge base provided, give a comprehensive and helpful response.

{context}

User Question: {query}

Instructions:
- Provide a clear, step-by-step answer when appropriate
- Use specific information from the knowledge base
- Include relevant URLs, portal links, or contact information
- Mention when to escalate to IT support
- Be concise but thorough
- If confidence is low, acknowledge limitations

Response:""",
            "troubleshooting": """You are an expert IT troubleshooting specialist. Provide systematic troubleshooting guidance.

{context}

Technical Issue: {query}

Instructions:
- Start with the most common causes and solutions
- Provide clear, numbered troubleshooting steps
- Include diagnostic questions to help identify the problem
- Specify when to try each step and what to expect
- Clearly indicate when to escalate to technical support
- Include any relevant error codes or symptoms to watch for

Troubleshooting Response:""",
            "installation": """You are an expert IT installation specialist. Provide comprehensive installation guidance.

{context}

Installation Request: {query}

Instructions:
- Start with system requirements and prerequisites
- Provide detailed, step-by-step installation instructions
- Include download links or internal portals when available
- Mention common installation issues and solutions
- Specify post-installation verification steps
- Include who to contact for licensing or approval issues

Installation Guide:""",
            "policy": """You are an expert IT policy advisor. Provide accurate policy information and compliance guidance.

{context}

Policy Question: {query}

Instructions:
- Clearly state the relevant policy requirements
- Explain the reasoning behind the policy when helpful
- Provide specific compliance steps if applicable
- Include consequences of non-compliance if relevant
- Mention who to contact for policy exceptions or clarifications
- Reference specific policy documents when available

Policy Response:""",
        }

        return templates.get(template_type, templates["standard"])

    def _calculate_response_confidence(
        self, query: str, context_docs: List[RetrievalResult], generated_response: str
    ) -> float:
        """Calculate enhanced confidence score for the response."""
        if not context_docs:
            return 0.1

        # Base confidence from retrieval
        context_quality = self._analyze_context_quality(context_docs)
        base_confidence = (
            context_quality["relevance"] * 0.5
            + context_quality["completeness"] * 0.3
            + context_quality["specificity"] * 0.2
        )

        # Response quality indicators
        response_lower = generated_response.lower()
        quality_score = 0.0

        # Check for step-by-step instructions
        if any(
            indicator in response_lower
            for indicator in self.quality_indicators["step_by_step"]
        ):
            quality_score += 0.15

        # Check for specific references (URLs, contacts)
        if any(
            indicator in response_lower
            for indicator in self.quality_indicators["specific_urls"]
        ):
            quality_score += 0.10

        # Check for escalation guidance
        if any(
            indicator in response_lower
            for indicator in self.quality_indicators["escalation_guidance"]
        ):
            quality_score += 0.10

        # Response length appropriateness
        if 50 <= len(generated_response) <= 800:
            quality_score += 0.05

        # Final confidence calculation
        final_confidence = min(1.0, base_confidence + quality_score)
        return final_confidence

    def generate_response(self, query: str, context_docs: List[RetrievalResult]) -> str:
        """Generate enhanced response with better context utilization."""
        try:
            if not context_docs:
                return "I don't have enough information to answer your question. Please contact IT support directly for assistance."

            # Use enhanced prompt
            prompt = self._enhance_prompt_with_context(query, context_docs, "standard")

            response = self.cohere_client.generate(
                model="command",
                prompt=prompt,
                max_tokens=500,  # Increased for more detailed responses
                temperature=0.2,  # Lower for more consistent responses
                k=0,
                p=0.9,
                stop_sequences=["User Question:", "Instructions:"],
            )

            return response.generations[0].text.strip()

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return "I'm having trouble generating a response. Please contact IT support directly."

    def generate_with_template(
        self,
        query: str,
        context_docs: List[RetrievalResult],
        template_type: str = "standard",
    ) -> str:
        """Generate response using specialized templates with enhanced context."""
        try:
            if not context_docs:
                return "I don't have enough information to answer your question. Please contact IT support directly for assistance."

            prompt = self._enhance_prompt_with_context(
                query, context_docs, template_type
            )

            response = self.cohere_client.generate(
                model="command",
                prompt=prompt,
                max_tokens=500,
                temperature=0.2,
                k=0,
                p=0.9,
                stop_sequences=[
                    "User Question:",
                    "Instructions:",
                    "Technical Issue:",
                    "Installation Request:",
                    "Policy Question:",
                ],
            )

            return response.generations[0].text.strip()

        except Exception as e:
            logger.error(f"Template generation error: {e}")
            return "I'm having trouble generating a response. Please contact IT support directly."

    def get_knowledge_response(
        self, query: str, template_type: str = "standard"
    ) -> KnowledgeResponse:
        """Get complete knowledge-based response with enhanced confidence."""
        if not self.retriever:
            raise ValueError("Retriever not initialized")

        # Get relevant documents with more results for better context
        relevant_docs = self.retriever.search_knowledge(query, n_results=7)

        # Generate response
        answer = self.generate_with_template(query, relevant_docs, template_type)

        # Calculate enhanced confidence
        confidence = self._calculate_response_confidence(query, relevant_docs, answer)

        return KnowledgeResponse(
            query=query,
            answer=answer,
            relevant_documents=relevant_docs,
            confidence=confidence,
        )

    def batch_process(self, queries: List[str]) -> List[KnowledgeResponse]:
        """Process multiple queries with enhanced error handling."""
        responses = []
        for query in queries:
            try:
                response = self.get_knowledge_response(query)
                responses.append(response)
                logger.info(
                    f"Processed query: {query[:50]}... (confidence: {response.confidence:.3f})"
                )
            except Exception as e:
                logger.error(f"Error processing '{query}': {e}")
                responses.append(
                    KnowledgeResponse(
                        query=query,
                        answer="Error processing request. Please contact IT support.",
                        relevant_documents=[],
                        confidence=0.0,
                    )
                )
        return responses


if __name__ == "__main__":
    API_KEY = os.getenv("COHERE_API_KEY", "your-api-key-here")

    if API_KEY == "your-api-key-here":
        print("Set COHERE_API_KEY environment variable")
        exit()

    # Initialize systems
    retriever = KnowledgeRetriever(API_KEY)
    generator = ResponseGenerator(API_KEY, retriever)

    # Load knowledge base
    doc_count = retriever.load_knowledge_base()
    print(f"Loaded {doc_count} document chunks")

    # Test queries with different templates
    test_queries = [
        ("How do I reset my password?", "standard"),
        ("My WiFi won't connect", "troubleshooting"),
        ("How to install Slack?", "installation"),
        ("What's the password policy?", "policy"),
    ]

    print("\n=== ENHANCED RESPONSE TESTING ===")
    for query, template in test_queries:
        print(f"\nQuery: {query} ({template})")
        response = generator.get_knowledge_response(query, template)
        print(f"Confidence: {response.confidence:.3f}")
        print(f"Sources used: {len(response.relevant_documents)}")
        print(f"Response: {response.answer[:200]}...")
        if response.confidence > 0.7:
            print("✅ High confidence response")
        elif response.confidence > 0.5:
            print("⚠️ Medium confidence response")
        else:
            print("❌ Low confidence response")
