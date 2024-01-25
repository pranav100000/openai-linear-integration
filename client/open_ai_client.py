import os
import numpy as np
from openai import OpenAI
from numpy.linalg import norm
import json
import retry
import logging

class OpenAIClient:
    MODEL = "gpt-4"
    EMBEDDING_MODEL = "text-embedding-ada-002"
    DETERMINE_BUG_OR_FEATURE_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "determine_bug_or_feature_or_neither",
                "description": "Given a conversation transcript between a customer and a customer support agent, determine the issue type and come up with a name and description for the issue.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_type": {
                            "type": "string",
                            "enum": ["bug fix", "feature request", "neither"],
                            "description": "The issue type. A bug fix is when a customer is experiencing an issue with the product. A feature request is when a customer is requesting a new feature. Neither is when the customer is not experiencing an issue and is not requesting a new feature"
                        },
                        "issue_name": {
                            "type": "string",
                            "description": "The name of the issue in 10 words or less."
                        },
                        "issue_description": {
                            "type": "string",
                            "description": "The description of the issue in 100 words or less."
                        }
                    },
                    "required": ["issue_type", "issue_name", "issue_description"]
                }
            }
        }
    ]
    
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
        
    @retry.retry(tries=3, delay=2)
    def determine_bug_or_feature(self, conversation_transcript):
        logging.debug("Determining bug, feature, or neither:")
        response = self.client.chat.completions.create(
            model=self.MODEL,
            n=1,
            temperature=0.1,
            messages=[{"role": "user", "content": conversation_transcript}],
            tools=self.DETERMINE_BUG_OR_FEATURE_TOOLS,
            tool_choice={"type": "function", "function": {"name": "determine_bug_or_feature_or_neither"}}
        )
        json_resp = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        if json_resp is None: 
            raise Exception("determine_bug_or_feature response is None")
        logging.info(f"Issue type: {json_resp["issue_type"]}")
        logging.debug("determine_bug_or_feature response: " + str(json_resp))
        return json_resp["issue_type"], json_resp["issue_name"], json_resp["issue_description"]
        
    def find_similar_issue(self, issues, issue, similarity_threshold):
        logging.info(f"Finding similar issue for issue with name: \"{issue[1]}\", and description: \"{issue[2]}\"")
        if len(issues) == 0: 
            return
        query_name_embedding, query_description_embedding = self._get_embedding(issue[1]), self._get_embedding(issue[2])
        embeddings = []
        for issue in issues:
            name_embedding, description_embedding = self._get_embedding(issue["title"]), self._get_embedding(issue["description"])
            similarity = self._find_similarity(name_embedding, query_name_embedding, description_embedding, query_description_embedding)
            if similarity > similarity_threshold: 
                embeddings.append((issue["id"], similarity)) 
        embeddings = sorted(embeddings, key=lambda x: x[1], reverse=True)
        if len(embeddings) > 0: 
            logging.info(f"Found similar issue. Creating comment on issue with ID: {embeddings[0][0]}")
            logging.debug(f"Most similar issue's ID is: {embeddings[0][0]} with similarity: {embeddings[0][1]}")
            return embeddings[0][0]
        logging.info("No similar issue found. Creating new issue.")
    
    @retry.retry(tries=3, delay=2)
    def generate_test_transcript(self, issue_type):
        logging.info(f"Generating test transcript for issue type: {issue_type}")
        if issue_type not in ["bug fix", "feature request", "neither"]: 
            logging.error(f"Invalid issue type: {issue_type}")
            return
        response = self.client.chat.completions.create(
            model=self.MODEL,
            n=1,
            messages=[
                {"role": "system", "content": "You are an assistant. Based on a prompt, create a conversation transcript. If the prompt is 'bug fix', create a conversation in which the customer is discussing a bug they need fixed. If the prompt is 'feature request', create a conversation in which the customer is requesting a new feature. If the prompt is 'neither', create a conversation in which the customer is not experiencing an issue and is not requesting a new feature."},
                {"role": "user", "content": issue_type}
            ]
        )
        logging.info(f"Generated test transcript:\n\n{response.choices[0].message.content}")
        return response.choices[0].message.content
    
    @retry.retry(tries=3, delay=2)
    def _get_embedding(self, text):
        return self.client.embeddings.create(input=text, model=self.EMBEDDING_MODEL).data[0].embedding
    
    def _find_similarity(self, name_embedding1, name_embedding2, description_embedding1, description_embedding2):
        return self._get_dot_product(name_embedding1, name_embedding2) * self._get_dot_product(description_embedding1, description_embedding2)
    
    def _get_dot_product(self, embedding1, embedding2):
        return np.dot(embedding1, embedding2)/(norm(embedding1)*norm(embedding2))