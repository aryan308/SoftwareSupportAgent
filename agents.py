import os
import json
import inspect
import google.genai as genai
from litellm import completion
from crewai import Crew, Agent, Task, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
load_dotenv()

# Optionally, you can list available models with:
# models = genai.list_models()
# print(models)

@CrewBase
class SoftwareSupport:
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    def __init__(self, prompt, paths, content):
        # 'prompt' holds the user's support query including error logs and system details.
        self.prompt = prompt
        # 'paths' is a list of code file paths from the repository.
        self.paths = paths
        # 'content' can be used for additional context if needed.
        self.content = content

    @agent
    def software_support_agent(self) -> Agent:
        """
        Create and configure an agent for software support inquiries.
        """
        agent_obj = Agent(
            name="SoftwareSupportAgent",
            role="Software Support Specialist",
            goal=(
                f"Analyze the user's support query provided in self.prompt, which may include error logs, "
                "system configuration details, and other relevant information. Identify the root cause and "
                "generate clear, actionable troubleshooting steps and recommendations tailored to the issue."
            ),
            backstory=(
                "A seasoned software support expert with extensive experience in diagnosing and resolving a wide range "
                "of software issues. Trained in best practices for debugging, user support, and system analysis."
            ),
            description=(
                "An intelligent agent that parses support queries by extracting key error messages, system and environment "
                "details, then delivers concise, effective solutions to expedite issue resolution."
            ),
            llm="gemini/gemini-2.0-flash"  # Ensure this model identifier is correct and available.
        )
        return agent_obj

    @task
    def breaking_support_question_task(self) -> Task:
        """
        Create a task to break down the user's support query.
        The prompt instructs the agent to output a structured JSON object with key components of the support issue.
        """
        return Task(
            description=(
                f"Analyze the provided support query: {self.prompt}. "
                "Break it down into its core components by extracting relevant error messages, system configuration details, "
                "environment context, and any pertinent logs. Identify potential root causes and propose actionable troubleshooting steps. "
                "Return ONLY a JSON object with the following keys: 'error_messages', 'system_info', 'possible_causes', and 'troubleshooting_steps'."
            ),
            expected_output=(
                "A JSON object with the keys 'error_messages', 'system_info', 'possible_causes', and 'troubleshooting_steps', "
                "detailing the breakdown of the support query."
            ),
            agent=self.software_support_agent()  # Use the software support agent.
        )

    @task
    def file_relevance_task(self) -> Task:
        """
        Create a task that leverages the output of the support query breakdown and a list of code file paths.
        The prompt instructs the agent to determine which code files are most relevant to address each component
        of the support issue.
        """
        return Task(
            description=(
                "Using the structured support query breakdown (which includes 'error_messages', 'system_info', "
                "'possible_causes', and 'troubleshooting_steps') obtained from the previous task, "
                f"and the provided list of code file paths: {self.paths}, "
                "analyze the codebase to determine which files are most likely related to addressing each component. "
                "Return ONLY a JSON object with the following keys: 'error_messages_files', 'system_info_files', "
                "'possible_causes_files', and 'troubleshooting_steps_files'. Each key's value should be a list of file paths "
                "that are relevant to that specific aspect of the support query."
            ),
            expected_output=(
                "A JSON object with the keys 'error_messages_files', 'system_info_files', "
                "'possible_causes_files', and 'troubleshooting_steps_files', where each value is a list of file paths "
                "identified as relevant for the corresponding support component."
            ),
            agent=self.software_support_agent(),
            context=[self.breaking_support_question_task()]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.software_support_agent()],
            tasks=[self.breaking_support_question_task(), self.file_relevance_task()],
            process=Process.sequential
        )
