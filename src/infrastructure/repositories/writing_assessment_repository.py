"""MongoDB implementation for writing assessment repository"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection

from ...domain.entities.writing_assessment import (
    WritingAssessment, 
    WritingSubmission,
    ScoringCriteria,
    AssessmentResult,
    DetailedFeedback,
    CriterionScore,
    ErrorCorrection,
    VocabularyEnhancement,
    ScoreCriterion,
    AssessmentStatus
)
from ...domain.repositories.writing_assessment_repository import WritingAssessmentRepository as WritingAssessmentRepositoryInterface


class WritingAssessmentRepository(WritingAssessmentRepositoryInterface):
    """MongoDB implementation of writing assessment repository"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def save(self, assessment: WritingAssessment) -> None:
        """Save or update an assessment"""
        document = self._assessment_to_document(assessment)
        await self.collection.replace_one(
            {"_id": assessment.id},
            document,
            upsert=True
        )
    
    async def get_by_id(self, assessment_id: str) -> Optional[WritingAssessment]:
        """Get assessment by ID"""
        document = await self.collection.find_one({"_id": assessment_id})
        if document:
            return self._document_to_assessment(document)
        return None
    
    async def get_by_user_id(self, user_id: str) -> List[WritingAssessment]:
        """Get all assessments for a user"""
        cursor = self.collection.find(
            {"submission.user_id": user_id}
        ).sort("created_at", -1)
        
        assessments = []
        async for document in cursor:
            assessments.append(self._document_to_assessment(document))
        
        return assessments
    
    async def get_by_user_id_paginated(
        self, 
        user_id: str, 
        page: int, 
        per_page: int
    ) -> Tuple[List[WritingAssessment], int]:
        """Get paginated assessments for a user"""
        
        # Count total documents
        total_count = await self.collection.count_documents(
            {"submission.user_id": user_id}
        )
        
        # Get paginated results
        skip = (page - 1) * per_page
        cursor = self.collection.find(
            {"submission.user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(per_page)
        
        assessments = []
        async for document in cursor:
            assessments.append(self._document_to_assessment(document))
        
        return assessments, total_count
    
    async def delete(self, assessment_id: str) -> bool:
        """Delete an assessment"""
        result = await self.collection.delete_one({"_id": assessment_id})
        return result.deleted_count > 0
    
    async def get_recent_assessments(self, limit: int = 10) -> List[WritingAssessment]:
        """Get recent assessments across all users"""
        cursor = self.collection.find().sort("created_at", -1).limit(limit)
        
        assessments = []
        async for document in cursor:
            assessments.append(self._document_to_assessment(document))
        
        return assessments
    
    def _assessment_to_document(self, assessment: WritingAssessment) -> Dict[str, Any]:
        """Convert assessment entity to MongoDB document"""
        document = {
            "_id": assessment.id,
            "submission": {
                "user_id": assessment.submission.user_id,
                "writing_text": assessment.submission.writing_text,
                "writing_prompt": assessment.submission.writing_prompt,
                "image_url": assessment.submission.image_url,
                "image_description": assessment.submission.image_description,
                "scoring_criteria": {
                    "vocabulary_weight": assessment.submission.scoring_criteria.vocabulary_weight,
                    "grammar_weight": assessment.submission.scoring_criteria.grammar_weight,
                    "structure_weight": assessment.submission.scoring_criteria.structure_weight,
                    "max_score": assessment.submission.scoring_criteria.max_score,
                    "min_score": assessment.submission.scoring_criteria.min_score,
                },
                "language": assessment.submission.language,
                "word_count": assessment.submission.word_count,
                "character_count": assessment.submission.character_count,
            },
            "status": assessment.status.value,
            "error_message": assessment.error_message,
            "created_at": assessment.created_at,
            "started_at": assessment.started_at,
            "completed_at": assessment.completed_at,
            "processing_steps": assessment.processing_steps,
            "ai_interactions": assessment.ai_interactions,
        }
        
        # Add result if available
        if assessment.result:
            document["result"] = {
                "overall_score": assessment.result.overall_score,
                "criterion_scores": [
                    {
                        "criterion": score.criterion.value,
                        "score": score.score,
                        "max_score": score.max_score,
                        "feedback": score.feedback,
                        "strengths": score.strengths,
                        "weaknesses": score.weaknesses,
                    }
                    for score in assessment.result.criterion_scores
                ],
                "assessment_time_seconds": assessment.result.assessment_time_seconds,
                "ai_model_used": assessment.result.ai_model_used,
            }
            
            # Add detailed feedback if available
            if assessment.result.detailed_feedback:
                feedback = assessment.result.detailed_feedback
                document["result"]["detailed_feedback"] = {
                    "prompt_adherence_score": feedback.prompt_adherence_score,
                    "prompt_adherence_feedback": feedback.prompt_adherence_feedback,
                    "missed_requirements": feedback.missed_requirements,
                    "grammar_corrections": [
                        {
                            "error_text": correction.error_text,
                            "corrected_text": correction.corrected_text,
                            "explanation": correction.explanation,
                            "error_type": correction.error_type,
                            "rule_reference": correction.rule_reference,
                            "line_number": correction.line_number,
                        }
                        for correction in feedback.grammar_corrections
                    ],
                    "vocabulary_enhancements": [
                        {
                            "original": enhancement.original,
                            "suggestion": enhancement.suggestion,
                            "context_explanation": enhancement.context_explanation,
                            "example_sentence": enhancement.example_sentence,
                            "formality_level": enhancement.formality_level,
                            "difficulty_level": enhancement.difficulty_level,
                        }
                        for enhancement in feedback.vocabulary_enhancements
                    ],
                    "structure_suggestions": feedback.structure_suggestions,
                    "overall_strengths": feedback.overall_strengths,
                    "areas_for_improvement": feedback.areas_for_improvement,
                    "next_steps": feedback.next_steps,
                    "recommended_topics": feedback.recommended_topics,
                    "difficulty_level": feedback.difficulty_level,
                }
        
        return document
    
    def _document_to_assessment(self, document: Dict[str, Any]) -> WritingAssessment:
        """Convert MongoDB document to assessment entity"""
        
        # Create submission
        submission_data = document["submission"]
        scoring_criteria_data = submission_data["scoring_criteria"]
        
        submission = WritingSubmission(
            user_id=submission_data["user_id"],
            writing_text=submission_data["writing_text"],
            writing_prompt=submission_data["writing_prompt"],
            image_url=submission_data.get("image_url"),
            image_description=submission_data.get("image_description"),
            scoring_criteria=ScoringCriteria(
                vocabulary_weight=scoring_criteria_data["vocabulary_weight"],
                grammar_weight=scoring_criteria_data["grammar_weight"],
                structure_weight=scoring_criteria_data["structure_weight"],
                max_score=scoring_criteria_data["max_score"],
                min_score=scoring_criteria_data["min_score"],
            ),
            language=submission_data["language"],
            word_count=submission_data["word_count"],
            character_count=submission_data["character_count"],
        )
        
        # Create assessment
        assessment = WritingAssessment(
            id=document["_id"],
            submission=submission,
            status=AssessmentStatus(document["status"]),
            error_message=document.get("error_message"),
            created_at=document["created_at"],
            started_at=document.get("started_at"),
            completed_at=document.get("completed_at"),
            processing_steps=document.get("processing_steps", []),
            ai_interactions=document.get("ai_interactions", []),
        )
        
        # Add result if available
        if "result" in document:
            result_data = document["result"]
            
            # Create criterion scores
            criterion_scores = []
            for score_data in result_data["criterion_scores"]:
                criterion_scores.append(CriterionScore(
                    criterion=ScoreCriterion(score_data["criterion"]),
                    score=score_data["score"],
                    max_score=score_data["max_score"],
                    feedback=score_data["feedback"],
                    strengths=score_data["strengths"],
                    weaknesses=score_data["weaknesses"],
                ))
            
            # Create detailed feedback if available
            detailed_feedback = None
            if "detailed_feedback" in result_data:
                feedback_data = result_data["detailed_feedback"]
                
                # Create grammar corrections
                grammar_corrections = []
                for correction_data in feedback_data["grammar_corrections"]:
                    grammar_corrections.append(ErrorCorrection(
                        error_text=correction_data["error_text"],
                        corrected_text=correction_data["corrected_text"],
                        explanation=correction_data["explanation"],
                        error_type=correction_data["error_type"],
                        rule_reference=correction_data.get("rule_reference"),
                        line_number=correction_data.get("line_number"),
                    ))
                
                # Create vocabulary enhancements
                vocabulary_enhancements = []
                for enhancement_data in feedback_data["vocabulary_enhancements"]:
                    vocabulary_enhancements.append(VocabularyEnhancement(
                        original=enhancement_data["original"],
                        suggestion=enhancement_data["suggestion"],
                        context_explanation=enhancement_data["context_explanation"],
                        example_sentence=enhancement_data["example_sentence"],
                        formality_level=enhancement_data["formality_level"],
                        difficulty_level=enhancement_data["difficulty_level"],
                    ))
                
                detailed_feedback = DetailedFeedback(
                    prompt_adherence_score=feedback_data["prompt_adherence_score"],
                    prompt_adherence_feedback=feedback_data["prompt_adherence_feedback"],
                    missed_requirements=feedback_data["missed_requirements"],
                    grammar_corrections=grammar_corrections,
                    vocabulary_enhancements=vocabulary_enhancements,
                    structure_suggestions=feedback_data["structure_suggestions"],
                    overall_strengths=feedback_data["overall_strengths"],
                    areas_for_improvement=feedback_data["areas_for_improvement"],
                    next_steps=feedback_data["next_steps"],
                    recommended_topics=feedback_data["recommended_topics"],
                    difficulty_level=feedback_data["difficulty_level"],
                )
            
            # Create assessment result
            assessment.result = AssessmentResult(
                overall_score=result_data["overall_score"],
                criterion_scores=criterion_scores,
                detailed_feedback=detailed_feedback,
                assessment_time_seconds=result_data["assessment_time_seconds"],
                ai_model_used=result_data["ai_model_used"],
            )
        
        return assessment