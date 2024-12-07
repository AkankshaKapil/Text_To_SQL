# SQL Query Assistant with Workflow Automation

This project is an **SQL Query Assistant** that automates the process of generating, executing, and explaining SQL queries using a combination of a **Graph-based Workflow** and a **Large Language Model (LLM)**. It leverages `langgraph` for state management and OpenAI's GPT for intelligent query generation and response formatting.

## Features

- **Dynamic SQL Query Generation:** Converts user questions into valid SQL queries.
- **SQL Execution:** Executes the generated queries on a SQLite database.
- **Intelligent Responses:** Formats and explains query results or errors in a user-friendly way.
- **Workflow Automation:** Uses a graph-based state machine to orchestrate the process.

## Tech Stack

- **Python**
- **SQLite** for database storage.
- **LangChain** and **OpenAI GPT** for natural language processing.
- **langgraph** for graph-based workflow management.
- **dotenv** for environment variable management.

## How It Works

1. **Input:** The user enters a natural language query.
2. **Workflow:**
   - **Node 1:** `generate_sql` - Transforms the query into SQL using the LLM.
   - **Node 2:** `execute_query` - Executes the SQL query on a SQLite database.
   - **Node 3:** `generate_response` - Formats the results (or errors) into a readable response.
3. **Output:** The assistant displays the SQL query, results, or error explanation.

## Prerequisites

1. Python 3.10 or higher.
2. Install required libraries: pip install -r requirements.txt
