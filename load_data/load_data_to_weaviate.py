from typing import List
import json
import weaviate
from weaviate.util import generate_uuid5
from weaviate.embedded import EmbeddedOptions
import time
import os
from dotenv import load_dotenv

def get_article_text_objects(file_path):
    
    with open(file_path, mode='r') as file:
        # Load the JSON data from the file
        data = json.load(file)

    return data

def word_splitter(source_text: str) -> List[str]:
    import re
    source_text = re.sub("\s+", " ", source_text)  # Replace multiple whitespces
    return re.split("\s", source_text)  # Split by single whitespace

def get_chunks_fixed_size_with_overlap(text: str, chunk_size: int, overlap_fraction: float) -> List[str]:
    text_words = word_splitter(text)
    overlap_int = int(chunk_size * overlap_fraction)
    chunks = []
    for i in range(0, len(text_words), chunk_size):
        chunk = " ".join(text_words[max(i - overlap_int, 0): i + chunk_size])
        chunks.append(chunk)
    return chunks

def get_chunks_by_paragraph(source_text: str) -> List[str]:
    return source_text.split("\n\n")

def get_chunks_by_paragraph_and_min_length(source_text: str) -> List[str]:
    chunks = source_text.split("\n==")

    # Chunking
    new_chunks = list()
    chunk_buffer = ""
    min_length = 25

    for chunk in chunks:
        new_buffer = chunk_buffer + chunk  # Create new buffer
        new_buffer_words = new_buffer.split(" ")  # Split into words
        if len(new_buffer_words) < min_length:  # Check whether buffer length too small
            chunk_buffer = new_buffer  # Carry over to the next chunk
        else:
            new_chunks.append(new_buffer)  # Add to chunks
            chunk_buffer = ""

    if len(chunk_buffer) > 0:
        new_chunks.append(chunk_buffer)  # Add last chunk, if necessary
    return new_chunks

def build_chunk_objs(book_text_obj, chunks):
    chunk_objs = list()
    for i, c in enumerate(chunks):
        chunk_obj = {
            "url": book_text_obj["url"],
            "title": book_text_obj["title"],
            "article": book_text_obj["article"],
            "chunk": c,
            "chunk_index": i
        }
        chunk_objs.append(chunk_obj)
    return chunk_objs

# Load environment variables from .env file
load_dotenv()

WEAVIATE_CLUSTER_URL = os.getenv('WEAVIATE_CLUSTER_URL')
WEAVIATE_API_KEY = os.getenv('WEAVIATE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

#Load the articles
article_text_objs = get_article_text_objects('./web_scraping/scraped_autism_articles.json')

# Get multiple sets of chunks - according to chunking strategy
chunk_obj_sets = dict()
for article_text_obj in article_text_objs:
    text = article_text_obj["article"]  # Get the object's text body

    # Loop through chunking strategies:
    for strategy_name, chunks in [
        ["fixed_size_25", get_chunks_fixed_size_with_overlap(text, 25, 0.2)]
    ]:
        chunk_objs = build_chunk_objs(article_text_obj, chunks)

        if strategy_name not in chunk_obj_sets.keys():
            chunk_obj_sets[strategy_name] = list()

        chunk_obj_sets[strategy_name] += chunk_objs

# Connect to Weaviate cloud and set up embedding
client = weaviate.connect_to_wcs(
    cluster_url=WEAVIATE_CLUSTER_URL,  # Replace with your Weaviate Cloud URL
    auth_credentials=weaviate.auth.AuthApiKey(WEAVIATE_API_KEY),  # Replace with your Weaviate Cloud key
    headers={'X-OpenAI-Api-key': OPENAI_API_KEY}  # Replace with your OpenAI API key
)
client = weaviate.Client(
    embedded_options=EmbeddedOptions(),
    additional_headers = {
        "X-OpenAI-Api-Key": OPENAI_API_KEY  # Replace with your inference API key
    }
)

# Create class object, make sure to specify model
class_obj = {
    "class": "Article",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {},
        "generative-openai": {"model": "gpt-3.5-turbo-16k"}  # Ensure the `generative-openai` module is used for generative queries
    },
    "properties": [
        {
            "name": "chunk",
            "dataType": ["text"],
        },
        {
            "name": "url",
            "dataType": ["text"],
        },
        {
            "name": "title",
            "dataType": ["text"],
        },
        {
            "name": "article",
            "dataType": ["text"],
        },
        {
            "name": "chunking_strategy",
            "dataType": ["text"],
            "tokenization": "field",
        }
    ]
}

# Clear out all the schemas since you're only working with Article
client.schema.delete_all()

# Load data into db
print("Begin database load")
client.schema.create_class(class_obj)
with client.batch as batch:
    for chunking_strategy, chunk_objects in chunk_obj_sets.items():
        for chunk_obj in chunk_objects:
            chunk_obj["chunking_strategy"] = chunking_strategy
            time.sleep(0.25) # Small sleep for OpenAI API so robot overlords will look upon me kindly
            batch.add_data_object(
                data_object=chunk_obj,
                class_name="Article",
                uuid=generate_uuid5(chunk_obj)
            )
print("Database load complete.")

# Print out counts to make sure what you loaded makes sense
print("Total count:")
print(client.query.aggregate("Article").with_meta_count().do())  # Get a total count
for chunking_strategy in chunk_obj_sets.keys():
    where_filter = {
        "path": ["chunking_strategy"],
        "operator": "Equal",
        "valueText": chunking_strategy
    }
    print(f"Object count for {chunking_strategy}")
    strategy_count = (
        client.query.aggregate("Article")
        .with_where(where_filter)
        .with_meta_count().do()
    )
    print(strategy_count)  # Get a count for each strategy (in this case, just one strategy of 25)
