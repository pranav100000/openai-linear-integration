from dotenv import load_dotenv
import client.open_ai_client as open_ai_client
import client.linear_client as linear_client
import logging

class OpenAILinearIntegrationClient:
    similarity_threshold = 0.81
    
    def __init__(self):
        self.open_ai_client = open_ai_client.OpenAIClient()
        self.linear_client = linear_client.LinearClient()
        self.linear_client.get_and_set_team_id()
        
    def handle_new_message(self, message):
        bug_or_feature_resp = self.open_ai_client.determine_bug_or_feature(message)
        issue_type, issue_name, issue_description = bug_or_feature_resp
        if issue_type == "neither": return
        
        issues = self.linear_client.get_issues()
        issues_with_same_key = [issue for issue in issues if (len(issue["labelIds"]) > 0 and issue["labelIds"][0] == issue_type)]
        similar_issue_resp = self.open_ai_client.find_similar_issue(issues_with_same_key, bug_or_feature_resp, self.similarity_threshold)

        if similar_issue_resp is None: self.linear_client.create_issue(issue_type, issue_name, issue_description)
        else: self.linear_client.comment_on_issue(similar_issue_resp, bug_or_feature_resp[2])

logging.basicConfig(level=logging.INFO)
load_dotenv()
open_ai_linear_integration_client = OpenAILinearIntegrationClient()
while True:
    user_input = input("Enter a conversation transcript (or 'exit' to exit): ")
    if user_input == "exit":
        break
    open_ai_linear_integration_client.handle_new_message(user_input)