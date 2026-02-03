"""
RAG System Accuracy Evaluation Script
Tests 10 questions against the Legal-Civil-RAG API
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

# 10 Test questions based on the RERA documents
TEST_QUESTIONS = [
    "What is the purpose of the Conciliation and Dispute Resolution Cell?",
    "What are the fees charged by KARERA for services?",
    "What is the procedure for transferring promoter rights to a third party?",
    "What are the guidelines for project registration under K-RERA?",
    "What is the penalty for ongoing projects that are not registered?",
    "What are the guidelines for advertisements on digital portals?",
    "What is the procedure for extension of a real estate project?",
    "What is the standard operating procedure for court orders?",
    "What is the process for incorporating modified sanction plan?",
    "When is a landowner treated as a promoter under RERA?",
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
    print("=" * 60)
    print("RAG SYSTEM ACCURACY EVALUATION")
    print("=" * 60)
    print(f"\nTesting {len(TEST_QUESTIONS)} questions...\n")
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/10] Question: {question}")
        print("-" * 50)
        
        result = query_chat(question)
        
        if result["success"]:
            answer = result["answer"]
            # Truncate for display
            display_answer = answer[:500] + "..." if len(answer) > 500 else answer
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
    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"Successful queries: {successful}/{len(TEST_QUESTIONS)}")
    print(f"Results saved to: evaluation_results.json")
    
    return results

if __name__ == "__main__":
    main()
