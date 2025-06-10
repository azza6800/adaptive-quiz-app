
from pydantic import BaseModel
from typing import List
from enum import Enum


class SegmentationsContent(BaseModel):
    Segmentationtitle: str  # Le titre du segment
    Segmentationcontent: str  # Le contenu du segment

class Segmentations(BaseModel):
    courseName: str
    introduction_titres: str
    segmentation_titres: List[SegmentationsContent]  # Liste de SegmentContent pour inclure le titre et le contenu

class QuestionType(str, Enum):
    SINGLE_CHOICE = "single-choice"
    MULTIPLE_CHOICE = "multiple-choice"

class Option(BaseModel):
    optionId: int 
    optionText: str
    isCorrect: bool

class Question(BaseModel):
    questionText: str
    type: QuestionType  
    options: List[Option]

class QuizData(BaseModel):
    title: str
    singleChoiceCount: int
    multipleChoiceCount: int
    questionCount: int
    questions: List[Question]
class QuizResult(BaseModel):
    quiz_title: str
    total_questions: int
    correct_answers: int
    score: float  # Le score en pourcentage
    feedback: str  # Un retour basé sur le score


class Explanation(BaseModel):
    explanation: str  # Contenu de l'explication générée
    score: float  # Score du quiz

class CommendCmd(BaseModel):
    cmdLabel: str
    description: str
    cmd: str



