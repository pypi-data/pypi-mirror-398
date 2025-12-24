"""Types for v4 metrics."""
from pydantic import Field

from trustwise.sdk.types import SDKBaseModel, SDKRequestModel, SDKResponseModel
from trustwise.sdk.utils.docs_utils import sphinx_autodoc


@sphinx_autodoc
class Score(SDKBaseModel):
    """
    A score value between 0 and 100.
    """
    value: float = Field(..., ge=0, le=100, description="Score value between 0 and 100.")
    
    def __float__(self) -> float:
        """Convert to float for arithmetic operations."""
        return self.value
    
    def __str__(self) -> str:
        """String representation."""
        return str(self.value)
    
    def __repr__(self) -> str:
        """Representation."""
        return f"Score({self.value})"


def convert_to_score(v: float | int | dict | Score) -> Score:
    """Convert various input types to Score."""
    if isinstance(v, (int, float)):
        return Score(value=v)
    elif isinstance(v, dict) and "value" in v:
        return Score(value=v["value"])
    elif isinstance(v, Score):
        return v
    else:
        raise ValueError(f"Cannot convert {type(v)} to Score")
@sphinx_autodoc
class ObjectStyleScore(SDKBaseModel):
    """
    Object style score with label.
    """
    label: str = Field(..., description="The label for the score.")
    score: float = Field(..., ge=0, le=100, description="The value of the score. (0-100)")

@sphinx_autodoc
class ContextChunk(SDKBaseModel):
    """
    A single context chunk for v4 context relevancy evaluation.
    """
    chunk_text: str = Field(..., description="The text content of the context chunk.")
    chunk_id: str = Field(..., description="The unique identifier for the context chunk.")

Context = list[ContextChunk]

@sphinx_autodoc
class ContextRelevancyRequest(SDKRequestModel):
    """
    Request type for v4 context relevancy evaluation.
    """
    query: str = Field(..., description="The input query string.")
    context: Context = Field(..., min_length=1, description="A non-empty list of context chunks.")
    severity: float | None = Field(None, ge=0, le=1, description="(Optional) severity level (0-1).")
    include_chunk_scores: bool | None = Field(default=None, description="(Optional) Whether to include individual chunk scores in the response.")
    metadata: dict = Field(None, description="Optional metadata to be returned in the response.")


@sphinx_autodoc
class PromptManipulationRequest(SDKRequestModel):
    """
    Request type for v4 prompt manipulation evaluation.
    """
    text: str = Field(..., description="The text to evaluate for prompt manipulation.")
    severity: int | None = Field(default=None, ge=1, le=1, description="(Optional) Severity level (0-1).")


@sphinx_autodoc
class PromptManipulationResponse(SDKResponseModel):
    """
    Response type for prompt manipulation detection.
    
    Higher scores indicate a greater likelihood that the text contains
    prompt manipulation attempts that could manipulate the AI system.
    """
    score: float = Field(..., ge=0, le=100, description="Overall prompt manipulation score (0-100). A higher score indicates a higher likelihood of the text being used for prompt manipulation.")
    scores: list[ObjectStyleScore] = Field(..., description="Detailed breakdown of manipulation scores by type.")

@sphinx_autodoc
class AnswerRelevancyRequest(SDKRequestModel):
    """
    Request type for answer relevancy evaluation.
    """
    query: str = Field(..., description="The input query string.")
    response: str = Field(..., description="The response to evaluate.")

@sphinx_autodoc
class AnswerRelevancyResponse(SDKResponseModel):
    """
    Response type for answer relevancy evaluation.
    
    Answer relevancy measures how well the response addresses the specific query.
    A higher score indicates the response is more directly relevant to the question asked.
    """
    score: float = Field(..., ge=0, le=100, description="Answer relevancy score (0-100). A higher score, indicating a better response, is correlated with a higher confidence in the response being relevant to the query.")
    generated_question: str = Field(..., description="The generated question for which the response would be relevant.")


@sphinx_autodoc
class FaithfulnessRequest(SDKRequestModel):
    """
    Request type for faithfulness evaluation.
    """
    query: str = Field(..., description="The input query string.")
    response: str = Field(..., description="The response to evaluate.")
    context: Context = Field(..., min_length=1, description="A non-empty list of context chunks.")
    severity: float | None = Field(None, ge=0, le=1, description="(Optional) severity level (0-1).")
    include_citations: bool | None = Field(None, description="Whether to include citations in the response. If true, a unique chunk_id must additionally be provided for each context chunk.")

