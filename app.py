import smtplib
import os
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Tuple


app = Flask(__name__)
cors = CORS(app)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


@app.route("/email_sender", methods=["POST"])
def postME():
    data = request.get_json()
    company_name = data['project']['projectApplication']['businessDetails']['name']
    contact_name = data['project']['projectApplication']['businessDetails']['contactPerson']['name']
    project_name = data['project']['projectApplication']['projectDetails']['projectName']
    project_description = data['project']['projectApplication']['projectDetails']['description']
    project_requirements = data['project']['projectApplication']['projectDetails']['requirements']
    project_skills = [project_requirement['skill'] for project_requirement in project_requirements]

    candidates_list = data['candidates']
    """
    candidates_per_requirements = []
    for candidates in candidates_list:
        candidates_per_requirements.append([
            {
                'name': candidate['profile_name'],
                'role': candidate['role'],
                'seniority': candidate['seniority'],
                'explanation': candidate['explanation'],
            }
            for candidate in candidates
        ])
    """

    # Send to the client
    prompt = build_company_email_prompt(company_name, contact_name, project_name, project_skills, candidates_list)
    # print(prompt)
    subject, body = generate_email(prompt)
    send_email('hackathon.hyw.2025@gmail.com', subject, body)
    
    # Send to the consultants
    prompt = build_candidate_email_prompt(company_name, contact_name, project_name, project_description, candidates_list)
    # print(prompt)
    subject, body = generate_email(prompt)
    send_email('hackathon.hyw.2025@gmail.com', subject, body)
    
    return jsonify({"message": "Emails sent successfully"}), 200


def build_company_email_prompt(
    company_name: str, contact_name: str, project_name: str, project_skills: List[str],
    candidates_per_requirements: List[List[Dict]], scheduling_link: str = "https://your-scheduling-link.com",
) -> str:
    candidates_text = ""
    for skill, candidates in zip(project_skills, candidates_per_requirements):
        candidates_text += f"The following consultants are assigned for the required skill: {skill}\n"
        candidates_text += "\n".join(
            f"- {c['profile_name']} ({c['seniority']} {c['role']}): {c['explanation']}"
            for c in candidates
        )

    prompt = f"""
        You are writing an email to the contact person at a company.

        Contact name: {contact_name}
        Company name: {company_name}
        Project name: {project_name}

        Context:
        The company has requested consultant support for a project. You are now presenting a curated shortlist of recommended candidates for their consideration. Each candidate was selected based on alignment with the project's specific skill requirements.
        
        Here are the selected candidates:
        {candidates_text}

        Write a professional email with:
        - A subject line on the first line only. Do **not** add “Subject:” or any label. Just write the subject text. (e.g. “Recommended Candidates for [Project Name]”)
        - A greeting using the contact name
        - A brief introduction referencing the project and purpose
        - A short, readable summary of the recommended candidates and their assigned role
        - A polite closing

        At the end of the email, include the following sentence:
        "Please schedule a short alignment interview using the following link: {scheduling_link}"

        Do not add any details not included above.
        """
    return prompt


def build_candidate_email_prompt(
    company_name: str, contact_name: str, project_name: str, project_description: str, 
    candidates_per_requirements: List[List[Dict]], scheduling_link="https://your-scheduling-link.com",
) -> str:
    lines = []
    for candidates in candidates_per_requirements:
        lines.extend(
            f"- {c['profile_name']} ({c['role']})"
            for c in candidates
        )
    candidates_text = "\n".join(lines)

    prompt = f"""
        You are a professional consultant coordinator writing an email to a group of consultants from your firm.

        Context:
        You are notifying selected consultants that they’ve been chosen to participate in a client project. The goal is to inform, motivate, and briefly outline the project.

        Client company: {company_name}
        Client contact person: {contact_name}
        Project name: {project_name}
        Project description: {project_description}

        The following candidates have been selected for this project:
        {candidates_text}

        Write a professional email with:
        - A subject line on the first line only. Do **not** add “Subject:” or any label. Just write the subject text. (e.g., “You’ve Been Assigned to {project_name}”)
        - A warm greeting to the consultants as a group
        - A brief paragraph announcing their selection and acknowledging their skills
        - A short summary of the project and the client
        - A motivational tone that communicates trust in their expertise
        - A friendly, professional closing with next steps or encouragement

        At the end of the email, include the following sentence:
        "Please schedule a short alignment interview using the following link: {scheduling_link}"

        Do not add any details not included above.
        """
    return prompt


def generate_email(prompt: str) -> Tuple[str, str]:
    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a professional business assistant. Write concise, polite, and clear emails for business communication.",
        input=prompt,
    )

    content = response.output_text
    subject, body = content.split("\n", 1)
    # print(content)
    # print(subject)
    # print(body)
    return subject, body


def send_email(receiver: str, subject: str, body: str):
    # Build the email
    msg = MIMEMultipart()
    msg['From'] = 'hackathon.hyw.2025@gmail.com'
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send it via Gmail SMTP
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login('hackathon.hyw.2025@gmail.com', 'xfpxvloxywksskhh')
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    app.run(debug=True, port=5001)
