"""
Demo script for testing Writing Assessment API

This script demonstrates how to use the writing assessment endpoints:
1. Submit writing for assessment
2. Check assessment status
3. Get assessment results
4. Get detailed feedback
5. Get assessment history
"""

import asyncio
import httpx
import json
from datetime import datetime


class WritingAssessmentDemo:
    """Demo class for writing assessment API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def submit_writing_assessment(self, user_id: str) -> str:
        """Submit a writing sample for assessment"""
        
        sample_writing = """
        I believe that technology has significantly improved our daily lives in many ways. 
        Firstly, communication has become much easier with smartphones and the internet. 
        We can talk to people from all over the world instantly through video calls and messaging apps.
        
        Secondly, technology has made education more accessible. Online courses and educational 
        platforms allow people to learn new skills from home. Students can access vast amounts 
        of information and resources that were not available before.
        
        However, there are also some disadvantages. People sometimes become too dependent on 
        technology and lose important social skills. Additionally, excessive use of technology 
        can cause health problems like eye strain and poor posture.
        
        In conclusion, while technology has brought many benefits to our lives, we should use 
        it wisely and maintain a balance between digital and real-world activities.
        """
        
        sample_prompt = """
        Write an essay about how technology has impacted our daily lives. 
        Discuss both positive and negative effects. 
        Your essay should be 200-250 words and include:
        - Introduction with main idea
        - At least 2 body paragraphs with examples  
        - Conclusion that summarizes your points
        """
        
        request_data = {
            "user_id": user_id,
            "writing_text": sample_writing.strip(),
            "writing_prompt": sample_prompt.strip(),
            "vocabulary_weight": 0.35,
            "grammar_weight": 0.35,
            "structure_weight": 0.30,
            "language": "en"
        }
        
        print("📝 Submitting writing for assessment...")
        print(f"Writing length: {len(sample_writing.split())} words")
        
        response = await self.client.post(
            f"{self.base_url}/writing-assessment/submit",
            json=request_data
        )
        
        if response.status_code == 202:
            result = response.json()
            assessment_id = result["assessment_id"]
            print(f"✅ Assessment submitted successfully!")
            print(f"Assessment ID: {assessment_id}")
            print(f"Status: {result['status']}")
            return assessment_id
        else:
            print(f"❌ Error submitting assessment: {response.status_code}")
            print(response.text)
            return None
    
    async def check_assessment_status(self, assessment_id: str, user_id: str):
        """Check the processing status of an assessment"""
        print(f"\n🔍 Checking assessment status...")
        
        response = await self.client.get(
            f"{self.base_url}/writing-assessment/{assessment_id}/status",
            params={"user_id": user_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result['status']}")
            print(f"Progress: {result['progress_percentage']}%")
            print(f"Current step: {result['current_step']}")
            return result["status"]
        else:
            print(f"❌ Error checking status: {response.status_code}")
            return None
    
    async def get_assessment_result(self, assessment_id: str, user_id: str):
        """Get the complete assessment result"""
        print(f"\n📊 Getting assessment results...")
        
        response = await self.client.get(
            f"{self.base_url}/writing-assessment/{assessment_id}",
            params={"user_id": user_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result["status"] == "completed" and result["result"]:
                print("✅ Assessment completed!")
                print(f"Overall Score: {result['result']['overall_score']}/10")
                
                for criterion in result['result']['criterion_scores']:
                    print(f"{criterion['criterion'].title()}: {criterion['score']}/10")
                    print(f"  Feedback: {criterion['feedback'][:100]}...")
                
                return result
            else:
                print(f"Assessment status: {result['status']}")
                if result.get('error_message'):
                    print(f"Error: {result['error_message']}")
        else:
            print(f"❌ Error getting results: {response.status_code}")
        
        return None
    
    async def get_detailed_feedback(self, assessment_id: str, user_id: str):
        """Get detailed feedback with corrections and suggestions"""
        print(f"\n💡 Getting detailed feedback...")
        
        response = await self.client.get(
            f"{self.base_url}/writing-assessment/{assessment_id}/feedback",
            params={"user_id": user_id}
        )
        
        if response.status_code == 200:
            feedback = response.json()
            
            print("📋 Detailed Feedback:")
            print(f"Prompt Adherence: {feedback['prompt_adherence_score']}/10")
            print(f"Feedback: {feedback['prompt_adherence_feedback']}")
            
            if feedback['grammar_corrections']:
                print("\n🔧 Grammar Corrections:")
                for correction in feedback['grammar_corrections'][:3]:  # Show first 3
                    print(f"  Error: '{correction['error_text']}'")
                    print(f"  Correction: '{correction['corrected_text']}'")
                    print(f"  Explanation: {correction['explanation']}")
                    print()
            
            if feedback['vocabulary_enhancements']:
                print("📚 Vocabulary Enhancements:")
                for enhancement in feedback['vocabulary_enhancements'][:3]:  # Show first 3
                    print(f"  '{enhancement['original']}' → '{enhancement['suggestion']}'")
                    print(f"  Reason: {enhancement['context_explanation']}")
                    print()
            
            print("💪 Strengths:")
            for strength in feedback['overall_strengths']:
                print(f"  • {strength}")
            
            print("\n📈 Areas for Improvement:")
            for area in feedback['areas_for_improvement']:
                print(f"  • {area}")
            
            print("\n🎯 Next Steps:")
            for step in feedback['next_steps']:
                print(f"  • {step}")
            
            return feedback
        else:
            print(f"❌ Error getting feedback: {response.status_code}")
            return None
    
    async def get_assessment_history(self, user_id: str):
        """Get user's assessment history"""
        print(f"\n📚 Getting assessment history...")
        
        response = await self.client.get(
            f"{self.base_url}/writing-assessment/users/{user_id}/history",
            params={"page": 1, "per_page": 5}
        )
        
        if response.status_code == 200:
            history = response.json()
            
            print(f"📊 Assessment Statistics:")
            print(f"Total Assessments: {history['total_assessments']}")
            if history['average_score']:
                print(f"Average Score: {history['average_score']:.1f}/10")
            if history['best_score']:
                print(f"Best Score: {history['best_score']:.1f}/10")
            print(f"Trend: {history['improvement_trend']}")
            
            print(f"\n📋 Recent Assessments:")
            for assessment in history['assessments']:
                print(f"  {assessment['created_at'][:10]} - Status: {assessment['status']}")
                if assessment['overall_score']:
                    print(f"    Score: {assessment['overall_score']}/10")
                print(f"    Prompt: {assessment['writing_prompt_preview']}...")
                print()
            
            return history
        else:
            print(f"❌ Error getting history: {response.status_code}")
            return None
    
    async def run_complete_demo(self):
        """Run complete assessment demo"""
        user_id = f"demo_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print("🚀 Starting Writing Assessment Demo")
        print(f"Demo User ID: {user_id}")
        print("=" * 60)
        
        # Step 1: Submit assessment
        assessment_id = await self.submit_writing_assessment(user_id)
        if not assessment_id:
            return
        
        # Step 2: Wait for processing and check status
        print("\n⏳ Waiting for processing...")
        for i in range(30):  # Wait up to 30 seconds
            await asyncio.sleep(2)
            status = await self.check_assessment_status(assessment_id, user_id)
            if status == "completed":
                break
            elif status == "failed":
                print("❌ Assessment processing failed")
                return
        
        # Step 3: Get results
        result = await self.get_assessment_result(assessment_id, user_id)
        if not result:
            return
        
        # Step 4: Get detailed feedback
        await self.get_detailed_feedback(assessment_id, user_id)
        
        # Step 5: Get history
        await self.get_assessment_history(user_id)
        
        print("\n🎉 Demo completed successfully!")
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def main():
    """Main demo function"""
    demo = WritingAssessmentDemo()
    
    try:
        await demo.run_complete_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        await demo.close()


if __name__ == "__main__":
    print("Writing Assessment API Demo")
    print("Make sure the service is running on http://localhost:8000")
    print()
    
    asyncio.run(main())