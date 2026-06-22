"""Pydantic models for strict exercise meta validation"""
from pydantic import BaseModel, Field, root_validator
from typing import List, Optional, Union, Literal, Any


class TranslateMeta(BaseModel):
    sourceText: str
    correctAnswer: str
    hints: Optional[List[str]] = None


class ListenChooseMeta(BaseModel):
    correctAnswer: str
    options: List[str]
    sentence: str


class FillBlankSentence(BaseModel):
    text: str
    correctAnswer: str
    options: Optional[List[str]] = None


class FillBlankMeta(BaseModel):
    sentences: List[FillBlankSentence]
    context: Optional[str] = None


class SpeakMeta(BaseModel):
    prompt: str
    expectedText: str


class MatchPair(BaseModel):
    left: str
    right: str


class MatchMeta(BaseModel):
    pairs: List[MatchPair]


class MultipleChoiceOption(BaseModel):
    text: str
    order: int


class MultipleChoiceMeta(BaseModel):
    question: str
    options: List[MultipleChoiceOption]
    correctOrder: List[int]


class WritingPromptMeta(BaseModel):
    prompt: str
    minWords: Optional[int] = None
    maxWords: Optional[int] = None
    exampleAnswer: Optional[str] = None
    criteria: Optional[List[str]] = None


class ImageDescriptionMeta(BaseModel):
    imageUrl: str
    prompt: str
    expectedResults: str


class MatchPodcastQuestion(BaseModel):
    type: Literal['match']
    question: str
    pairs: List[MatchPair]


class TrueFalsePodcastQuestion(BaseModel):
    type: Literal['trueFalse']
    statement: str
    correctAnswer: bool
    explanation: Optional[str] = None


class ListenChoosePodcastQuestion(BaseModel):
    type: Literal['listenChoose']
    question: str
    correctWords: List[str]
    distractorWords: List[str]


class MultipleChoicePodcastQuestion(BaseModel):
    type: Literal['multipleChoice']
    question: str
    options: List[str]
    correctAnswer: str


EnhancedPodcastQuestion = Union[
    MatchPodcastQuestion,
    TrueFalsePodcastQuestion,
    ListenChoosePodcastQuestion,
    MultipleChoicePodcastQuestion
]


class PodcastMediaInfo(BaseModel):
    type: Literal['gif', 'video', 'lottie', 'none']
    url: Optional[str] = None
    thumbnailUrl: Optional[str] = None


class PodcastSegment(BaseModel):
    order: int
    transcript: str
    voiceGender: Literal['male', 'female']
    questions: Optional[List[EnhancedPodcastQuestion]] = None


class PodcastMeta(BaseModel):
    title: str
    description: Optional[str] = None
    showTranscript: Optional[bool] = None
    media: Optional[PodcastMediaInfo] = None
    segments: List[PodcastSegment]


class CompareWordsMeta(BaseModel):
    instruction: str
    word1: str
    word2: str
    correctAnswer: bool
    explanation: Optional[str] = None


META_TYPE_MAP = {
    "translate": TranslateMeta,
    "listen_choose": ListenChooseMeta,
    "fill_blank": FillBlankMeta,
    "speak": SpeakMeta,
    "match": MatchMeta,
    "multiple_choice": MultipleChoiceMeta,
    "writing_prompt": WritingPromptMeta,
    "image_description": ImageDescriptionMeta,
    "podcast": PodcastMeta,
    "compare_words": CompareWordsMeta
}
