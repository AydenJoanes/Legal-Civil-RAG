"""
RAG System - Third Round Advanced Accuracy Evaluation
Tests 10 NEW hard questions requiring specific details and cross-referencing
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

# 10 NEW Hard questions - same difficulty level
HARD_QUESTIONS_V2 = [
    # Specific numeric/date questions
    "What is the minimum font size requirement for RERA registration number in advertisements?",
    "How many days does an opposite party have to consent to conciliation proceedings?",
    
    # Cross-document reasoning  
    "What are the specific documents required for both project registration AND project extension?",
    "Compare the responsibilities of promoters vs real estate agents under RERA Karnataka.",
    
    # Procedural complexity
    "What is the complete step-by-step process for quarterly update submission by promoters?",
    "Describe the full approval workflow when a Member disagrees with a Chairman's draft order.",
    
    # Legal interpretation
    "What are the specific penalties for false information in project registration under Section 59?",
    "Under what conditions can the Authority revoke a project registration?",
    
    # Edge cases and specific details
    "What is the exact format required for the affidavit when transferring promoter rights?",
    "What specific information must be displayed on the K-RERA website for each registered project?",
]

def query_chat(question: str) -> dict:
    """Query the chat API"""
    try:
        response = requests.post(
            f"{API_BASE}/chat/",
            params={"message": question},
            timeout=120
        )
        if response.status_code == 200:
            return {"success": True, "answer": response.json().get("answer", "")}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("=" * 70)
    print("RAG SYSTEM - THIRD ROUND EVALUATION (HARD QUESTIONS V2)")
    print("=" * 70)
    print(f"\nTesting {len(HARD_QUESTIONS_V2)} challenging questions...\n")
    
    results = []
    
    for i, question in enumerate(HARD_QUESTIONS_V2, 1):
        print(f"\n[{i}/10] Question: {question}")
        print("-" * 60)
        
        result = query_chat(question)
        
        if result["success"]:
            answer = result["answer"]
            # Truncate for display
            display_answer = answer[:600] + "..." if len(answer) > 600 else answer
            print(f"Answer: {display_answer}")
            results.append({
                "question": question,
                "answer": answer,
                "success": True
            })
        else:
            print(f"Error: {result['error']}")
            results.append({
                "question": question,
                "answer": None,
                "error": result["error"],
                "success": False
            })
        
        # Small delay between requests to avoid rate limiting
        time.sleep(2)
    
    # Save results to JSON
    with open("evaluation_hard_v2_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("THIRD ROUND EVALUATION COMPLETE")
    print("=" * 70)
    successful = sum(1 for r in results if r["success"])
    print(f"Successful queries: {successful}/{len(HARD_QUESTIONS_V2)}")
    print(f"Results saved to: evaluation_hard_v2_results.json")
    
    return results

if __name__ == "__main__":
    main()
