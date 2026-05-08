from openai import OpenAI
from django.conf import settings
import json



def generate_sql_from_request(request: dict, model: str = "gpt-4.1") -> str:
    """
    Generate an SQL query from a structured request using the OpenAI API.

    Parameters:
        request (dict): Dictionary with keys like 'dialect', 'instructions', 'tables', and 'query_request'.
        model (str): OpenAI model name for generation.

    Returns:
        str: The generated SQL query string.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    dialect = request.get("dialect", "mysql")
    instructions = request.get("instructions", "generate sql")
    tables = request.get("tables", {})

    # Format tables dictionary as JSON string for clarity
    tables_str = json.dumps(tables, indent=2)

    prompt = f"""
You are a highly skilled SQL generation assistant. Your task is to generate an optimized, syntactically correct SQL query based on the user's request, the specified SQL dialect, and the provided table schemas.

Instructions for Generating SQL Queries is {instructions}:
Dialect and Schema: Pay close attention to the specified SQL dialect and the provided table schemas.
in SELECT statements never use 'SELECT *'  
also All Key words in sql language should be capitalized


NOTE: Return Only The query Results , Dont add Comments Or any thing else

---

- **SQL dialect:** {dialect}

- **SQL Table:** {tables}
```
---

"""

    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )

    sql_query = response.choices[0].message.content.strip()
    return sql_query
