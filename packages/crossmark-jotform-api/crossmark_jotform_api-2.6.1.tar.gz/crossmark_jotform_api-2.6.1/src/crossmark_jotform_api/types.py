from typing import Union, Dict, List, Any, TypedDict, Optional


AnswerValue = Union[str, Dict[str, str], List[Any]]


class AnswerObject(TypedDict, total=False):
    text: str
    type: str
    answer: AnswerValue
    prettyFormat: Optional[str]


AnswersDict = Dict[str, AnswerObject]


class Submission(TypedDict, total=False):
    id: str
    form_id: str
    ip: str
    created_at: str
    updated_at: str
    status: str
    new: str
    answers: AnswersDict
    workflowStatus: Optional[str]
    limit_left: Optional[int]  # Only present in single submission response


class JotformAPIResponse(TypedDict):
    responseCode: int
    message: str
    content: List[Submission]
    limit_left: int  # For list submissions endpoint


class JotformSingleSubmissionResponse(TypedDict):
    responseCode: int
    message: str
    content: Submission  # Single submission, may include limit_left


class FormObject(TypedDict, total=False):
    id: str
    username: str
    title: str
    height: str
    status: str
    created_at: str
    updated_at: str
    last_submission: str
    new: str
    count: str
    type: str
    favorite: str
    archived: str
    url: str


class JotformFormAPIResponse(TypedDict):
    responseCode: int
    message: str
    content: Union[List[FormObject], FormObject]
    limit_left: int  # mapped from "limit-left" in JSON
