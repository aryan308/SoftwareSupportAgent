import os
import json
import inspect
import base64
import requests
from crewai_tools import GithubSearchTool
from litellm import completion
from crewai import Crew, Agent, Task, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@CrewBase
class SoftwareSupport:
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    def __init__(self, prompt, repo):
        self.prompt = prompt
        self.repo = repo
        self.github_token = os.getenv("GITHUB_TOKEN")
        # Fetch metadata and README at initialization
        self.repo_metadata = self._fetch_repo_metadata()
        self.readme_content = self._fetch_readme_content()

    def _parse_repo_url(self):
        # Expecting URL of form https://github.com/owner/repo
        parts = self.repo.rstrip('/').split('/')
        return parts[-2], parts[-1]

    def _fetch_repo_metadata(self):
        owner, name = self._parse_repo_url()
        url = f"https://api.github.com/repos/{owner}/{name}"
        headers = {"Authorization": f"Bearer {self.github_token}"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _fetch_readme_content(self):
        owner, name = self._parse_repo_url()
        url = f"https://api.github.com/repos/{owner}/{name}/readme"
        headers = {"Authorization": f"Bearer {self.github_token}",
                   "Accept": "application/vnd.github.v3+json"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data.get('content', '')).decode('utf-8', errors='ignore')
        return content

    @agent
    def codebase_qna_agent(self) -> Agent:
        """
        Create and configure an agent specialized in answering technical questions based on a given codebase,
        enriched with dynamic metadata and README context.
        """
        # Build structured context
        context_info = [
            {"type": "repo_metadata", "value": f"Name: {self.repo_metadata.get('full_name')}, Description: {self.repo_metadata.get('description')}"},
            {"type": "repo_stats", "value": f"Stars: {self.repo_metadata.get('stargazers_count')}, Forks: {self.repo_metadata.get('forks_count')}, Open issues: {self.repo_metadata.get('open_issues_count')}."},
            {"type": "readme_excerpt", "value": self.readme_content[:1000]},  # first 1000 chars
            {"type": "user_question", "value": f"{self.prompt}"},
            {"type": "model_guidance", "value": "Provide clear technical explanations, code snippets, and debugging steps as needed."}
        ]

        agent_obj = Agent(
            name="CodebaseQnAAgent",
            role="Software Codebase Expert",
            goal=(
                "Analyze and understand the provided codebase to accurately answer user queries. Extract key logic, "
                "dependencies, and implementation details to generate clear, insightful responses. Assist with debugging, "
                "optimizations, and architectural explanations."
            ),
            backstory=(
                "A highly proficient AI software expert with deep knowledge of multiple programming languages, "
                "frameworks, and system architectures. Skilled in reverse engineering, debugging, and explaining "
                "complex code structures to developers at various expertise levels."
            ),
            description=(
                "An intelligent agent designed to analyze code snippets, projects, or entire repositories to provide "
                "context-aware answers. Capable of identifying patterns, suggesting optimizations, troubleshooting "
                "errors, and explaining functionality in clear, actionable steps."
            ),
            tools=[GithubSearchTool(
                github_repo=self.repo,
                gh_token=self.github_token,
                content_types=['code', 'issue']
            )],
            llm="gemini/gemini-1.5-flash",
            context=context_info
        )
        return agent_obj

    @task
    def analyze_codebase_question_task(self) -> Task:
        return Task(
            description=(
                f"Analyze the given codebase and respond to the following question: {self.prompt}. "
                "Identify the relevant parts of the code, extract key functions, classes, and dependencies, "
                "and explain their role in the overall structure. If the question is technical, provide an in-depth explanation "
                "with examples or refactored code if necessary."
            ),
            expected_output=(
                "A well-structured response containing key components, explanations, code snippets, and best practices."
            ),
            tools=[GithubSearchTool(
                github_repo=self.repo,
                gh_token=self.github_token,
                content_types=['code', 'issue']
            )],
            agent=self.codebase_qna_agent()
        )

    @task
    def resolve_codebase_question_task(self) -> Task:
        return Task(
            description=(
                f"Thoroughly analyze the provided codebase to answer the following query: {self.prompt}. "
                "Locate potential issues, explain root causes, and provide fixes or optimizations as needed."
            ),
            expected_output=(
                "A complete resolution with clear answers, code fixes, and validation steps."
            ),
            tools=[GithubSearchTool(
                github_repo=self.repo,
                gh_token=self.github_token,
                content_types=['code', 'issue']
            )],
            context=[self.analyze_codebase_question_task()],
            agent=self.codebase_qna_agent()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.codebase_qna_agent()],
            tasks=[self.analyze_codebase_question_task(), self.resolve_codebase_question_task()],
            process=Process.sequential
        )
