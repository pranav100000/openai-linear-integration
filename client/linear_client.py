import os
import requests
import retry
import logging

class LinearClient:
    LINEAR_GRAPH_QL_URL = "https://api.linear.app/graphql"
    LABEL_TO_KEY = {
        "bug fix": "6b6c975e-417c-44c5-8a9a-4066557a479d",
        "feature request": "1e5e84a6-ee0b-4e0f-b9a1-38c073160116",
    }
    
    def __init__(self) -> None:
        self.api_key = os.getenv("LINEAR_API_KEY")
    
    @retry.retry(tries=3, delay=2)
    def get_and_set_team_id(self):
        logging.debug("Getting and setting team id")
        headers = {"Authorization": f'{self.api_key}', "Content-Type": 'application/json'}
        data = {
            "query": "query Teams { teams { nodes { id name } }}"
        }
        r = requests.post(self.LINEAR_GRAPH_QL_URL, headers=headers, json=data)
        if not r.ok: 
            raise Exception(r.text)
        resp_json = r.json()
        logging.debug(f"team_id: {resp_json["data"]["teams"]["nodes"][0]["id"]}")
        self.team_id = resp_json["data"]["teams"]["nodes"][0]["id"]
    
    @retry.retry(tries=3, delay=2)
    def create_issue(self, type, title, description):
        if type not in ["bug fix", "feature request"]: 
            return
        logging.info(f"Creating issue with type: {type}, title: {title}, and description: {description}")
        headers = {"Authorization": f'{self.api_key}', "Content-Type": 'application/json'}
        data = {
            "query": f"""
                mutation IssueCreate {{
                    issueCreate(input: {{
                        title: "{title}", 
                        description: "{description}", 
                        teamId: "{self.team_id}"
                        labelIds: ["{self.LABEL_TO_KEY[type]}"]
                    }})
                    {{ 
                        success 
                        issue {{ 
                            id 
                            title 
                        }}
                    }}
                }}
            """
        }
        r = requests.post(self.LINEAR_GRAPH_QL_URL, headers=headers, json=data)
        if not r.ok: 
            raise Exception(r.text)
        resp_json = r.json()
        logging.debug(f"ID of created issue: {resp_json["data"]["issueCreate"]["issue"]["id"]}")
    
    @retry.retry(tries=3, delay=2)
    def comment_on_issue(self, issue_id, comment):
        logging.info(f"Commenting: \"{comment}\" on issue with id: {issue_id}")
        headers = {"Authorization": f'{self.api_key}', "Content-Type": 'application/json'}
        data = {
            "query": f"""
                mutation CommentCreate {{
                    commentCreate(input: {{
                        issueId: "{issue_id}", 
                        body: "{comment}"
                    }})
                    {{ 
                        success 
                        comment {{ 
                            id 
                            body 
                        }}
                    }}
                }}
            """
        }
        r = requests.post(self.LINEAR_GRAPH_QL_URL, headers=headers, json=data)
        if not r.ok: 
            raise Exception(r.text)
        resp_json = r.json()
        logging.debug(f"ID of created comment: {resp_json["data"]["commentCreate"]["comment"]["id"]}")
    
    @retry.retry(tries=3, delay=2)
    def get_issues(self):
        logging.info(f"Getting issues for team with ID: {self.team_id}")
        headers = {"Authorization": f'{self.api_key}', "Content-Type": 'application/json'}
        data = {
            "query": f"""
                query Team {{ 
                    team(id: "{self.team_id}") {{ 
                        id 
                        name 
                        issues 
                        {{ 
                            nodes {{ 
                                id 
                                title 
                                description 
                                labelIds
                            }}
                        }}
                    }}
                }}
            """
        }
        r = requests.post(self.LINEAR_GRAPH_QL_URL, headers=headers, json=data)
        if not r.ok: 
            raise Exception(r.text)
        resp_json = r.json()
        key_to_label = {v: k for k, v in self.LABEL_TO_KEY.items()}
        for node in resp_json["data"]["team"]["issues"]["nodes"]:
            node["labelIds"] = [key_to_label[label_id] for label_id in node["labelIds"]]
        issues = resp_json["data"]["team"]["issues"]["nodes"]
        logging.debug(f"Issues: {issues}")
        return issues