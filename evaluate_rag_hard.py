"""
RAG System - Advanced Accuracy Evaluation
Tests 10 HARDER questions requiring multi-document reasoning
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

# 10 HARDER Test questions - requiring specific details, cross-referencing, and nuanced understanding
HARD_QUESTIONS = [
    # Specific numeric/date questions
    "What is the exact fee for third-party transfer of a project under K-RERA?",
    "Within how many days must the Authority pass an order on a promoter transfer application?",
    
    # Cross-document reasoning
    "What are the differences between COVID extensions granted in April 2020 vs December 2020?",
    "How do the guidelines for print media advertisements differ from digital portal advertisements?",
    
    # Procedural complexity
    "What happens if a promoter fails to complete a project even after the Force Majeure extension?",
    "What are the exact steps a conciliator must follow if parties reach a settlement agreement?",
    
    # Legal interpretation
    "Under what specific conditions can a landowner be jointly liable with a developer under RERA?",
    "What percentage of allottee consent is required for modifying a sanctioned plan vs transferring promoter rights?",
    
    # Edge cases and specific details
    "What is the time limit for Court Officer to send files to the Appellate Tribunal after an order?",
    "What are the circumstances under which amalgamation of companies does NOT require allottee consent?",
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
    print("RAG SYSTEM - ADVANCED ACCURACY EVALUATION (HARD QUESTIONS)")
    print("=" * 70)
    print(f"\nTesting {len(HARD_QUESTIONS)} challenging questions...\n")
    
    results = []
    
    for i, question in enumerate(HARD_QUESTIONS, 1):
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
        
        # Small delay between requests
        time.sleep(1)
    
    # Save results to JSON
    with open("evaluation_hard_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("ADVANCED EVALUATION COMPLETE")
    print("=" * 70)
    successful = sum(1 for r in results if r["success"])
    print(f"Successful queries: {successful}/{len(HARD_QUESTIONS)}")
    print(f"Results saved to: evaluation_hard_results.json")
    
    return results

if __name__ == "__main__":
    main()
