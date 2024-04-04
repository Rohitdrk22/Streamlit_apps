import mysql.connector
import streamlit as st
import pandas as pd
import io
import subprocess
import time

# Function to check if MySQL is installed
def is_mysql_installed():
    try:
        subprocess.check_call(["mysql", "--version"])
        return True
    except subprocess.CalledProcessError:
        return False
    
# Function to display a warning message for a few seconds
def show_warning_message(message, duration=5):
    st.warning(message)
    time.sleep(duration)
    st.empty()


# Function to authenticate user credentials with MySQL database
def authenticate(username, password):
    # Check if MySQL is installed
    if not is_mysql_installed():
        st.warning("MySQL should be installed in order to use this Streamlit MySQL app.")
        return False, None

    try:
        # Establish connection to MySQL Server
        mydb = mysql.connector.connect(
            host="localhost",
            user=username,
            password=password
        )
        # Return the connection object along with authentication status
        if mydb.is_connected():
            return True, mydb
        else:
            return False, None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False, None

# Function to reset MySQL password for a given username
def reset_password(username, old_password, new_password):
    try:
        # Connect to MySQL Server with the old password
        mydb = mysql.connector.connect(
            host="localhost",
            user=username,
            password=old_password
        )
        mycursor = mydb.cursor()

        # Reset the password for the specified username
        mycursor.execute(f"ALTER USER '{username}'@'localhost' IDENTIFIED BY '{new_password}'")
        mydb.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

# Create Streamlit App
def main():

    # Watermark
    st.markdown("<p style='text-align:left;color:gray;font-size:small;'>Developed by: Dopana Rohit Kumar</p>", unsafe_allow_html=True)
    
    st.title("🤖MySQL with Streamlit web app")

    # Create a session state to store authentication status and credentials
    session_state = st.session_state

    if 'authenticated' not in session_state:
        session_state.authenticated = False

    if 'reset_password' not in session_state:
        session_state.reset_password = False

    if 'username' not in session_state:
        session_state.username = ""

    if 'password' not in session_state:
        session_state.password = ""

    if not session_state.authenticated:
        # Login Form
        st.subheader("Login")
        username = st.text_input("Username", value=session_state.username)
        password = st.text_input("Password", type="password", value=session_state.password)
        
        # Display Reset Password checkbox
        session_state.reset_password = st.checkbox("Reset Password")

        # Show Reset Password panel if checkbox is checked
        if session_state.reset_password:
            reset_password_expander = st.expander("Reset Password", expanded=True)
            with reset_password_expander:
                reset_password_panel()

        if st.button("Login"):
            authenticated, db_connection = authenticate(username, password)
            if authenticated:
                session_state.authenticated = True
                session_state.db_connection = db_connection
                session_state.username = username
                session_state.password = password
                st.success("Login Successful!")
            else:
                st.error("Invalid username or password. Please try again.")


    if session_state.authenticated:
        # Add logout button in side panel
        if st.sidebar.button("Logout", help="Click to logout"):
            session_state.authenticated = False
            st.experimental_rerun()

        st.sidebar.subheader("Database Operations")
        perform_operations(session_state.db_connection)

# Panel for resetting password
def reset_password_panel():
    username_key = "reset_username_input"
    old_password_key = "reset_old_password_input"
    new_password_key = "reset_new_password_input"
    confirm_new_password_key = "reset_confirm_new_password_input"

    username = st.text_input("Username", key=username_key)
    old_password = st.text_input("Enter Old Password", type="password", key=old_password_key)
    new_password = st.text_input("Enter New Password", type="password", key=new_password_key)
    confirm_new_password = st.text_input("Confirm New Password", type="password", key=confirm_new_password_key)
    if st.button("Reset"):
        if new_password == confirm_new_password:
            if reset_password(username, old_password, new_password):
                st.success("Password reset successfully!")
            else:
                st.error("Failed to reset password. Please check your old password.")
        else:
            st.error("New password and confirm password do not match.")



# Function to perform database operations
def perform_operations(db_connection):
    mycursor = db_connection.cursor()
    
    # Checkbox for uploading MySQL script file
    upload_sql_script = st.sidebar.checkbox("Upload MySQL Script File")
    if upload_sql_script:
        upload_sql_script = st.file_uploader("Upload SQL Script", type=['sql'])
        
        if upload_sql_script is not None:
            if st.button("Execute Script"):
                execute_sql_script(upload_sql_script, mycursor, db_connection)

    # Checkbox for managing database
    manage_database = st.sidebar.checkbox("Manage Database")
    if manage_database:
        manage_database_operations(mycursor, db_connection)
    else:
        perform_crud_operations(mycursor, db_connection)

