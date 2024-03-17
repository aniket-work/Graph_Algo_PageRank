import networkx as nx
from pyvis.network import Network
import webbrowser
import random
from neo4j import GraphDatabase

# Number of customers and products
num_customers = 20
num_products = 30

# Generate random customer and product IDs
customers = [f'Customer{i}' for i in range(1, num_customers + 1)]
products = [f'Product{i}' for i in range(1, num_products + 1)]

# Create a directed graph
G = nx.DiGraph()

# Add nodes representing customers and products
G.add_nodes_from(customers, bipartite=0)  # Customers are type 0
G.add_nodes_from(products, bipartite=1)   # Products are type 1

# Generate random interactions (edges)
for customer in customers:
    # Choose a random number of interactions for each customer
    num_interactions = random.randint(1, 5)
    # Randomly select products for interactions
    for _ in range(num_interactions):
        product = random.choice(products)
        G.add_edge(customer, product)

# Calculate node size based on out-degree for customers and influence factor for products
node_sizes = {}
total_out_degree_dict = {}  # Store the total out-degree for each product
for node in G.nodes:
    if node.startswith('Customer'):
        node_sizes[node] = G.out_degree(node) * 5  # Increase the size for better visualization
    else:
        customers_connected = [neighbor for neighbor in G.predecessors(node) if neighbor.startswith('Customer')]
        total_out_degree = sum(G.out_degree[c] for c in customers_connected)
        total_out_degree_dict[node] = total_out_degree
        node_sizes[node] = total_out_degree

# Create a pyvis network
network = Network(notebook=False, heading='Product Recommendation Graph')

# Add nodes and edges
for node in G.nodes:
    if node.startswith('Customer'):
        node_color = '#ff5733'  # Orange color for customers
        tooltip = f'Name: {node}\nOUT: {G.out_degree(node)}'
    else:
        node_color = '#1f77b4'  # Blue color for products
        customers_connected = [neighbor for neighbor in G.predecessors(node) if neighbor.startswith('Customer')]
        total_out_degree = sum(G.out_degree[c] for c in customers_connected)
        total_in_degree = G.in_degree(node)
        tooltip = f'Name: {node}\nInfluence Factor: {total_out_degree} \nIN: {total_in_degree} '
    network.add_node(node, color=node_color, size=node_sizes[node], title=tooltip)  # Add node with tooltip

for edge in G.edges:
    network.add_edge(edge[0], edge[1], title='Purchase', arrows='to')  # Add directed edge with arrow

# Configure network options
network_options = {
    "physics": {"enabled": True},  # Disable physics to prevent nodes from repositioning after dragging
    "edges": {
        "arrowStrikethrough": True,  # Make arrow lighter
        "arrowScaleFactor": 0.5,      # Reduce the size of the arrow
        "arrows": {
            "to": {"enabled": True, "type": "arrow"}
        }
    }
}

# Set network options
network.options = network_options

# Save the graph to an HTML file in the current directory
html_file = 'product_recommendation.html'
network.save_graph(html_file)
print(f"Graph exported to '{html_file}'")

# Open the HTML file in a web browser
webbrowser.open_new_tab(html_file)

# Function to load data into Neo4j
def load_data(tx):
    for node in G.nodes:
        if node.startswith('Customer'):
            tx.run("MERGE (c:Customer {id: $id, OUT: $out_degree})",
                   id=node, out_degree=G.out_degree(node))
        else:
            customers_connected = [neighbor for neighbor in G.predecessors(node) if neighbor.startswith('Customer')]
            total_out_degree = sum(G.out_degree[c] for c in customers_connected)
            total_in_degree = G.in_degree(node)
            tx.run("MERGE (p:Product {id: $id, InfluenceFactor: $influence, IN: $in_degree})",
                   id=node, influence=total_out_degree, in_degree=total_in_degree)

    for edge in G.edges:
        tx.run("MATCH (c:Customer {id: $cid}) "
               "MATCH (p:Product {id: $pid}) "
               "MERGE (c)-[:PURCHASED]->(p)", cid=edge[0], pid=edge[1])

    # Create a named graph in Neo4j
    tx.run("CALL gds.graph.project('aniketGraph6', '*', '*')")

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "abcd1234"

# Connect to Neo4j and load data
driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    session.write_transaction(load_data)

# Close the Neo4j driver
driver.close()