@sphinx_autodoc
class Statement(SDKBaseModel):
    """
    A verified fact extracted from a response.
    """
    statement: str = Field(
        description="The extracted statement from the response text that represents a 'atomically' fact"
    )
    label: str = Field(
        description="The label indicating the fact's hallucination status. One of ('Safe', 'Unsafe', 'Intrinsic Hallucination', 'Extrinsic Hallucination')"
    )
    probability: float = Field(
        ge=0, le=1, description="The associated probability of the label (0-1)"
    )
    sentence_span: list[int] = Field(
        description="A list of two integers [start, end] indicating the character positions of this statement in the response text"
    )


Statements = list[Statement]
@sphinx_autodoc
class FaithfulnessResponse(SDKBaseModel):
    """
    Response type for faithfulness evaluation.
    
    Faithfulness measures how well the response adheres to the provided context.
    A higher score indicates better alignment with the source material.
    """
    score: float = Field(..., ge=0, le=100, description="Faithfulness score (0-100). A higher score, indicating a better response, is correlated with a higher confidence in each statement being true, and also a higher proportion of statements being true with respect to the context.")
    statements: Statements = Field(
        description="List of extracted 'atomic' statements from the response, each containing the statement, label, associated probability, and location in the text."
    )



@sphinx_autodoc
class ContextRelevancyResponse(SDKResponseModel):
    """
    Response type for context relevancy evaluation.
    
    Context relevancy measures how well the provided context is relevant to the query.
    A higher score indicates the context is more directly relevant to the question asked.
    """
    score: float = Field(..., ge=0, le=100, description="Overall context relevancy score (0-100). A higher score indicates better context relevancy to the query.")
    scores: list[ObjectStyleScore] = Field(..., description="Detailed breakdown of context relevancy scores by aspect.")

@sphinx_autodoc
class ClarityRequest(SDKRequestModel):
    """
    Request type for clarity evaluation.
    
    Clarity measures how easy text is to read. It gives higher scores to writing that contains words which are easier to read, and uses concise, self-contained sentences. It does not measure how well you understand the ideas in the text.
    """
    text: str = Field(..., description="The text to evaluate for clarity.")

@sphinx_autodoc
class ClarityResponse(SDKResponseModel):
    """
    Response type for clarity evaluation.
    
    Clarity scores indicate how clear and understandable the response is.
    Higher scores suggest better readability and comprehension.
    """
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="A score from 0-100 indicating how clear and understandable the response is. "
                   "Higher scores indicate better clarity of the response."
    )

@sphinx_autodoc
class FormalityRequest(SDKRequestModel):
    """
    Request type for formality evaluation.
    
    Formality measures the level of formality in written text,
    distinguishing between casual, conversational, and formal writing styles.
    """
    text: str = Field(..., description="The text to evaluate for formality.")

@sphinx_autodoc
class FormalityResponse(SDKResponseModel):
    """
    Response type for formality evaluation.
    
    Formality scores indicate the level of formality in the text.
    Higher scores indicate more formal writing, lower scores indicate more casual writing.
    """
    score: float = Field(..., ge=0, le=100, description="Formality score (0-100). The Formality metric judges how formal a piece of text is. A higher score indicates the text is more formal, and a lower score indicates the text is more informal.")

@sphinx_autodoc
class SimplicityRequest(SDKRequestModel):
    """
    Request type for simplicity evaluation.
    
    Simplicity measures how easy it is to understand the words in a text. It gives higher scores to writing that uses common, everyday words instead of special terms or complicated words. Simplicity looks at the words you choose, not how you put them together in sentences.
    """
    text: str = Field(..., description="The text to evaluate for simplicity.")

@sphinx_autodoc
class SimplicityResponse(SDKResponseModel):
    """
    Response type for simplicity evaluation.
    
    Simplicity measures how easy it is to understand the words in a text. It gives higher scores to writing that uses common, everyday words instead of special terms or complicated words. Simplicity looks at the words you choose, not how you put them together in sentences.
    """
    score: float = Field(..., ge=0, le=100, description="Simplicity score (0-100). A higher score indicates a simpler response, with fewer words and simpler language which is easier to understand.")

