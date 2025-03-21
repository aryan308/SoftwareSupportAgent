from agents import SoftwareSupport
from code_scraper import get_file_list

def main():
    owner = "langflow-ai"
    repo = "langflow"
    file_list = get_file_list(owner=owner, repo=repo)
    
    # Ensure file_list is not None
    if file_list is None:
        print("No files were returned from get_file_list!")
        return
    
    # Initialize paths as an empty list and append each file path
    paths = []
    for file in file_list:
        if 'path' in file:  # Check if 'path' key exists
            paths.append(file['path'])
    
    prompt = 'I want to deploy lang-flow to my local. Should I use the Dockerfile in deploy or the Dockerfile in the root directory?'
    content = ''
    
    # Create an instance of SoftwareSupport with the prompt, file paths, and additional content
    software_support_instance = SoftwareSupport(prompt=prompt, paths=paths, content=content)
    crew_instance = software_support_instance.crew()
    
    # Kick off the crew process and print the result
    result = crew_instance.kickoff()
    print(result.raw)

if __name__ == "__main__":
    main()
