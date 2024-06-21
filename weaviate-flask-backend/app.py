from flask import Flask, request, jsonify
from flask_cors import CORS
import weaviate
import json
from weaviate.embedded import EmbeddedOptions
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

WEAVIATE_CLUSTER_URL = os.getenv('WEAVIATE_CLUSTER_URL')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app)  # Enable CORS

# Connect to weaviate cloud
client = weaviate.Client(
    url=WEAVIATE_CLUSTER_URL,
    auth_client_secret=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY),
    additional_headers = {
        "X-OpenAI-Api-Key": OPENAI_API_KEY
    }
)
client = weaviate.Client(
    embedded_options=EmbeddedOptions(),
    additional_headers = {
        "X-OpenAI-Api-Key": OPENAI_API_KEY  # Replace with your inference API key
    }
)

@app.route('/query', methods=['POST'])
def query_weaviate():
    request_data = request.json
    search_string = request_data.get('question')
    
    generateTask = "Please provide a very brief summary of the following text: {chunk}"

    result = (
        client.query
        .get("Article", ["url", "title", "chunk", "chunking_strategy"])
        .with_near_text({
            "concepts": [search_string]
        })
        .with_limit(2)
        .with_generate(grouped_task=generateTask)
    ).do()

    # Instantiate a dictionary for the API output
    api_output = dict()
    api_output["summary"] = result["data"]["Get"]["Article"][0]["_additional"]["generate"]["groupedResult"]

    # Extract articles from JSON data
    articles = result['data']['Get']['Article']

    # Dynamically add the articles to the API payload, ensuring no duplicates
    seen_urls = set()
    api_output["articles"] = []
    for article in articles:
        if article["url"] not in seen_urls:
            api_output["articles"].append({"title": article["title"], "url": article["url"]})
            seen_urls.add(article["url"])

    return jsonify(api_output)

if __name__ == '__main__':
    app.run(debug=True)
