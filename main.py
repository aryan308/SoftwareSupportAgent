import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from agents import SoftwareSupport

# Load environment variables from .env
load_dotenv()

# Ensure GITHUB_TOKEN and OPENAI_API_KEY are set in your environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN not found in environment. Please set it in your .env file.")


def fetch_github_discussions():
    """
    Fetch the latest 5 discussion threads from the specified GitHub repository using GraphQL.
    """
    url = "https://api.github.com/graphql"
    query = """
    query {
      repository(owner: "langflow-ai", name: "langflow") {
        discussions(first: 5) {
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
    response.raise_for_status()
    data = response.json()
    return data.get('data', {}) \
               .get('repository', {}) \
               .get('discussions', {}) \
               .get('nodes', [])


def save_answer_to_json(question, answer, discussion_url):
    """
    Save the agent's answer paired with its question and discussion URL to a timestamped JSON file.
    """
    # Create answers directory if it doesn't exist
    os.makedirs('answers', exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"answers/answer_{timestamp}.json"

    data = {
        "question": question,
        "answer": answer,
        "discussion_url": discussion_url,
        "timestamp": timestamp
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filename


def main():
    repo_link = "https://github.com/langflow-ai/langflow"
    discussions = fetch_github_discussions()

    if not discussions:
        print("Failed to fetch questions from GitHub discussions")
        return

    print(f"Found {len(discussions)} discussions to process")

    for i, discussion in enumerate(discussions, start=1):
        title = discussion.get('title')
        question = discussion.get('bodyText')
        url = discussion.get('url')

        print(f"\nProcessing discussion {i}/{len(discussions)}: {title}")

        # Initialize the agent with the question and repo link
        ss = SoftwareSupport(
            prompt=question,
            repo=repo_link
        )

        # Kickoff the crew to get the answer
        result = ss.crew().kickoff()

        # Save the answer to a JSON file
        filename = save_answer_to_json(
            question=question,
            answer=result.raw,
            discussion_url=url
        )
        print(f"Answer saved to: {filename}")

        # Wait 60 seconds between processing each discussion (except after the last)
        if i < len(discussions):
            print("Waiting 60 seconds before processing next discussion...")
            time.sleep(60)


if __name__ == '__main__':
    main()