@sphinx_autodoc
class ToneRequest(SDKRequestModel):
    """
    Request type for tone evaluation.
    
    Tone evaluation identifies the emotional tone and sentiment expressed
    in the text across multiple emotional categories.
    """
    text: str = Field(..., description="The text to evaluate for tone.")
    tones: list[str] | None = Field(None, description="The tones to evaluate for tone metric.")

@sphinx_autodoc
class ToneResponse(SDKResponseModel):
    """
    Response type for tone evaluation.
    
    Tone analysis identifies the emotional tones present in the text,
    with confidence scores for each detected tone category.
    """
    scores: list[ObjectStyleScore] = Field(
        description="List of detected tones with confidence scores (0-100). "
                   "Higher scores indicate stronger presence of that tone."
    )

@sphinx_autodoc
class ToxicityRequest(SDKRequestModel):
    """
    Request type for toxicity evaluation.
    
    Toxicity evaluation identifies harmful or inappropriate content
    across multiple categories like threats, insults, and hate speech.
    """
    text: str = Field(..., description="The text to evaluate for toxicity.")
    severity: int | None = Field(None, ge=0, le=1, description="(Optional) Severity level (0-1).")

@sphinx_autodoc
class ToxicityResponse(SDKResponseModel):
    """
    Response type for toxicity evaluation.
    
    Toxicity scores indicate the presence of harmful content across different categories.
    Higher scores indicate more toxic content, so lower scores are preferred.
    """
    score: float = Field(..., ge=0, le=100, description="Toxicity score (0-100). A higher score indicates the text is more toxic, and thus a lower score is preferred.")
    scores: list[ObjectStyleScore] = Field(..., description="List of toxicity scores by category (0-100). A higher score indicates the text is more toxic, and thus a lower score is preferred.")

@sphinx_autodoc
class PIIEntity(SDKBaseModel):
    """
    A detected piece of personally identifiable information.
    
    PII entities represent sensitive information that has been identified
    in text, including its location and category.
    """
    interval: list[int] = Field(..., description="The [start, end] indices of the PII in the text.")
    string: str = Field(..., description="The detected PII string.")
    category: str = Field(..., description="The PII category.")

@sphinx_autodoc
class PIIRequest(SDKRequestModel):
    """
    Request type for PII detection.
    
    PII detection identifies personally identifiable information in text
    based on customizable allowlists and blocklists.
    """
    text: str = Field(..., description="The text to evaluate for PII detection.")
    allowlist: list[str] | None = Field(default=None, description="(Optional) List of allowed PII strings or regex patterns.")
    blocklist: list[str] | None = Field(default=None, description="(Optional) List of blocked PII strings or regex patterns.")
    categories: list[str] | None = Field(default=None, description="(Optional) List of PII categories to evaluate.")

@sphinx_autodoc
class PIIResponse(SDKResponseModel):
    """
    Response type for PII detection.
    
    Contains all detected PII entities with their locations and categories
    for further processing or filtering.
    """
    pii: list[PIIEntity] = Field(..., description="List of detected PII occurrences.")

@sphinx_autodoc
class HelpfulnessRequest(SDKRequestModel):
    """
    Request type for helpfulness evaluation.
    
    Helpfulness measures how useful a given text is. It gives higher scores to texts that fully explain a topic. Helpful responses provide clear, complete information.
    """
    text: str = Field(..., description="The text to evaluate for helpfulness.")

@sphinx_autodoc
class HelpfulnessResponse(SDKResponseModel):
    """
    Response type for helpfulness evaluation.
    
    Helpfulness measureshow useful a given text is. It gives higher scores to texts that fully explain a topic. Helpful responses provide clear, complete information.
    """
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="A score from 0-100 indicating how helpful the response is. "
                   "Higher scores indicate better helpfulness of the response."
    )

@sphinx_autodoc
class SensitivityRequest(SDKRequestModel):
    """
    Request type for sensitivity evaluation.
    """
    text: str = Field(..., description="The text to evaluate for sensitivity.")
    topics: list[str] = Field(..., description="List of topics to check for sensitivity.")

@sphinx_autodoc
class SensitivityResponse(SDKResponseModel):
    """
    Response type for sensitivity evaluation.
    
    Sensitivity evaluation checks for the presence of specific topics or themes
    in the text, providing scores for each requested topic.
    """
    scores: list[ObjectStyleScore] = Field(..., description="List of sensitivity scores for each requested topic (0-100). A high score for a topic indicates that the topic is present in the text.")

