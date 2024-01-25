from dotenv import load_dotenv
import client.open_ai_client as open_ai_clt
import client.linear_client as linear_clt
import logging

class OpenAILinearIntegrationClient:
    similarity_threshold = 0.81
    
    def __init__(self):
        self.open_ai_client = open_ai_clt.OpenAIClient()
        self.linear_client = linear_clt.LinearClient()
        self.linear_client.get_and_set_team_id()
        
    def handle_new_message(self, message):
        bug_or_feature_resp = self.open_ai_client.determine_bug_or_feature(message)
        issue_type, issue_name, issue_description = bug_or_feature_resp
        if issue_type == "neither": 
            return
        issues = self.linear_client.get_issues()
        issues_with_same_key = [issue for issue in issues if (len(issue["labelIds"]) > 0 and issue["labelIds"][0] == issue_type)]
        similar_issue_resp = self.open_ai_client.find_similar_issue(issues_with_same_key, bug_or_feature_resp, self.similarity_threshold)
        if similar_issue_resp is None: 
            self.linear_client.create_issue(issue_type, issue_name, issue_description)
        else: 
            self.linear_client.comment_on_issue(similar_issue_resp, bug_or_feature_resp[2])

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s: %(message)s", datefmt="%H:%M:%S")
logging.getLogger("httpx").disabled = True
load_dotenv()
open_ai_linear_integration_client = OpenAILinearIntegrationClient()
while True:
    user_input = input("Enter a conversation transcript or type 'generate {issue_type}' (bug fix, feature request, or neither) to generate one with ChatGPT (or 'exit' to exit): ")
    if user_input.startswith("generate"):
        test_transcript = open_ai_linear_integration_client.open_ai_client.generate_test_transcript(user_input.removeprefix("generate "))
        if test_transcript is not None: 
            user_input = test_transcript
    elif user_input == "exit":
        break
    open_ai_linear_integration_client.handle_new_message(user_input)