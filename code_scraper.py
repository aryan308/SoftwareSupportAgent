import requests
import base64

def get_file_list(owner, repo, branch='main'):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    files = []
    
    response = requests.get(url)
    response.raise_for_status()  # Ensure response is successful
    data = response.json()

    if 'tree' in data:
        files = [file for file in data['tree'] if file['type'] == 'blob']  # Only keep files, not directories

    return files

def get_file_content(owner, repo, path):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    
    if 'content' in data:
        content = base64.b64decode(data['content']).decode()
        return content
    else:
        return f"Content not available for: {path}"

# owner = "langflow-ai"
# repo = "langflow"
# files = get_file_list(owner, repo)

# for file_path in files:
#     print(f"Fetching: {file_path['path']}")
# #     content = get_file_content(owner, repo, file_path['path'])
#     print(content[:500])  # Print first 500 characters to avoid overflow
