from agents import SoftwareSupport

def main():
    repo_link = "https://github.com/langflow-ai/langflow"
    question = "If i had create a model on langflow what step i can do to test the performance and how i can get the output after create the model cause there is a framework that i know testing using eval data which i assumse that the data get from output of the model"
    ss = SoftwareSupport(prompt=question,repo=repo_link)
    r = ss.crew().kickoff()
    print(r.raw)


if __name__ == '__main__':
    main()