import os
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import openai  # For example, using OpenAI's GPT
import networkx as nx
import matplotlib.pyplot as plt
import json

# Load environment variables from .env file
load_dotenv()

# Neo4j connection details
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = "Ecology"  # Specify the database name

# Set up OpenAI API (replace with your LLM API)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Connect to Neo4j
class Neo4jConnector:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
    
    def close(self):
        self.driver.close()
    
    def fetch_graph_data(self, query):
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            data = result.data()
            print(f"Query: {query}")
            print(f"Data: {data}")
            return data

# Fetch and structure the graph data
def get_graph_data(item_label_value):
    item_label_value = str(item_label_value)  # Ensure the input is a string
    query = f"""
    MATCH (n:Ecology_Entity)-[r]->(m:Publication)
    WHERE n.item_label_value = '{item_label_value}'
    RETURN n.item_label_value AS source_label_value, type(r) AS relationship, m.item_label_value AS target_label_value
    LIMIT 10;
    """
    data = Neo4jConnector(uri, username, password, database).fetch_graph_data(query)
    return data

# Format data for LLM
def format_graph_for_llm(graph_data):
    nodes = list(set([item["source_label_value"] for item in graph_data if item["source_label_value"]] + [item["target_label_value"] for item in graph_data if item["target_label_value"]]))
    edges = [{"source": item["source_label_value"], "target": item["target_label_value"], "relationship": item["relationship"]} for item in graph_data if item["source_label_value"] and item["target_label_value"]]
    return {
        "nodes": nodes,
        "edges": edges
    }

# Generate prompt for LLM
def create_prompt(graph_json):
    nodes = [node for node in graph_json['nodes'] if node]
    prompt = f"""
    Analyze the following graph structure and provide insights:

    Nodes:
    {', '.join(nodes)}

    Relationships:
    {json.dumps(graph_json['edges'], indent=2)}

    Based on this data, what patterns or insights can you observe? Suggest any key areas for further investigation and importance of the nodes.
    """
    return prompt

# Send the prompt to the LLM
def analyze_with_llm(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Replace with the model you are using
        messages=[
            {"role": "system", "content": "You are an ecology expert analyzing a graph structure."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response['choices'][0]['message']['content']

# Function to show the graph
def show_graph(graph_data):
    G = nx.DiGraph()
    for item in graph_data:
        if item["source_label_value"] and item["target_label_value"]:
            G.add_edge(item["source_label_value"], item["target_label_value"], label=item["relationship"])
    
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, font_weight="bold", arrows=True)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
    plt.title("Graph Visualization")
    plt.show()