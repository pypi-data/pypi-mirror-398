from trinitypython.docutils import pdf
from collections import defaultdict
import ollama

prompt_cfg = {
	"prompts": [
		{
			"section": "Requirements Gathering",
			"title": "What questions to ask to clarify scope ?",
			"prompt": "Act like you are a technology consultant. What questions should be asked to gather inventory of components involded in implementing the below project ?\nproject -\n{project}"
		},
		{
			"section": "Automation",
			"title": "What tools are available for automation ?",
			"prompt": "Act like you are a technology consultant. What tools / accelerators are available to automate the below project ?\nproject -\n{project}"
		},
		{
			"section": "Challenges",
			"title": "What are the potential challenges ?",
			"prompt": "Act like you are a technology consultant. What are the potential challenges that i may encounter when implementing the below project ?\nproject -\n{project}"
		},
		{
			"section": "Testing",
			"title": "What regression testing tools are available ?",
			"prompt": "Act like you are a technology consultant. What regression testing tools are available for testing below project ?\nproject -\n{project}"
		},
		{
			"section": "Estimation and Staffing",
			"title": "What people and skillset are required ?",
			"prompt": "Act like you are a technology consultant. What will be the number of people required to implement the below project ? What should be the skillset of the people ?\nproject -\n{project}"
		},
		{
			"section": "Estimation and Staffing",
			"title": "What are different technical components ?",
			"prompt": "Act like you are a technology consultant. What questions should be asked to gather inventory of components involded in implementing the below project ?\nproject -\n{project}"
		},
		{
			"section": "Requirements Gathering",
			"title": "What will be the success criteria ?",
			"prompt": "Act like you are a technology consultant. List down success criteria for implementation of the below project ?\nproject -\n{project}"
		},
		{
			"section": "Requirements Gathering",
			"title": "What are the assumptions ?",
			"prompt": "Act like you are a technology consultant. Enlist assumptions to be communicated to stakeholders in implementing the below project.\nproject -\n{project}"
		},
		{
			"section": "Requirements Gathering",
			"title": "What are the best practices ?",
			"prompt": "Act like you are a technology consultant. Suggest the best practices to be used for the below project.\nproject -\n{project}"
		},
		{
			"section": "DevOPS",
			"title": "What should be the approach ?",
			"prompt": "Act like you are a devops consultant. What is the recommended approach to implement CICD for the below project.\nproject -\n{project}"
		},
		{
			"section": "Testing",
			"title": "What are automation testing tools available ?",
			"prompt": "Act like you are a technology manager. What automation testing tools are available for testing of the below project ?\nproject -\n{project}"
		},
		{
			"section": "Estimation and Staffing",
			"title": "How should I perform estimation ?",
			"prompt": "Act like you are a technology manager. How should i calculate estimated cost for execution of the below project ?\nproject -\n{project}"
		},
		{
			"section": "Estimation and Staffing",
			"title": "What components are to be considered for cost estimation ?",
			"prompt": "Act like you are a technology manager. Enlist the list of components that will be required to perform cost estimation for implementation of the below project ?\nproject -\n{project}"
		},
		{
			"section": "AI",
			"title": "How can AI be used ?",
			"prompt": "Act like you are a technology consultant. List down different tasks where AI can be used in the implementation of the below project ?\nproject -\n{project}"
		},
		{
			"section": "Monitoring",
			"title": "What monitoring tools can be used ?",
			"prompt": "Act like you are a technology consultant. What are the different monitoring tools that can be used in the implementation of the below project ?\nproject -\n{project}"
		},
		{
			"section": "Monitoring",
			"title": "What metrics should be monitored ?",
			"prompt": "Act like you are a technology consultant. What are the different metrics that need to be monitored in the implementation of the below project ?\nproject -\n{project}"
		},
		{
			"section": "Security",
			"title": "Which products can be used for security ?",
			"prompt": "Act like you are a information security advisor. Suggest some security products that can be used for implementing security layer for the below project ?\nproject -\n{project}"
		},
		{
			"section": "Security",
			"title": "What factors are to be considered for security ?",
			"prompt": "Act like you are a information security advisor. What factors are to be considered for implementing security layer for the below project ?\nproject -\n{project}"
		},
		{
			"section": "Testing",
			"title": "What should be done in user acceptance testing ?",
			"prompt": "Act like you are a business analyst. Enlist test cases to be executed as part of user acceptance testing for the below project.\nproject -\n{project}"
		},
		{
			"section": "Testing",
			"title": "What should be done in performance testing ?",
			"prompt": "Act like you are a quality analyst. Enlist test cases to be executed as part of performance testing for the below project.\nproject -\n{project}"
		},
		{
			"section": "Testing",
			"title": "What should be done in integration testing ?",
			"prompt": "Act like you are a quality analyst. Enlist test cases to be executed as part of integration testing for the below project.\nproject -\n{project}"
		}
	]
}

def base_research(proj_desc, out_fl, model, max_retry):
    sections = defaultdict(dict)
    sections["Project Description"]["Description"] = proj_desc

    for elm in prompt_cfg["prompts"]:
        print("Getting answer from model for question:", elm["title"])
        answer = ""
        rem_attempts = max_retry
        while rem_attempts:
            response = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': elm["prompt"].replace("{project}", proj_desc)
                },
            ])
            rem_attempts -= 1
            answer = response['message']['content'].strip()
            if len(answer) > 20:
                break
            elif rem_attempts > 0:
                print("Failed attempt. Retrying")
            else:
                print("Max retry attempts reached. Skipping this " +
                      "question. ")
        sections[elm["section"]][elm["title"]] = answer

    pdf.create_pdf_from_sections(sections,out_fl)

if __name__ == "__main__":
    proj_desc = "Migrate SQL Server on premise to Snowflake on AWS"
    out_fl = r"C:\Users\Dell\OneDrive\Desktop\output_with_links.pdf"
    base_research(proj_desc, out_fl, "phi", 3)
