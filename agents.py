import os
import json
import inspect
from crewai_tools import GithubSearchTool
from litellm import completion
from crewai import Crew, Agent, Task, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
load_dotenv()

# Optionally, you can list available models with:
# models = genai.list_models()
# print(models)

# Initialize the tool for semantic searches within a specific GitHub repository


@CrewBase
class SoftwareSupport:
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    def __init__(self, prompt, repo):
        self.prompt = prompt
        self.repo = repo

    @agent
    def codebase_qna_agent(self) -> Agent:
        """
        Create and configure an agent specialized in answering technical questions based on a given codebase.
        """
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
	github_repo='https://github.com/langflow-ai/langflow',
	gh_token=os.environ["GH_TOKEN"],
	content_types=['code', 'issue'] # Options: code, repo, pr, issue
)],
            llm="gemini/gemini-1.5-pro"  # Use a model optimized for in-depth technical understanding.
        )
        return agent_obj


    @task
    def analyze_codebase_question_task(self) -> Task:
        """
        Create a task for analyzing a codebase to answer technical and general questions.
        The agent should extract key components, understand the architecture, and provide clear explanations.
        """
        return Task(
            description=(
                f"Analyze the given codebase and respond to the following question: {self.prompt}. "
                "Identify the relevant parts of the code, extract key functions, classes, and dependencies, "
                "and explain their role in the overall structure. If the question is technical, provide an in-depth explanation "
                "with examples or refactored code if necessary. If the question is general, explain the use case, design choices, "
                "and intended behavior in a clear and concise manner. "
                "Ensure the response is structured with relevant code snippets, explanations, and suggestions if applicable."
            ),
            expected_output=(
                "A well-structured response containing:\n"
                "- Key components of the codebase relevant to the question\n"
                "- Detailed technical explanation (if applicable)\n"
                "- Clear description of the use case and design choices (if applicable)\n"
                "- Code snippets or refactored examples (if needed)\n"
                "- Best practices, optimizations, or alternative approaches"
            ),
            tools=[GithubSearchTool(
	github_repo='https://github.com/langflow-ai/langflow',
	gh_token=os.environ["GH_TOKEN"],
	content_types=['code', 'issue'] # Options: code, repo, pr, issue
)],
            agent=self.codebase_qna_agent()  # Use the software support agent.
        )

    @task
    def resolve_codebase_question_task(self) -> Task:
        """
        A task for resolving user queries related to a given codebase.
        The agent will analyze the code, understand the context, and provide a clear, actionable solution.
        """
        return Task(
            description=(
                f"Thoroughly analyze the provided codebase to answer the following query: {self.prompt}. "
                "Identify relevant functions, classes, and dependencies, and determine how they interact within the code. "
                "If the query involves debugging, locate potential issues, explain the root cause, and provide a corrected version of the code. "
                "If the query is about implementation or optimization, offer best practices and refactored solutions where necessary. "
                "Ensure the response is well-structured, addressing the core question with precision and clarity."
            ),
            expected_output=(
                "A complete resolution to the query, including:\n"
                "- A clear and concise answer to the user's question\n"
                "- Relevant code snippets demonstrating the solution\n"
                "- Explanation of the identified issue (if applicable)\n"
                "- Suggested fixes, optimizations, or improvements\n"
                "- Best practices and reasoning behind the solution\n"
                "- Steps to verify and validate the solution in the codebase"
            ),tools=[GithubSearchTool(
	github_repo='https://github.com/langflow-ai/langflow',
	gh_token=os.environ["GH_TOKEN"],
	content_types=['code', 'issue'] # Options: code, repo, pr, issue
)],context=[self.analyze_codebase_question_task()],
            agent=self.codebase_qna_agent()  # Use the software support agent.
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.codebase_qna_agent()],
            tasks=[self.analyze_codebase_question_task(), self.resolve_codebase_question_task()],
            process=Process.sequential
        )
