from neo4j import GraphDatabase

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "abcd1234"

# Function to run PageRank algorithm
def run_page_rank(tx):
    query = (
        "CALL gds.pageRank.stream('aniketGraph6', "
        "{maxIterations: 100000, dampingFactor: 0.95}) "
        "YIELD nodeId, score "
        "RETURN gds.util.asNode(nodeId).id AS node, score "
        "ORDER BY score DESC"
    )
    result = tx.run(query)
    for record in result:
        print(f"{record['node']}: {record['score']}")

# Connect to Neo4j and run PageRank algorithm
driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session(database="neo4j") as session:
    session.read_transaction(run_page_rank)

# Close the Neo4j driver
driver.close()
