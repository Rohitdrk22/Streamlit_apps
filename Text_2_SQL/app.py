from dotenv import load_dotenv
load_dotenv()  # Load all the environment variables

import streamlit as st
import os
import pandas as pd
import atexit
import mysql.connector
import google.generativeai as genai

# Configure Genai Key
genai.configure(api_key=os.getenv("Google_api_key"))

# Establish a connection to MySQL Server
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123",
    database="information_schema"  # Using information_schema to fetch schema and table names
)
mycursor = mydb.cursor()


# Function to fetch schema names from information_schema
def get_schema_names():
    mycursor.execute("SELECT schema_name FROM schemata WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema')")
    return [row[0] for row in mycursor.fetchall()]

# Function to fetch table names for a given schema
def get_table_names(schema):
    mycursor.execute(f"USE {schema}")
    mycursor.execute("SHOW TABLES")
    return [table[0] for table in mycursor.fetchall()]

# Function To Load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function To retrieve query from the database
def read_sql_query(sql):
    try:
        mycursor.execute(sql)
        columns = [desc[0] for desc in mycursor.description]
        rows = mycursor.fetchall()
        return columns, rows
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

# Function to fetch column names for a given table
def get_column_names(schema, table):
    mycursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'")
    return [column[0] for column in mycursor.fetchall()]

def get_prompt(schema, table):
    columns = get_column_names(schema, table)
    # Assuming the first column is the primary key
    primary_key = columns[0] if columns else 'id'
    # Assuming the second column is the name
    name = columns[1] if len(columns) > 1 else 'name'
    # Assuming the third column is the class
    class_column = columns[2] if len(columns) > 2 else 'class'

    prompt = f"""
    You are an expert in converting English questions to SQL query!
    The MySQL database has the name {schema} and the table {table} has the following columns - {', '.join(columns)} 
    \n\nFor example,
    \nExample 1 - How many entries of records are present?, 
    the SQL command will be something like this SELECT COUNT(*) FROM {table};
    \nExample 2 - Tell me all the students studying in Data Science class?, 
    the SQL command will be something like this SELECT * FROM {table} 
    where {class_column}='Data Science'; 
    \nExample 3 - What is the average score of students in each class?, 
    the SQL command will be something like this SELECT {class_column}, AVG(SCORE) FROM {table} GROUP BY {class_column};
    \nExample 4 - What is the highest score in each class?, 
    the SQL command will be something like this SELECT {class_column}, MAX(SCORE) OVER (PARTITION BY {class_column}) FROM {table};
    \nExample 5 - How many students are in each class and section?, 
    the SQL command will be something like this SELECT {class_column}, SECTION, COUNT(*) FROM {table} GROUP BY {class_column}, SECTION HAVING COUNT(*) > 1;
    \nExample 6 - What is the name of the student with the highest score in the 'Data Science' class?, 
    the SQL command will be something like this SELECT {name} FROM {table} WHERE SCORE = (SELECT MAX(SCORE) FROM {table} WHERE {class_column} = 'Data Science');
    \nExample 7 - What is the name of the student with the highest score in each class?, 
    the SQL command will be something like this WITH MAX_SCORES AS (SELECT {class_column}, MAX(SCORE) AS MAX_SCORE FROM {table} GROUP BY {class_column}) SELECT t.{name}, t.{class_column} FROM {table} t INNER JOIN MAX_SCORES ms ON t.{class_column} = ms.{class_column} AND t.SCORE = ms.MAX_SCORE;
    \nExample 8 - What are the names of the students who are studying in the same class as 'John'?, 
    the SQL command will be something like this SELECT t1.{name} FROM {table} t1 INNER JOIN {table} t2 ON t1.{class_column} = t2.{class_column} WHERE t2.{name} = 'John';
    \nExample 9 - What are the names of the students who are not studying in the same class as 'John'?, 
    the SQL command will be something like this SELECT t1.{name} FROM {table} t1 LEFT JOIN {table} t2 ON t1.{class_column} = t2.{class_column} AND t2.{name} = 'John' WHERE t2.{name} IS NULL;
    \nExample 10 - What are the names of the students who are studying either in the same class as 'John' or in the class 'Data Science'?, 
    the SQL command will be something like this SELECT t1.{name} FROM {table} t1 LEFT JOIN {table} t2 ON t1.{class_column} = t2.{class_column} AND t2.{name} = 'John' WHERE t2.{name} IS NOT NULL OR t1.{class_column} = 'Data Science';
    \nExample 11 - What are the names of all the students along with the class of 'John' if they are studying in the same class?, 
    the SQL command will be something like this SELECT t1.{name}, t2.{class_column} FROM {table} t1 FULL JOIN {table} t2 ON t1.{class_column} = t2.{class_column} AND t2.{name} = 'John';
    \nalso the sql code should not have ``` in beginning or end and sql word in output
    """
    return [prompt]




# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    with open("student.sql", "wb") as f:  # Assuming the uploaded file is a SQL dump
        f.write(uploaded_file.getbuffer())

# Delete MySQL database file when Streamlit server is closed
def delete_db_file():
    # Add code to delete MySQL database file if necessary
    pass


# Function to display radio buttons for table selection
def select_table_radio(table_names):
    selected_table = st.selectbox("Select Table", table_names, format_func=lambda x: 'Select a Table' if x == '' else x,index=None)
    return selected_table





# Set page config with the icon URL
st.set_page_config(page_title="Text 2 SQL", page_icon='https://www.icone-png.com/png/53/53389.png')

st.header("\U0001F4BB Text to SQL- Retrieve SQL Data")

# Option selection: select schema or upload file
option = st.radio("Select Option", ["Select Schema", "Upload File"], index=None)


if option == "Upload File":
    # Upload file section
    uploaded_file = st.file_uploader("Upload a SQL Dump File", type="sql")

    if uploaded_file:
        save_uploaded_file(uploaded_file)
        st.success("File uploaded successfully.")
        script = uploaded_file.getvalue().decode('utf-8')  # Read the uploaded file content
        lines = script.split('\n')

        # Extract table names
        table_names = set()
        for line in lines:
            line = line.strip()
            if line.startswith("CREATE TABLE"):
                table_name = line.split("`")[1]
                table_names.add(table_name)

        # Display radio buttons for table selection
        selected_table = st.radio("Select Table", sorted(list(table_names)), index=None)        
        
        # Fetch schema name for database connection
        selected_schema = "information_schema"  # Assuming default schema for now
        

elif option == "Select Schema":
    # Schema selection dropdown
    schema_names = get_schema_names()
    selected_schema = st.selectbox("Select Schema", schema_names, format_func=lambda x: 'Select a Schema' if x == '' else x, index=None)

    if selected_schema and selected_schema != "Select a Schema":
        table_names = get_table_names(selected_schema)
        selected_table = select_table_radio(table_names)

# Delete MySQL database file when Streamlit server is closed
atexit.register(delete_db_file)

question = st.text_input("Input: ", key="input")
submit = st.button("Ask the question")

if submit and selected_table and selected_schema:
    prompt = get_prompt(selected_schema, selected_table)
    generated_sql = get_gemini_response(question, prompt)
    print(f"Generated SQL: {generated_sql}")  # Print the generated SQL query

    # Execute the generated SQL query
    columns, response_rows = read_sql_query(generated_sql)

    # Display the generated SQL query
    st.subheader("Question:")
    st.write(question)

    st.subheader("Generated SQL Query:")
    st.write(generated_sql)

    # Display the Response with column headers in table format
    if columns is not None and response_rows is not None:
        st.subheader("The Response is:")
        st.table(pd.DataFrame(response_rows, columns=columns))

