from typing import Annotated, Any, Dict, List, Tuple, TypedDict
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import operator
from datetime import datetime
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create and setup database
def setup_database():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        country TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        product TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')
    
    # Sample data
    sample_customers = [
        (1, 'John Doe', 'john@example.com', 'USA'),
        (2, 'Jane Smith', 'jane@example.com', 'Canada'),
    ]
    
    sample_orders = [
        (1, 1, 'Laptop', 1200.00, '2024-01-15'),
        (2, 2, 'Monitor', 299.99, '2024-01-20'),
    ]
    
    cursor.executemany('INSERT OR REPLACE INTO customers VALUES (?,?,?,?)', sample_customers)
    cursor.executemany('INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?)', sample_orders)
    
    conn.commit()
    conn.close()

# Define state structure
class State(TypedDict):
    messages: List[Any]
    sql_query: str
    results: List[Tuple]
    current_step: str
    error: str

# SQL execution tool
def execute_sql(query: str) -> List[Tuple]:
    try:
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        raise Exception(f"SQL Error: {str(e)}")

# Node for SQL query generation
def generate_sql(state: State) -> Dict:
    # Get the last message
    question = state["messages"][-1].content
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a SQL expert. Generate a valid SQLite query based on the user's question.
        Available tables:
        - customers (customer_id, name, email, country)
        - orders (order_id, customer_id, product, amount, date)
        
        Generate only the SQL query without any explanation."""),
        ("human", question)
    ])
    
    # Initialize LLM
    model = ChatOpenAI(temperature=0)
    
    # Generate SQL query
    messages = prompt.format_messages()
    response = model.invoke(messages)
    
    return {"sql_query": response.content}

# Node for executing SQL query
def execute_query(state: State) -> Dict:
    try:
        results = execute_sql(state["sql_query"])
        return {"results": results, "error": ""}
    except Exception as e:
        return {"results": [], "error": str(e)}

# Node for generating response
def generate_response(state: State) -> Dict[str, List]:
    if state["error"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Explain the SQL error to the user in a friendly way."),
            ("human", f"SQL Error: {state['error']}")
        ])
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant. Format and explain the SQL results to the user.
            Include both the SQL query used and the results in your explanation."""),
            ("human", f"""SQL Query: {state['sql_query']}
            Results: {state['results']}""")
        ])
    
    model = ChatOpenAI()
    messages = prompt.format_messages()
    response = model.invoke(messages)
    
    return {"messages": [*state["messages"], AIMessage(content=response.content)]}

# Define workflow
def create_workflow() -> Any:  # Changed return type to Any
    # Create workflow graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_query", execute_query)
    workflow.add_node("generate_response", generate_response)
    
    # Define edges
    workflow.add_edge("generate_sql", "execute_query")
    workflow.add_edge("execute_query", "generate_response")
    
    # Set entry point
    workflow.set_entry_point("generate_sql")
    
    # Set finish point
    workflow.set_finish_point("generate_response")
    
    # Compile workflow
    return workflow.compile()

def main():
    try:
        # Setup database
        setup_database()
        
        # Create workflow
        app = create_workflow()
        
        # Example queries
        # test_queries = [
        #     "Show all customers from USA",
        #     "What is the total amount spent by each customer?",
        #     "List all orders with customer names"
        # ]
        while True:
            query= input("Enter the query (or type exit to quit )")
            if query.lower()=="exit":
                print("Exiting ... ")
                break

        
        # Process queries
            
            try:
                    print(f"\nProcessing query: {query}")
                    
                    # Initialize state
                    state = {
                        "messages": [HumanMessage(content=query)],
                        "sql_query": "",
                        "results": [],
                        "current_step": "start",
                        "error": ""
                    }
                    
                    # Run workflow
                    final_state = app.invoke(state)
                    print("\nGenerated query:")
                    print(final_state["sql_query"])
                    
                    # Print results
                    print("\nFinal Response:")
                    print(final_state["messages"][-1].content)
                    print("\n" + "="*50)
            except Exception as e:
                    print(f"Error processing query: {str(e)}")
                    print("\n" + "="*50)
                    continue
                    
    except Exception as e:
        print(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
