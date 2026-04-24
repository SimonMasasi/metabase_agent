SAMPLE_QUERY_ONE = """
{
                "dataset_query": {
                    "database": 5,
                    "type": "query",
                    "query": {
                        "aggregation": [["count"]],
                        "breakout": [["field", "gender", {"base-type": "type/Text"}]],
                        "source-table": "card__572",
                    },
                },
                "display": "bar",
                "displayIsLocked": true,
                "parameters": [],
                "visualization_settings": {},
                "original_card_id": 572,
                "type": "question",
            } 
"""