# Function to execute SQL script
def execute_sql_script(uploaded_file, mycursor, db_connection):
    try:
        # Read the content of the uploaded file
        content_str = io.StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        # Split the content into individual queries
        queries = content_str.split(';')
        # Execute each query
        for query in queries:
            if query.strip():
                mycursor.execute(query)
        db_connection.commit()
        st.success("SQL script executed successfully and queries added to the database.")
    except mysql.connector.Error as err:
        st.error(f"An error occurred while executing the SQL script: {err}")

# Function to perform CRUD operations
def perform_crud_operations(mycursor, db_connection):
    # Checkbox for creating new database or table
    create_new_db_table = st.sidebar.checkbox("Create New Database or Table")
    if create_new_db_table:
        create_new_database_or_table(mycursor)

    # Display Options for CRUD Operations
    operation = st.sidebar.selectbox("Select an Operation", ("Create", "Read", "Update", "Delete"),
                                     placeholder='CRUD Operation', index=None)
    if operation != "Read":
        selected_database, selected_table = select_database_and_table(mycursor)

    # Perform Selected CRUD Operations
    if operation == "Create" and not create_new_db_table:
        create_record(selected_database, selected_table, mycursor, db_connection)

    elif operation == "Read":
        read_records(mycursor)

    elif operation == "Update":
        update_record(selected_database, selected_table, mycursor, db_connection)

    elif operation == "Delete":
        delete_record(selected_database, selected_table, mycursor, db_connection)

# Function to manage database operations
def manage_database_operations(mycursor, db_connection):
    selected_database = st.sidebar.selectbox("Select Database", get_all_databases(mycursor), key="manage_database_selectbox",
                                             placeholder='Select Database', index=None)
    if selected_database:
        operation = st.sidebar.selectbox("Select Operation", ("Alter Table","Truncate Table","Drop Table","Drop Database" ),
                                         index=None)
        if operation == "Alter Table":
            alter_table(selected_database, mycursor, db_connection)
        elif operation == "Truncate Table":
            truncate_table(selected_database, mycursor, db_connection)
        elif operation == "Drop Table":
            drop_table(selected_database, mycursor, db_connection)
        elif operation == "Drop Database":
            drop_database(selected_database, mycursor, db_connection)


