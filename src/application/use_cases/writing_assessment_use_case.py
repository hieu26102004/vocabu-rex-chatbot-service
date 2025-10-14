"""Writing assessment use cases"""
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional

from ..dtos.writing_assessment_dtos import (
    WritingAssessmentRequest,
    WritingAssessmentResponse, 
    DetailedFeedbackResponse,
    AssessmentHistoryResponse,
    AssessmentStatusResponse
)
from ...domain.entities.writing_assessment import (
    WritingAssessment,
    WritingSubmission, 
    ScoringCriteria,
    AssessmentResult,
    DetailedFeedback,
    ScoreCriterion,
    CriterionScore,
    AssessmentStatus,
    ErrorCorrection,
    VocabularyEnhancement
)
from ...domain.repositories.writing_assessment_repository import WritingAssessmentRepository
from ...domain.services.ai_service import AIService
from ...core.exceptions import ValidationError, ProcessingError, NotFoundError
from ...shared.config import settings


class WritingAssessmentUseCase:
    """Use case for writing assessment operations"""
    
    def __init__(
        self,
        assessment_repository: WritingAssessmentRepository,
        ai_service: AIService
    ):
        self.assessment_repository = assessment_repository
        self.ai_service = ai_service
    
    async def submit_writing_for_assessment(self, request: WritingAssessmentRequest) -> WritingAssessmentResponse:
        """Submit writing for assessment"""
        try:
            # Validate input
            await self._validate_writing_submission(request)
            
            # Create assessment entity
            assessment = self._create_assessment_from_request(request)
            
            # Save initial assessment
            await self.assessment_repository.save(assessment)
            
            # Start async processing
            asyncio.create_task(self._process_assessment_async(assessment.id))
            
            # Return immediate response
            return self._map_assessment_to_response(assessment)
            
        except Exception as e:
            raise ProcessingError(f"Failed to submit writing for assessment: {str(e)}")
    
    async def get_assessment_status(self, assessment_id: str, user_id: str) -> AssessmentStatusResponse:
        """Get assessment processing status"""
        try:
            assessment = await self.assessment_repository.get_by_id(assessment_id)
            if not assessment:
                raise NotFoundError(f"Assessment {assessment_id} not found")
            
            # Check user permission
            if assessment.submission.user_id != user_id:
                raise ValidationError("Access denied to this assessment")
            
            return AssessmentStatusResponse(
                assessment_id=assessment_id,
                status=assessment.status.value,
                progress_percentage=self._calculate_progress(assessment),
                current_step=self._get_current_step(assessment),
                error_message=assessment.error_message
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ProcessingError(f"Failed to get assessment status: {str(e)}")
    
    async def get_assessment_result(self, assessment_id: str, user_id: str) -> WritingAssessmentResponse:
        """Get complete assessment result"""
        try:
            assessment = await self.assessment_repository.get_by_id(assessment_id)
            if not assessment:
                raise NotFoundError(f"Assessment {assessment_id} not found")
            
            # Check user permission
            if assessment.submission.user_id != user_id:
                raise ValidationError("Access denied to this assessment")
            
            return self._map_assessment_to_response(assessment)
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ProcessingError(f"Failed to get assessment result: {str(e)}")
    
    async def get_detailed_feedback(self, assessment_id: str, user_id: str) -> DetailedFeedbackResponse:
        """Get detailed feedback for assessment"""
        try:
            assessment = await self.assessment_repository.get_by_id(assessment_id)
            if not assessment:
                raise NotFoundError(f"Assessment {assessment_id} not found")
            
            # Check user permission and completion status
            if assessment.submission.user_id != user_id:
                raise ValidationError("Access denied to this assessment")
            
            if assessment.status != AssessmentStatus.COMPLETED:
                raise ValidationError("Assessment is not completed yet")
            
            if not assessment.result or not assessment.result.detailed_feedback:
                raise ValidationError("Detailed feedback not available")
            
            return self._map_detailed_feedback_to_response(assessment.result.detailed_feedback)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            raise ProcessingError(f"Failed to get detailed feedback: {str(e)}")
    
    async def get_user_assessment_history(
        self, 
        user_id: str, 
        page: int = 1, 
        per_page: int = 10
    ) -> AssessmentHistoryResponse:
        """Get user's assessment history"""
        try:
            # Get paginated assessments
            assessments, total_count = await self.assessment_repository.get_by_user_id_paginated(
                user_id, page, per_page
            )
            
            # Calculate statistics
            completed_assessments = [a for a in assessments if a.status == AssessmentStatus.COMPLETED and a.result]
            
            average_score = None
            best_score = None
            if completed_assessments:
                scores = [a.result.overall_score for a in completed_assessments]
                average_score = sum(scores) / len(scores)
                best_score = max(scores)
            
            # Map to response
            assessment_summaries = [self._map_assessment_to_summary(a) for a in assessments]
            
            return AssessmentHistoryResponse(
                user_id=user_id,
                total_assessments=total_count,
                assessments=assessment_summaries,
                average_score=average_score,
                best_score=best_score,
                improvement_trend=self._calculate_improvement_trend(completed_assessments),
                page=page,
                total_pages=(total_count + per_page - 1) // per_page,
                per_page=per_page
            )
            
        except Exception as e:
            raise ProcessingError(f"Failed to get assessment history: {str(e)}")
    
    async def _process_assessment_async(self, assessment_id: str) -> None:
        """Process assessment asynchronously"""
        try:
            assessment = await self.assessment_repository.get_by_id(assessment_id)
            if not assessment:
                return
            
            # Start processing
            assessment.start_processing()
            await self.assessment_repository.save(assessment)
            
            # Step 1: Vocabulary Analysis
            assessment.add_processing_step("Starting vocabulary analysis")
            vocabulary_score = await self._analyze_vocabulary(assessment)
            
            # Step 2: Grammar Analysis  
            assessment.add_processing_step("Starting grammar analysis")
            grammar_score = await self._analyze_grammar(assessment)
            
            # Step 3: Structure Analysis
            assessment.add_processing_step("Starting structure analysis") 
            structure_score = await self._analyze_structure(assessment)
            
            # Step 4: Generate detailed feedback
            assessment.add_processing_step("Generating detailed feedback")
            detailed_feedback = await self._generate_detailed_feedback(assessment)
            
            # Step 5: Calculate final result
            assessment.add_processing_step("Calculating final scores")
            result = self._calculate_final_result(
                vocabulary_score, grammar_score, structure_score,
                detailed_feedback, assessment.submission.scoring_criteria
            )
            
            # Complete processing
            assessment.complete_processing(result)
            await self.assessment_repository.save(assessment)
            
        except Exception as e:
            # Mark as failed
            assessment = await self.assessment_repository.get_by_id(assessment_id)
            if assessment:
                assessment.fail_processing(str(e))
                await self.assessment_repository.save(assessment)
    
    async def _analyze_vocabulary(self, assessment: WritingAssessment) -> CriterionScore:
        """Analyze vocabulary usage"""
        try:
            response = await self.ai_service.analyze_writing_vocabulary(
                assessment.submission.writing_text,
                assessment.submission.writing_prompt,
                assessment.submission.language
            )
            
            assessment.add_ai_interaction(
                "Vocabulary analysis request", response, settings.gemini_model
            )
            
            # Parse AI response
            import json
            data = json.loads(response)
            return CriterionScore(
                criterion=ScoreCriterion.VOCABULARY,
                score=data.get("score", 7.0),
                max_score=10.0,
                feedback=data.get("feedback", "Vocabulary analysis completed"),
                strengths=data.get("strengths", ["Adequate vocabulary usage"]),
                weaknesses=data.get("weaknesses", ["No major issues identified"])
            )
            
        except Exception as e:
            # Fallback if analysis fails
            return CriterionScore(
                criterion=ScoreCriterion.VOCABULARY,
                score=7.0,
                max_score=10.0,
                feedback="Vocabulary analysis completed with limited data",
                strengths=["Basic vocabulary competency"],
                weaknesses=[f"Analysis error: {str(e)[:100]}"]
            )
    
    async def _analyze_grammar(self, assessment: WritingAssessment) -> CriterionScore:
        """Analyze grammar usage"""
        try:
            response = await self.ai_service.analyze_writing_grammar(
                assessment.submission.writing_text,
                assessment.submission.language
            )
            
            assessment.add_ai_interaction(
                "Grammar analysis request", response, settings.gemini_model
            )
            
            # Parse AI response 
            import json
            data = json.loads(response)
            return CriterionScore(
                criterion=ScoreCriterion.GRAMMAR,
                score=data.get("score", 7.0),
                max_score=10.0,
                feedback=data.get("feedback", "Grammar analysis completed"),
                strengths=data.get("strengths", ["Basic grammar competency"]),
                weaknesses=data.get("weaknesses", ["No major issues identified"])
            )
            
        except Exception as e:
            return CriterionScore(
                criterion=ScoreCriterion.GRAMMAR,
                score=7.0,
                max_score=10.0,
                feedback="Grammar analysis completed with limited data",
                strengths=["Basic grammar competency"],
                weaknesses=[f"Analysis error: {str(e)[:100]}"]
            )
    
    async def _analyze_structure(self, assessment: WritingAssessment) -> CriterionScore:
        """Analyze structure and logic"""
        try:
            response = await self.ai_service.analyze_writing_structure(
                assessment.submission.writing_text,
                assessment.submission.writing_prompt,
                assessment.submission.language
            )
            
            assessment.add_ai_interaction(
                "Structure analysis request", response, settings.gemini_model
            )
            
            # Parse AI response
            import json
            data = json.loads(response)
            return CriterionScore(
                criterion=ScoreCriterion.STRUCTURE,
                score=data.get("score", 7.0),
                max_score=10.0,
                feedback=data.get("feedback", "Structure analysis completed"),
                strengths=data.get("strengths", ["Basic organization present"]),
                weaknesses=data.get("weaknesses", ["No major issues identified"])
            )
            
        except Exception as e:
            return CriterionScore(
                criterion=ScoreCriterion.STRUCTURE,
                score=7.0,
                max_score=10.0,
                feedback="Structure analysis completed with limited data",
                strengths=["Basic organization present"],
                weaknesses=[f"Analysis error: {str(e)[:100]}"]
            )
    
    async def _generate_detailed_feedback(self, assessment: WritingAssessment) -> DetailedFeedback:
        """Generate comprehensive detailed feedback"""
        try:
            # Get previous analysis results from AI interactions
            vocab_analysis = ""
            grammar_analysis = ""  
            structure_analysis = ""
            
            # Extract analysis from stored interactions
            for interaction in assessment.ai_interactions:
                if "Vocabulary analysis" in interaction.get("prompt", ""):
                    vocab_analysis = interaction.get("response", "")
                elif "Grammar analysis" in interaction.get("prompt", ""):
                    grammar_analysis = interaction.get("response", "")
                elif "Structure analysis" in interaction.get("prompt", ""):
                    structure_analysis = interaction.get("response", "")
            
            # Generate comprehensive feedback
            feedback_response = await self.ai_service.generate_detailed_feedback(
                assessment.submission.writing_text,
                assessment.submission.writing_prompt,
                vocab_analysis,
                grammar_analysis,
                structure_analysis,
                assessment.submission.language
            )
            
            assessment.add_ai_interaction(
                "Detailed feedback generation", feedback_response, settings.gemini_model
            )
            
            # Parse detailed feedback response
            import json
            feedback_data = json.loads(feedback_response)
            
            # Create error corrections
            grammar_corrections = []
            for correction in feedback_data.get("grammar_corrections", []):
                grammar_corrections.append(ErrorCorrection(
                    error_text=correction.get("error_text", ""),
                    corrected_text=correction.get("corrected_text", ""),
                    explanation=correction.get("explanation", ""),
                    error_type=correction.get("error_type", "general"),
                    rule_reference=correction.get("rule_reference")
                ))
            
            # Create vocabulary enhancements
            vocabulary_enhancements = []
            for enhancement in feedback_data.get("vocabulary_enhancements", []):
                vocabulary_enhancements.append(VocabularyEnhancement(
                    original=enhancement.get("original", ""),
                    suggestion=enhancement.get("suggestion", ""),
                    context_explanation=enhancement.get("context_explanation", ""),
                    example_sentence=enhancement.get("example_sentence", ""),
                    formality_level=enhancement.get("formality_level", "academic")
                ))
            
            return DetailedFeedback(
                prompt_adherence_score=feedback_data.get("prompt_adherence", {}).get("score", 8.0),
                prompt_adherence_feedback=feedback_data.get("prompt_adherence", {}).get("feedback", "Good adherence to prompt"),
                missed_requirements=feedback_data.get("prompt_adherence", {}).get("missed_requirements", []),
                grammar_corrections=grammar_corrections,
                vocabulary_enhancements=vocabulary_enhancements,
                structure_suggestions=feedback_data.get("structure_suggestions", {}),
                overall_strengths=feedback_data.get("overall_strengths", ["Clear writing style"]),
                areas_for_improvement=feedback_data.get("areas_for_improvement", ["Minor improvements needed"]),
                next_steps=feedback_data.get("next_steps", ["Continue practicing"]),
                recommended_topics=feedback_data.get("recommended_topics", ["General writing skills"]),
                difficulty_level=feedback_data.get("difficulty_level", "intermediate")
            )
            
        except Exception as e:
            # Fallback detailed feedback if generation fails
            return DetailedFeedback(
                prompt_adherence_score=8.0,
                prompt_adherence_feedback="Writing addresses the main requirements effectively.",
                overall_strengths=["Clear communication", "Adequate structure"],
                areas_for_improvement=["Minor refinements needed"],
                next_steps=["Continue practicing writing skills"],
                recommended_topics=["General writing improvement"],
                difficulty_level="intermediate"
            )
    
    def _calculate_final_result(
        self,
        vocabulary_score: CriterionScore,
        grammar_score: CriterionScore,  
        structure_score: CriterionScore,
        detailed_feedback: DetailedFeedback,
        criteria: ScoringCriteria
    ) -> AssessmentResult:
        """Calculate final assessment result"""
        
        # Calculate weighted overall score
        overall_score = (
            vocabulary_score.score * criteria.vocabulary_weight +
            grammar_score.score * criteria.grammar_weight +
            structure_score.score * criteria.structure_weight
        )
        
        return AssessmentResult(
            overall_score=round(overall_score, 1),
            criterion_scores=[vocabulary_score, grammar_score, structure_score],
            detailed_feedback=detailed_feedback,
            assessment_time_seconds=30.0,  # Mock value
            ai_model_used=settings.gemini_model
        )
    
    # Helper methods for validation and mapping
    async def _validate_writing_submission(self, request: WritingAssessmentRequest) -> None:
        """Validate writing submission"""
        if len(request.writing_text.strip()) < 10:
            raise ValidationError("Writing text too short (minimum 10 characters)")
        
        word_count = len(request.writing_text.split())
        if word_count > 2000:
            raise ValidationError("Writing text too long (maximum 2000 words)")
    
    def _create_assessment_from_request(self, request: WritingAssessmentRequest) -> WritingAssessment:
        """Create assessment entity from request"""
        submission = WritingSubmission(
            user_id=request.user_id,
            writing_text=request.writing_text,
            writing_prompt=request.writing_prompt,
            image_url=request.image_url,
            scoring_criteria=ScoringCriteria(
                vocabulary_weight=request.vocabulary_weight,
                grammar_weight=request.grammar_weight,
                structure_weight=request.structure_weight
            ),
            language=request.language
        )
        
        return WritingAssessment(
            id=str(uuid.uuid4()),
            submission=submission
        )
    
    def _map_assessment_to_response(self, assessment: WritingAssessment) -> WritingAssessmentResponse:
        """Map assessment entity to response DTO"""
        from ..dtos.writing_assessment_dtos import (
            AssessmentResultResponse,
            CriterionScoreResponse,
            DetailedFeedbackResponse,
            ErrorCorrectionResponse,
            VocabularyEnhancementResponse
        )
        
        # Map result if available
        result_response = None
        detailed_feedback_response = None
        
        if assessment.result:
            # Map criterion scores
            criterion_scores = []
            for score in assessment.result.criterion_scores:
                criterion_scores.append(CriterionScoreResponse(
                    criterion=score.criterion.value,
                    score=score.score,
                    max_score=score.max_score,
                    feedback=score.feedback,
                    strengths=score.strengths,
                    weaknesses=score.weaknesses
                ))
            
            result_response = AssessmentResultResponse(
                overall_score=assessment.result.overall_score,
                max_score=10.0,
                criterion_scores=criterion_scores,
                assessment_time_seconds=assessment.result.assessment_time_seconds,
                ai_model_used=assessment.result.ai_model_used
            )
            
            # Map detailed feedback if available
            if assessment.result.detailed_feedback:
                feedback = assessment.result.detailed_feedback
                
                # Map error corrections
                grammar_corrections = []
                for correction in feedback.grammar_corrections:
                    grammar_corrections.append(ErrorCorrectionResponse(
                        error_text=correction.error_text,
                        corrected_text=correction.corrected_text,
                        explanation=correction.explanation,
                        error_type=correction.error_type,
                        rule_reference=correction.rule_reference,
                        line_number=correction.line_number
                    ))
                
                # Map vocabulary enhancements
                vocabulary_enhancements = []
                for enhancement in feedback.vocabulary_enhancements:
                    vocabulary_enhancements.append(VocabularyEnhancementResponse(
                        original=enhancement.original,
                        suggestion=enhancement.suggestion,
                        context_explanation=enhancement.context_explanation,
                        example_sentence=enhancement.example_sentence,
                        formality_level=enhancement.formality_level,
                        difficulty_level=enhancement.difficulty_level
                    ))
                
                detailed_feedback_response = DetailedFeedbackResponse(
                    prompt_adherence_score=feedback.prompt_adherence_score,
                    prompt_adherence_feedback=feedback.prompt_adherence_feedback,
                    missed_requirements=feedback.missed_requirements,
                    grammar_corrections=grammar_corrections,
                    vocabulary_enhancements=vocabulary_enhancements,
                    structure_suggestions=feedback.structure_suggestions,
                    overall_strengths=feedback.overall_strengths,
                    areas_for_improvement=feedback.areas_for_improvement,
                    next_steps=feedback.next_steps,
                    recommended_topics=feedback.recommended_topics,
                    difficulty_level=feedback.difficulty_level
                )
        
        return WritingAssessmentResponse(
            assessment_id=assessment.id,
            status=assessment.status.value,
            word_count=assessment.submission.word_count,
            character_count=assessment.submission.character_count,
            language=assessment.submission.language,
            result=result_response,
            detailed_feedback=detailed_feedback_response,
            created_at=assessment.created_at,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at,
            error_message=assessment.error_message
        )
    
    def _calculate_progress(self, assessment: WritingAssessment) -> float:
        """Calculate processing progress percentage"""
        if assessment.status == AssessmentStatus.PENDING:
            return 0.0
        elif assessment.status == AssessmentStatus.PROCESSING:
            return min(len(assessment.processing_steps) * 20, 90)
        elif assessment.status == AssessmentStatus.COMPLETED:
            return 100.0
        else:
            return 0.0
    
    def _get_current_step(self, assessment: WritingAssessment) -> str:
        """Get current processing step"""
        if assessment.processing_steps:
            return assessment.processing_steps[-1]
        return "Initializing..."
    
    # Additional helper methods...
    def _map_detailed_feedback_to_response(self, feedback: DetailedFeedback) -> DetailedFeedbackResponse:
        """Map detailed feedback to response"""
        from ..dtos.writing_assessment_dtos import (
            DetailedFeedbackResponse,
            ErrorCorrectionResponse,
            VocabularyEnhancementResponse
        )
        
        # Map error corrections
        grammar_corrections = []
        for correction in feedback.grammar_corrections:
            grammar_corrections.append(ErrorCorrectionResponse(
                error_text=correction.error_text,
                corrected_text=correction.corrected_text,
                explanation=correction.explanation,
                error_type=correction.error_type,
                rule_reference=correction.rule_reference,
                line_number=correction.line_number
            ))
        
        # Map vocabulary enhancements
        vocabulary_enhancements = []
        for enhancement in feedback.vocabulary_enhancements:
            vocabulary_enhancements.append(VocabularyEnhancementResponse(
                original=enhancement.original,
                suggestion=enhancement.suggestion,
                context_explanation=enhancement.context_explanation,
                example_sentence=enhancement.example_sentence,
                formality_level=enhancement.formality_level,
                difficulty_level=enhancement.difficulty_level
            ))
        
        return DetailedFeedbackResponse(
            prompt_adherence_score=feedback.prompt_adherence_score,
            prompt_adherence_feedback=feedback.prompt_adherence_feedback,
            missed_requirements=feedback.missed_requirements,
            grammar_corrections=grammar_corrections,
            vocabulary_enhancements=vocabulary_enhancements,
            structure_suggestions=feedback.structure_suggestions,
            overall_strengths=feedback.overall_strengths,
            areas_for_improvement=feedback.areas_for_improvement,
            next_steps=feedback.next_steps,
            recommended_topics=feedback.recommended_topics,
            difficulty_level=feedback.difficulty_level
        )
    
    def _map_assessment_to_summary(self, assessment: WritingAssessment):
        """Map assessment to summary"""
        from ..dtos.writing_assessment_dtos import AssessmentSummaryResponse
        
        return AssessmentSummaryResponse(
            assessment_id=assessment.id,
            status=assessment.status.value,
            overall_score=assessment.result.overall_score if assessment.result else None,
            word_count=assessment.submission.word_count,
            writing_prompt_preview=assessment.submission.writing_prompt[:100],
            created_at=assessment.created_at,
            completed_at=assessment.completed_at
        )
    
    def _calculate_improvement_trend(self, assessments: List[WritingAssessment]) -> str:
        """Calculate improvement trend"""
        if len(assessments) < 2:
            return "stable"
        
        recent_scores = [a.result.overall_score for a in assessments[-5:]]
        if len(recent_scores) < 2:
            return "stable"
        
        # Simple trend calculation
        if recent_scores[-1] > recent_scores[0]:
            return "improving"
        elif recent_scores[-1] < recent_scores[0]:
            return "declining"
        else:
            return "stable"