@sphinx_autodoc
class RefusalRequest(SDKRequestModel):
    """
    Request type for refusal evaluation.
    
    Refusal measures the likelihood that a response is a refusal to answer or comply with the query.
    This metric helps identify when AI systems decline to provide information or perform tasks.
    """
    query: str = Field(..., description="The input prompt/query sent to the LLM or agent.")
    response: str = Field(..., description="The response from LLM or agent to evaluate.")

@sphinx_autodoc
class RefusalResponse(SDKResponseModel):
    """
    Response type for refusal evaluation.
    
    Refusal scores indicate the likelihood that the response is a refusal to answer or comply.
    Higher scores indicate stronger refusal behavior.
    """
    score: float = Field(..., ge=0, le=100, description="Refusal score (0-100). A higher score indicates a higher degree (firmness) of refusal.")


@sphinx_autodoc
class CompletionRequest(SDKRequestModel):
    """
    Request type for completion evaluation.
    
    Completion measures how well the response completes or follows the query's instruction.
    """
    query: str = Field(..., description="The input prompt/query sent to the LLM or agent.")
    response: str = Field(..., description="The response from LLM or agent to evaluate.")


@sphinx_autodoc
class CompletionResponse(SDKResponseModel):
    """
    Response type for completion evaluation.

    Completion score indicates how well the response completes the query (0-100).
    """
    score: float = Field(..., ge=0, le=100, description="Completion score (0-100). A higher score indicates a better completion of the query.")

@sphinx_autodoc
class AdherenceRequest(SDKRequestModel):
    """
    Request type for adherence evaluation.

    Adherence evaluation measures how well the response follows a given policy or instruction.
    """
    policy: str = Field(..., description="The policy or instruction the response should adhere to.")
    response: str = Field(..., description="The response from LLM or agent to evaluate.")

@sphinx_autodoc
class AdherenceResponse(SDKResponseModel):
    """
    Response type for adherence evaluation.

    Adherence score indicates how well the response follows the policy (0-100).
    """
    score: float = Field(..., ge=0, le=100, description="Adherence score (0-100). A higher score indicates better adherence to the policy.")

@sphinx_autodoc
class StabilityRequest(SDKRequestModel):
    """
    Request type for stability evaluation.

    Stability evaluation measures the consistency of responses to the same prompt.
    """
    responses: list[str] = Field(..., min_length=2, description="A list of responses to evaluate for stability. Must contain at least two responses.")

@sphinx_autodoc
class StabilityResponse(SDKResponseModel):
    """
    Response type for stability evaluation.

    Stability measures how consistent the responses are. A higher score indicates greater consistency among the responses.
    """
    min: int = Field(..., ge=0, le=100, description="An integer, 0-100, measuring the minimum stability between any two pairs of responses (100 is high similarity)")
    avg: int = Field(..., ge=0, le=100, description="An integer, 0-100, measuring the average stability between all two pairs of responses (100 is high similarity)")


@sphinx_autodoc
class CarbonValue(SDKBaseModel):
    """
    A carbon value with unit.
    """
    value: float = Field(..., ge=0, description="The carbon value.")
    unit: str = Field(..., description="The unit of measurement (e.g., 'kg_co2e').")


@sphinx_autodoc
class CarbonComponent(SDKBaseModel):
    """
    A carbon component breakdown.
    """
    component: str = Field(..., description="The component name (e.g., 'operational_gpu', 'operational_cpu', 'embodied_cpu').")
    carbon: CarbonValue = Field(..., description="The carbon value for this component.")


@sphinx_autodoc
class CarbonRequest(SDKRequestModel):
    """
    Request type for carbon evaluation.
    
    Carbon evaluation measures the carbon footprint of AI operations
    based on provider, instance type, region, and latency.
    """
    provider: str = Field(..., description="The cloud provider (e.g., 'azure', 'aws', 'gcp').")
    region: str = Field(..., description="The region where the instance is located.")
    instance_type: str = Field(None, description="The instance type.")
    latency: float | int = Field(..., ge=0, description="The latency in milliseconds.")


@sphinx_autodoc
class CarbonResponse(SDKResponseModel):
    """
    Response type for carbon evaluation.
    
    Carbon evaluation provides the total carbon footprint and breakdown
    by component (operational GPU, operational CPU, embodied CPU).
    """
    carbon: CarbonValue = Field(..., description="The total carbon footprint.")
    components: list[CarbonComponent] = Field(..., description="Breakdown of carbon footprint by component.")