# Function to alter table
def alter_table(selected_database, mycursor, db_connection):
    st.subheader("Alter Table")
    mycursor.execute(f"USE {selected_database}")
    selected_table = st.selectbox("Select Table to Alter", get_all_tables(selected_database, mycursor))
    if selected_table:
        try:
            # Fetching table columns
            mycursor.execute(f"DESCRIBE {selected_table}")
            table_columns = [col[0] for col in mycursor.fetchall()]
            selected_column = st.selectbox("Select Column to Alter", table_columns)
            if selected_column:
                # Fetching data type of selected column
                mycursor.execute(f"SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}' AND COLUMN_NAME = '{selected_column}'")
                selected_column_data_type = mycursor.fetchone()[0]

                alter_option = st.radio("Select Option", ("Rename Column", "Change Column Type", "Add New Column", "Delete Column", "Rename Table"))
                if alter_option == "Rename Column":
                    new_column_name = st.text_input("Enter New Column Name (e.g., new_column int(100))")
                    if st.button("Rename") and new_column_name:
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} CHANGE {selected_column} {new_column_name}")
                            db_connection.commit()
                            st.success("Column Renamed Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Change Column Type":
                    new_column_type = st.text_input("Enter New Column Type (e.g., int(100) or varchar(255))", placeholder=f"Current: {selected_column_data_type}")
                    if st.button("Change Type") and new_column_type:
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} MODIFY {selected_column} {new_column_type}")
                            db_connection.commit()
                            st.success("Column Type Changed Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Add New Column":
                    new_column_input = st.text_input("Enter New Column Name and Type (e.g., new_column VARCHAR(255))")
                    if st.button("Add Column") and new_column_input:
                        try:
                            new_column_data = new_column_input.split()
                            new_column_name = new_column_data[0]
                            new_column_type = " ".join(new_column_data[1:])
                            mycursor.execute(f"ALTER TABLE {selected_table} ADD {new_column_name} {new_column_type}")
                            db_connection.commit()
                            st.success("New Column Added Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Delete Column":
                    column_to_delete = st.selectbox("Select Column to Delete", table_columns)
                    if st.button("Delete Column"):
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} DROP COLUMN {column_to_delete}")
                            db_connection.commit()
                            st.success("Column Deleted Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Rename Table":
                    new_table_name = st.text_input("Enter New Table Name")
                    if st.button("Rename Table") and new_table_name:
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} RENAME TO {new_table_name}")
                            db_connection.commit()
                            st.success("Table Renamed Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")


# Function to truncate a table
def truncate_table(selected_database, mycursor, db_connection):
    st.subheader("Truncate Table")
    mycursor.execute(f"USE {selected_database}")
    selected_table = st.selectbox("Select Table to Truncate", get_all_tables(selected_database, mycursor))
    if selected_table:
        if st.button("Truncate"):
            try:
                mycursor.execute(f"TRUNCATE TABLE {selected_table}")
                db_connection.commit()
                st.success(f"Table '{selected_table}' truncated successfully!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")
# Function to drop table
def drop_table(selected_database, mycursor, db_connection):
    st.subheader("Drop Table")
    mycursor.execute(f"USE {selected_database}")
    selected_table = st.selectbox("Select Table to Drop", get_all_tables(selected_database, mycursor))
    if selected_table:
        if st.button("Drop"):
            try:
                mycursor.execute(f"DROP TABLE {selected_table}")
                st.success(f"Table '{selected_table}' dropped successfully!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")

# Function to drop database
def drop_database(selected_database, mycursor, db_connection):
    st.subheader("Drop Database")
    if st.button("Drop"):
        try:
            mycursor.execute(f"DROP DATABASE {selected_database}")
            st.success(f"Database '{selected_database}' dropped successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Select Database and Table
def select_database_and_table(mycursor):
    st.sidebar.subheader("Select Database")
    mycursor.execute("SHOW DATABASES")
    databases = [db[0] for db in mycursor.fetchall()]
    if not databases:
        st.sidebar.warning("No databases found.")
        selected_database = None
    else:
        selected_database = st.sidebar.selectbox("Database", databases, placeholder='Select Database', index=None)

    if selected_database:
        # Select Table
        mycursor.execute(f"USE {selected_database}")
        mycursor.execute("SHOW TABLES")
        tables = [table[0] for table in mycursor.fetchall()]
        if not tables:
            st.sidebar.warning("No tables found in the selected database.")
            selected_table = None
        else:
            selected_table = st.sidebar.selectbox("Table", tables, index=0)
            # Show selected table
            st.sidebar.write(f"Selected Table: {selected_table}")
    else:
        selected_table = None

    return selected_database, selected_table

# Function to create a new database or table
def create_new_database_or_table(mycursor):
    st.subheader("Create New Database or Table")
    create_option = st.radio("Select Option", ("Database", "Table"))
    if create_option == "Database":
        create_new_database(mycursor)
    elif create_option == "Table":
        create_new_table(mycursor)

# Function to create a new database
def create_new_database(mycursor):
    new_db_name = st.text_input("Enter New Database Name:")
    if st.button("Create") and new_db_name:
        try:
            # Create new database
            mycursor.execute(f"CREATE DATABASE {new_db_name}")
            st.success(f"Database '{new_db_name}' created successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to create a new table
def create_new_table(mycursor):
    st.subheader("Create New Table")
    selected_database = st.selectbox("Select Database", get_all_databases(mycursor), key="create_table_selectbox",
                                     placeholder='Select Database', index=None)
    if selected_database:
        mycursor.execute(f"USE {selected_database}")
        new_table_name = st.text_input("Enter New Table Name:")
        columns_input = st.text_area("Enter Column Names, Types, and Properties (comma-separated):",placeholder='e.g., id int(10) AUTO_INCREMENT PRIMARY KEY, name varchar(255), email varchar(255)')
        if st.button("Create") and new_table_name and columns_input:
            try:
                # Split the input by comma to get individual column definitions
                column_defs = columns_input.split(',')
                # Join the column definitions to create the SQL query
                sql_query = f"CREATE TABLE {new_table_name} ({', '.join(column_defs)})"
                # Execute the SQL query
                mycursor.execute(sql_query)
                st.success(f"Table '{new_table_name}' created successfully in database '{selected_database}'!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")


# Function to create a record
def create_record(selected_database, selected_table, mycursor, db_connection):
    st.subheader("Create a Record")
    st.write(f"Selected Table: {selected_table}")
    mycursor.execute(f"DESCRIBE {selected_table}")
    columns = [col[0] for col in mycursor.fetchall()]
    entry_values = {}
    for col in columns:
        entry_values[col] = st.text_input(f"Enter {col}")
    if st.button("Create"):
        column_names = ', '.join(entry_values.keys())
        column_values = ', '.join(["'{}'".format(value) for value in entry_values.values()])
        sql = f"INSERT INTO {selected_table}({column_names}) VALUES({column_values})"
        mycursor.execute(sql)
        db_connection.commit()
        st.success("Record Created Successfully!!!")

# Function to read records
def read_records(mycursor):
    st.subheader("Read Records")
    selected_database, selected_table = select_database_and_table(mycursor)
    if selected_table:
        st.write(f"Selected Table: {selected_table}")
        try:
            mycursor.execute(f"SELECT * FROM {selected_table}")
            result = mycursor.fetchall()
            df = pd.DataFrame(result, columns=[i[0] for i in mycursor.description])
            st.write(df)
            # Read and discard the unread result
            mycursor.fetchall()
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to update a record
def update_record(selected_database, selected_table, mycursor, db_connection):
    st.subheader("Update a Record")
    if selected_table:
        st.write(f"Selected Table: {selected_table}")
        # Get all primary key columns
        try:
            mycursor.execute(f"SHOW KEYS FROM {selected_table} WHERE Key_name = 'PRIMARY'")
            primary_keys_info = mycursor.fetchall()

            if not primary_keys_info:
                st.error("No primary key found in the table. Cannot perform update.")
                return

            primary_keys = [primary_key_info[4] for primary_key_info in primary_keys_info]

            # Check if there is only one primary key
            if len(primary_keys) == 1:
                primary_key = primary_keys[0]
                # Get all column names excluding the primary key
                mycursor.execute(f"DESCRIBE {selected_table}")
                columns = [col[0] for col in mycursor.fetchall() if col[0] != primary_key]
                # Show primary key column for reference
                st.write(f"Primary Key: {primary_key}")

            else:
                st.write("Multiple primary keys found in the table.")
                st.write("Select the primary key to use for update:")
                # Automatically select the first primary key for update
                primary_key = primary_keys[0]
                st.write(f"Primary key '{primary_key}' selected for update.")
                # Get all column names excluding the selected primary key
                mycursor.execute(f"DESCRIBE {selected_table}")
                columns = [col[0] for col in mycursor.fetchall() if col[0] != primary_key]
                # Show primary key column for reference
                st.write(f"Primary Key: {primary_key}")

            # Get all primary key values
            mycursor.execute(f"SELECT {primary_key} FROM {selected_table}")
            primary_key_values = [row[0] for row in mycursor.fetchall()]

            # Display dropdown list for primary key selection
            id = st.selectbox(f"Select {primary_key} to Update", primary_key_values)

            # Fetch current values for the selected record
            mycursor.execute(f"SELECT * FROM {selected_table} WHERE {primary_key} = %s", (id,))
            current_record = mycursor.fetchone()

            # Input fields for updating values
            entry_values = {}
            for col, value in zip(columns, current_record[1:]):  # Skip primary key column
                entry_values[col] = st.text_input(f"Enter New {col}", placeholder=value)

            if st.button("Update"):
                # Construct SQL query for update
                update_values = ', '.join([f"{col}='{value}'" for col, value in entry_values.items() if value.strip()])
                if update_values:
                    sql = f"UPDATE {selected_table} SET {update_values} WHERE {primary_key}=%s"
                    val = (id,)
                    mycursor.execute(sql, val)
                    db_connection.commit()
                    st.success("Record Updated Successfully!!!")
                else:
                    st.warning("No fields to update.")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to delete a record
def delete_record(selected_database, selected_table, mycursor, db_connection):
    st.subheader("Delete a Record")
    if selected_table:
        st.write(f"Selected Table: {selected_table}")
        # Get all primary key columns
        try:
            mycursor.execute(f"SHOW KEYS FROM {selected_table} WHERE Key_name = 'PRIMARY'")
            primary_keys_info = mycursor.fetchall()

            if not primary_keys_info:
                st.error("No primary key found in the table. Cannot perform deletion.")
                return

            primary_keys = [primary_key_info[4] for primary_key_info in primary_keys_info]

            # Check if there is only one primary key
            if len(primary_keys) == 1:
                primary_key = primary_keys[0]
                # Get all primary key values
                mycursor.execute(f"SELECT {primary_key} FROM {selected_table}")
                primary_key_values = [row[0] for row in mycursor.fetchall()]
                # Display dropdown list for primary key selection
                id = st.selectbox(f"Select {primary_key} to Delete", primary_key_values)
                if st.button("Delete"):
                    # Construct SQL query for deletion
                    sql = f"DELETE FROM {selected_table} WHERE {primary_key} = %s"
                    val = (id,)
                    mycursor.execute(sql, val)
                    db_connection.commit()
                    st.success("Record Deleted Successfully!!!")
            else:
                st.write("Multiple primary keys found in the table.")
                st.write("Select the primary key to use for deletion:")
                st.write("Cannot perform deletion for tables with composite primary keys.")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to get all databases
def get_all_databases(mycursor):
    mycursor.execute("SHOW DATABASES")
    databases = [db[0] for db in mycursor.fetchall()]
    return databases

# Function to get all tables in a database
def get_all_tables(database, mycursor):
    mycursor.execute(f"USE {database}")
    mycursor.execute("SHOW TABLES")
    tables = [table[0] for table in mycursor.fetchall()]
    return tables

if __name__ == "__main__":
    main()
