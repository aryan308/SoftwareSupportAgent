from agents import SoftwareSupport
import requests
import json
import os
from dotenv import load_dotenv
import time
load_dotenv()
from datetime import datetime

def fetch_github_discussions():
    GITHUB_TOKEN = os.environ["GH_TOKEN"]
    url = "https://api.github.com/graphql"
    
    query = """
    query {
      repository(owner: "langflow-ai", name: "langflow") {
        discussions(first: 2) {
          nodes {
            title
            bodyText
            url
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json={"query": query}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        discussions = data['data']['repository']['discussions']['nodes']
        return discussions
    return None

def save_answer_to_json(question, answer, discussion_url):
    # Create answers directory if it doesn't exist
    if not os.path.exists('answers'):
        os.makedirs('answers')
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"answers/answer_{timestamp}.json"
    
    # Prepare data to save
    data = {
        "question": question,
        "answer": answer,
        "discussion_url": discussion_url,
        "timestamp": timestamp
    }
    
    # Save to JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filename

def main():

    time.sleep(90)
    repo_link = "https://github.com/langflow-ai/langflow"
    discussions = fetch_github_discussions()
    
    if not discussions:
        print("Failed to fetch questions from GitHub discussions")
        return
    
    print(f"Found {len(discussions)} discussions to process")
    
    for i, discussion in enumerate(discussions, 1):
        print(f"\nProcessing question {i}/{len(discussions)}")
        print(f"Title: {discussion['title']}")
        
        ss = SoftwareSupport(
            prompt=discussion['bodyText'],
            repo=repo_link
        )
        r = ss.crew().kickoff()
        
        # Save the answer to a JSON file
        filename = save_answer_to_json(
            question=discussion['bodyText'],
            answer=r.raw,
            discussion_url=discussion['url']
        )
        
        print(f"Answer saved to: {filename}")

                # Add a 60-second delay between questions
        if i <= len(discussions):  # Don't wait after the last question
            print("\nWaiting 60 seconds before processing next question...")
            time.sleep(90)

if __name__ == '__main__':
    main()