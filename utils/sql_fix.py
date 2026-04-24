from openai import OpenAI
from django.conf import settings

# Initialize OpenAI client with API key from Django settings

def fix_sql_query(request: dict, model: str = "gpt-4") -> str:
    """
    Fix the user's SQL query based on the error message and schema using the OpenAI API.

    Parameters:
    request (dict): Dictionary with keys 'sql', 'dialect', 'error_message', and 'schema_ddl'.
                    Example:
                    {
                        "sql": "SELECT COUNT(*) AS total_advanced_skills FROM public.user_skills WHERE skill_leve = 'advanced';",
                        "dialect": "postgres",
                        "error_message": "ERROR: column \"skill_leve\" does not exist\\n  Hint: Perhaps you meant to reference the column \"user_skills.skill_level\".\\n  Position: 201",
                        "schema_ddl": "CREATE TABLE public.user_skills (\\n  primary_key int4,\\n  unique_id uuid,\\n  created_date timestamptz,\\n  is_active bool,\\n  skill_level varchar,\\n  profile_id int4,\\n  skill_id int4\\n);\\n"
                    }
    model (str): OpenAI model name for generation (defaulting to gpt-4 for better accuracy).

    Returns:
    str: The corrected SQL query string, or an error message if the fix fails.
    """
    # Extract required inputs from the request dictionary, providing sensible defaults
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    original_sql = request.get("sql", "").strip()
    dialect = request.get("dialect", "mysql").lower() # Ensure dialect is lowercase for consistency
    error_message = request.get("error_message", "No specific error message provided.").strip()
    schema_ddl = request.get("schema_ddl", "").strip()

    # Define the prompt for the OpenAI model
    prompt = f"""
You are an SQL query fixing assistant. Your primary goal is to provide a corrected, syntactically accurate SQL query.

Given a user's SQL query that has an error, the SQL dialect, the detailed error message, and the schema DDL, your task is to generate a corrected SQL query that directly addresses and fixes the identified error.

---

### Inputs for SQL Query Fix:

- **SQL dialect:** {dialect}
- **Original SQL query (with error):**
```sql
{original_sql}
```
- **Error message:**
```
{error_message}
```
- **Schema DDL:**
```sql
{schema_ddl}
```

---

### Guidelines for Generating the Fixed SQL Query:

1.  **Error Analysis:** Thoroughly analyze the `error_message` to pinpoint the exact issue.
2.  **Schema Reference:** Always refer to the `Schema DDL` to verify table names, column names, and data types.
3.  **Correction:** Correct the `Original SQL query` to resolve the error.
4.  **Syntax & Dialect:** Ensure the fixed query is syntactically correct for the specified `{dialect}`.
5.  **Identifier Quoting:** Use appropriate identifier quoting for the `{dialect}` (e.g., backticks for MySQL, double quotes for PostgreSQL, square brackets for SQL Server).
6.  **Minimal Changes:** Make only the necessary changes to fix the error. Preserve the original query's intent and structure as much as possible.
7.  **Semicolon:** End the corrected query with a semicolon.
8.  **Output Format:** **Crucially, wrap the corrected SQL query ONLY in a Markdown code block (e.g., ````sql... ````). Do not include any other text or explanation outside this block.**

---

Generate the corrected SQL query now within the specified Markdown code block.
"""

    try:
        # Call the OpenAI API to generate the corrected query
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract and clean the corrected SQL query from the response
        corrected_sql = response.choices[0].message.content.strip()

        # Remove Markdown code block fences if present
        if corrected_sql.startswith("```sql"):
            # Find the first newline after ```sql and the last ```
            start_index = corrected_sql.find('\n') + 1
            end_index = corrected_sql.rfind('```')
            if start_index != -1 and end_index != -1:
                corrected_sql = corrected_sql[start_index:end_index].strip()
            else: # Fallback if expected format not found, but starts with ```sql
                corrected_sql = corrected_sql.replace("```sql", "").replace("```", "").strip()

        return corrected_sql

    except Exception as e:
        # Log the error and return an informative message
        print(f"Error calling OpenAI API: {e}")
        return f"An error occurred while trying to fix the SQL query: {e}"

