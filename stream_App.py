import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx
from Graph_Embeding import get_graph_data, format_graph_for_llm, create_prompt, analyze_with_llm
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Neo4j connection details
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = "Ecology"  # Specify the database name

# Streamlit app
st.title("EcoSci Recommender")

entity_name = st.text_input(" what is the research topic:")

if st.button("Analyze"):
    # Fetch graph data
    graph_data = get_graph_data(entity_name)    
    if graph_data:
        st.subheader("Knowledge Gaph ")
        fig, ax = plt.subplots()
        G = nx.DiGraph()
        for item in graph_data:
            if item["source_label_value"] is not None and item["target_label_value"] is not None:
                source_label = item["source_label_value"]
                target_label = ' '.join(item["target_label_value"].split()[:5])  # Show only the first two words
                G.add_edge(source_label, target_label, label=item["relationship"])
        
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=False, node_size=3000, node_color="white", font_size=1, arrows=False, ax=ax)
        #edge_labels = nx.get_edge_attributes(G, 'label')
        #nx.draw_networkx_edge_labels(G, pos, edge_labels= "n", font_color='blue', ax=ax)
        
        # Adjust font size for node labels
        for p in pos:  # pos is a dictionary with node positions
            pos[p][1] += 0  # Adjust the y-position to avoid overlap
        nx.draw_networkx_labels(G, pos, font_size=6, font_color='black', ax=ax)
        
        st.pyplot(fig)

        st.subheader("Research Insights")
        graph_json = format_graph_for_llm(graph_data)
        prompt = create_prompt(graph_json)
        insights = analyze_with_llm(prompt)
        st.write(insights)
    else:
        st.write(f"No data found for entity '{entity_name}'.")