# import requests
# import json
# import re

# def process_payg_workflow(product_qid, product_id):
#     print("------6----")
#     """
#     Process PAYG workflow by making initial provision request and extracting PAYG ID for GraphQL mutation
    
#     Args:
#         product_qid (str): Product QID
#         product_id (str): Product ID
#         base_url (str): Base URL for provision endpoint
#         username (str): Username for Basic Auth
#         password (str): Password for Basic Auth
#         graphql_url (str): URL for GraphQL endpoint
#         bearer_token (str): Bearer token for GraphQL authentication
#         seller_item_id (str): Seller item ID for the GraphQL mutation
    
#     Returns:
#         dict: Response from GraphQL mutation or error details
#     """
#     # Prepare payload for provision request
#     payload = {
#         "product_qid": product_qid,
#         "productId": product_id
#     }
#     print(payload, "----28---")
#     try:
#         print("----3---")
#         # Make provision request with Basic Auth
#         response = requests.post(
#             url="https://payg.angazadesign.com/nexus/v1/provision_unit",
#             json=payload,
#             auth=("paulkamita", "PhdgRcs9e2Fp")
#         )
#         print(response.text, "response----212")
#         # Check if request was successful
#         response.raise_for_status()
        
#         # Parse response
#         response_data = response.json()
#         print(response_data, "Response Data---41--")
#         # Extract PAYG ID using regex
#         reason_text = response_data.get('context', {}).get('reason', '')
#         payg_id_match = re.search(r'PAYG ID (\d+)', reason_text)
        
#         print(payg_id_match, "Payg Id Match-----46---")
#         if not payg_id_match:
#             return {"error": "Could not extract PAYG ID from response"}
        
#         payg_id = payg_id_match.group(1)

#         print(payg_id, "Payg Id Match-----46---")
#         # Prepare GraphQL mutation
#         graphql_mutation = """
#         mutation {
#           updateItem(updateItemInput: {
#             itemId: "%s",
#             sellerItemID: "%s"
#           }) {
#             _id
#           }
#         }
#         """ % (product_id, payg_id)
        
#         # Make GraphQL request
#         headers = {
#             "Authorization": f"Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InhqTTVuMytXY2d3S0k0aEd6Ry94UzhOb2IvNW1keTdSOGhNVVQ3ZW9aNjA9In0.eyJkZWxlZ2F0b3JSb2xlSWQiOiI2MTc2NjhjYWY3NGVlYjA4OWIzNGVlODMiLCJkZWxlZ2F0b3JFbWFpbCI6ImRlbm5pc19uam9ndUBvbW5pdm9sdGFpYy5jb20iLCJ1c2VySWQiOiI2NjNhMTM2MjA0MzE1MDZlODVkNzYxNzEiLCJzZXJ2aWNlcklkIjpudWxsLCJkaXN0cmlidXRvcklkIjpudWxsLCJlbWFpbCI6ImRlbm5pc19uam9ndUBvbW5pdm9sdGFpYy5jb20iLCJyb2xlSWQiOiI2MTc2NjhjYWY3NGVlYjA4OWIzNGVlODMiLCJyb2xlTmFtZSI6IlNVUEVSX0FETUlOIiwic2VydmljZSI6bnVsbCwiYXV0aEluc3RhbmNlIjoiNjE3NjY4YTBmNzRlZWIxOTQ2MzRlZTgyIiwiZGlzdHJpYnV0b3JQZXJtIjpudWxsLCJzdWJSb2xlSWQiOm51bGwsImRlZmF1bHRJbnN0YW5jZSI6IjYxNzY2OGEwZjc0ZWViMTk0NjM0ZWU4MiIsImRpc3RyaWJ1dG9yRGVsZWdhdGUiOmZhbHNlLCJpYXQiOjE3MzYyMzg0OTYsImV4cCI6MTczNjMyNDg5Nn0.EqChxdD-yl6GLHVyc4tCF-yrxJdlF1MN_nuE_mBhcSPfxkWJWMvFC0u8QFDAneFsWLUYRLTz3ZOcyLTDJbhU5bBCUBZ6qSu3mJYybbV1e1CngDCuuw5rWQ06uCk6SIB72Yonxm63_Hk5uCop04TYhfCebplRPeoUKFhVTDTri53XbS0QwG8HmJ2h-xJ7ji67dG5Gj6kERWh5BgAItipm5cplhjsFNYRidkuDBo_9s6vQx3_RymNvJxoKeJkC2GAjXjl8fy1U8bWnj95qUq3X02482T61xUBBEfYqmngLbRu01JtqSKNAhqSHM070Psth9w-CmmE7_nUx3-pDUWCtmw",
#             "Content-Type": "application/json"
#         }
        
#         graphql_payload = {
#             "query": graphql_mutation
#         }
        
#         graphql_response = requests.post(
#             graphql_url="https://production-omnivoltaic-graphql-api.omnivoltaic.com/graphql",
#             json=graphql_payload,
#             headers=headers
#         )
        
#         graphql_response.raise_for_status()
#         print(graphql_response.json(), "Grpah Ql JSON")
#         return graphql_response.json()
        
#     except requests.exceptions.RequestException as e:
#         print(e,'-----88')
#         return {"error": f"Request failed: {str(e)}"}
#     except json.JSONDecodeError as e:
#         print('----91--')
#         return {"error": f"Failed to parse JSON response: {str(e)}"}
#     except Exception as e:
#         print(e, "---93---")
#         return {"error": f"Unexpected error: {str(e)}"}
    

# process_payg_workflow(
#     product_qid="PT001885", 
#     product_id="6678eb23e9c933a578baf6fa"
#     )

# import requests
# import json
# import re

# def process_payg_workflow(product_qid, product_id):
#     """
#     Process PAYG workflow by making initial provision request and extracting PAYG ID for GraphQL mutation
    
#     Args:
#         product_qid (str): Product QID
#         product_id (str): Product ID
    
#     Returns:
#         dict: Response from GraphQL mutation or error details
#     """
#     print("------6----")
#     # Prepare payload for provision request
#     payload = {
#         "product_qid": product_qid,
#         "productId": product_id
#     }
#     print(payload, "----28---")
    
#     try:
#         print("----3---")
#         # Make provision request with Basic Auth
#         response = requests.post(
#             url="https://payg.angazadesign.com/nexus/v1/provision_unit",
#             json=payload,
#             auth=("paulkamita", "PhdgRcs9e2Fp")
#         )
#         print(response.text, "response----212")

#         # We do NOT raise_for_status() here because we might expect a 400 error
#         # and still want to parse the response JSON.

#         # Parse the response JSON (this can raise a JSONDecodeError if invalid).
#         response_data = response.json()
        
#         # Check status code
#         if response.status_code == 200:
#             # Possibly in the success case, the server also returns context.reason or a direct PAYG ID
#             # If the success response structure is different, adapt accordingly.
#             reason_text = response_data.get('context', {}).get('reason', '')
            
#         elif response.status_code == 400:
#             # We expect a 400 with a reason containing something like "PAYG ID 852021419"
#             reason_text = response_data.get('context', {}).get('reason', '')
#             print("Got 400 - reason_text:", reason_text)
#         else:
#             # Handle other HTTP statuses (401,403,500, etc.)
#             return {
#                 "error": f"Unexpected status code {response.status_code}: {response.text}"
#             }
        
#         # Extract PAYG ID using regex from the reason_text
#         payg_id_match = re.search(r'PAYG ID (\d+)', reason_text)
#         print(payg_id_match, "Payg Id Match-----46---")
        
#         if not payg_id_match:
#             # If we can’t find PAYG ID in the reason, either the response format was different,
#             # or we had a success scenario with no ID in that field. Adjust as needed.
#             return {"error": "Could not extract PAYG ID from response"}
        
#         payg_id = payg_id_match.group(1)
#         print(payg_id, "Payg Id Match-----46---")
        
#         # Prepare GraphQL mutation
#         graphql_mutation = """
#         mutation {
#           updateItem(updateItemInput: {
#             itemId: "%s",
#             sellerItemID: "%s"
#           }) {
#             _id
#           }
#         }
#         """ % (product_id, payg_id)
        
#         # Make GraphQL request
#         headers = {
#             "Authorization": (
#                 "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InhqTTVuMytXY2d3S0k0aEd6Ry94UzhOb2IvNW1keTdSOGhNVVQ3ZW9aNjA9In0.eyJkZWxlZ2F0b3JSb2xlSWQiOiI2MTc2NjhjYWY3NGVlYjA4OWIzNGVlODMiLCJkZWxlZ2F0b3JFbWFpbCI6ImRlbm5pc19uam9ndUBvbW5pdm9sdGFpYy5jb20iLCJ1c2VySWQiOiI2NjNhMTM2MjA0MzE1MDZlODVkNzYxNzEiLCJzZXJ2aWNlcklkIjpudWxsLCJkaXN0cmlidXRvcklkIjpudWxsLCJlbWFpbCI6ImRlbm5pc19uam9ndUBvbW5pdm9sdGFpYy5jb20iLCJyb2xlSWQiOiI2MTc2NjhjYWY3NGVlYjA4OWIzNGVlODMiLCJyb2xlTmFtZSI6IlNVUEVSX0FETUlOIiwic2VydmljZSI6bnVsbCwiYXV0aEluc3RhbmNlIjoiNjE3NjY4YTBmNzRlZWIxOTQ2MzRlZTgyIiwiZGlzdHJpYnV0b3JQZXJtIjpudWxsLCJzdWJSb2xlSWQiOm51bGwsImRlZmF1bHRJbnN0YW5jZSI6IjYxNzY2OGEwZjc0ZWViMTk0NjM0ZWU4MiIsImRpc3RyaWJ1dG9yRGVsZWdhdGUiOmZhbHNlLCJpYXQiOjE3MzczNjYzOTIsImV4cCI6MTczNzQ1Mjc5Mn0.wsFIKDpGHBNTr-zGiFJ6QYXn9az-2537o7Z5qalmICLH378ydyZRytuRyptD9JOpPtDh0bt7WEAb0ybLIyWae7pP2IxE1w_6Ouo4noRUn38fV5Fc689An7gGFBLqNJ2FXcF_Miffqlnyut75eeDufWnNmCjiLmJfTAWWVUKaMZw5HNHqF_7Q2eamY_5nOfC1eHnzm-Y9pZGdkh-vswm-a6l-NXWgxJg6sqTwnBDFnOWcE2jzvHeuXKnFoDvvO37-rRE2XvsPa9AF8FiQgi4BzqLj93JhxCOp8nUYFU4ZsfAlQZN18awv4YLNvK2_WF8AXfzud8EKZc41seQ4ocwOUg"
#             ),
#             "Content-Type": "application/json"
#         }
        
#         graphql_payload = {
#             "query": graphql_mutation
#         }
        
#         graphql_response = requests.post(
#             url="https://production-omnivoltaic-graphql-api.omnivoltaic.com/graphql",
#             json=graphql_payload,
#             headers=headers
#         )
        
#         # Raise only if the GraphQL request fails (4xx/5xx)
#         graphql_response.raise_for_status()
        
#         graphql_data = graphql_response.json()
#         print(graphql_data, "GraphQL JSON")
#         return graphql_data

#     except requests.exceptions.RequestException as e:
#         print(e,'-----88')
#         return {"error": f"Request failed: {str(e)}"}
#     except json.JSONDecodeError as e:
#         print('----91--')
#         return {"error": f"Failed to parse JSON response: {str(e)}"}
#     except Exception as e:
#         print(e, "---93---")
#         return {"error": f"Unexpected error: {str(e)}"}

# # Example usage:
# process_payg_workflow(
#     product_qid="PT001885", 
#     product_id="6678eb24d153609cf65c3141"
# )


import requests
import json
import re

def process_payg_workflow(product_qid, product_ids):
    """
    Process PAYG workflow for multiple product IDs by making a provision request
    and extracting a PAYG ID for each, then running a GraphQL mutation.

    Args:
        product_qid (str): Product QID (common for all products in this example)
        product_ids (list[str]): List of Product IDs to process

    Returns:
        list: A list of results, where each element is either:
              { "product_id": "<id>", "graphql_result": <GraphQL JSON> }
              or
              { "product_id": "<id>", "error": "<error message>" }
    """
    results = []

    for product_id in product_ids:
        print(f"\nProcessing product_id: {product_id}")
        
        # Prepare payload for a single provision request
        payload = {
            "product_qid": product_qid,
            "productId": product_id
        }
        
        try:
            # 1. Provision request
            response = requests.post(
                url="https://payg.angazadesign.com/nexus/v1/provision_unit",
                json=payload,
                auth=("paulkamita", "PhdgRcs9e2Fp")
            )
            # Parse JSON (may raise JSONDecodeError)
            response_data = response.json()
            
            if response.status_code == 200:
                # Possibly in success, the server returns data differently
                reason_text = response_data.get('context', {}).get('reason', '')
            elif response.status_code == 400:
                # We might expect a 400 with a reason containing something like:
                # "ProductId 6678eb23e9c933a578baf6fa already assigned to PAYG ID 852021419"
                reason_text = response_data.get('context', {}).get('reason', '')
                print("Received 400 response:", reason_text)
            else:
                # Any other unexpected status code
                error_msg = (f"Unexpected status code {response.status_code}: "
                             f"{response.text}")
                results.append({
                    "product_id": product_id,
                    "error": error_msg
                })
                # Move on to the next product ID
                continue
            
            # 2. Extract PAYG ID from the reason text
            payg_id_match = re.search(r'PAYG ID (\d+)', reason_text)
            if not payg_id_match:
                # If we cannot extract the PAYG ID, log an error and continue
                results.append({
                    "product_id": product_id,
                    "error": f"Could not extract PAYG ID. reason_text: '{reason_text}'"
                })
                continue
            
            payg_id = payg_id_match.group(1)
            print("Extracted PAYG ID:", payg_id)
            
            # Prepare GraphQL mutation
            graphql_mutation = """
            mutation {
            updateItem(updateItemInput: {
                itemId: "%s",
                sellerItemID: "%s"
            }) {
                _id
            }
            }
            """ % (product_id, payg_id)
            
            # 4. Make the GraphQL request
            headers = {
                "Authorization": (
                    "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InhqTTVuMytXY2d3S0k0aEd6Ry94UzhOb2IvNW1keTdSOGhNVVQ3ZW9aNjA9In0.eyJkZWxlZ2F0b3JSb2xlSWQiOiI2MTc2NjhjYWY3NGVlYjA4OWIzNGVlODMiLCJkZWxlZ2F0b3JFbWFpbCI6ImRlbm5pc19uam9ndUBvbW5pdm9sdGFpYy5jb20iLCJ1c2VySWQiOiI2NjNhMTM2MjA0MzE1MDZlODVkNzYxNzEiLCJzZXJ2aWNlcklkIjpudWxsLCJkaXN0cmlidXRvcklkIjpudWxsLCJlbWFpbCI6ImRlbm5pc19uam9ndUBvbW5pdm9sdGFpYy5jb20iLCJyb2xlSWQiOiI2MTc2NjhjYWY3NGVlYjA4OWIzNGVlODMiLCJyb2xlTmFtZSI6IlNVUEVSX0FETUlOIiwic2VydmljZSI6bnVsbCwiYXV0aEluc3RhbmNlIjoiNjE3NjY4YTBmNzRlZWIxOTQ2MzRlZTgyIiwiZGlzdHJpYnV0b3JQZXJtIjpudWxsLCJzdWJSb2xlSWQiOm51bGwsImRlZmF1bHRJbnN0YW5jZSI6IjYxNzY2OGEwZjc0ZWViMTk0NjM0ZWU4MiIsImRpc3RyaWJ1dG9yRGVsZWdhdGUiOmZhbHNlLCJpYXQiOjE3MzczNjYzOTIsImV4cCI6MTczNzQ1Mjc5Mn0.wsFIKDpGHBNTr-zGiFJ6QYXn9az-2537o7Z5qalmICLH378ydyZRytuRyptD9JOpPtDh0bt7WEAb0ybLIyWae7pP2IxE1w_6Ouo4noRUn38fV5Fc689An7gGFBLqNJ2FXcF_Miffqlnyut75eeDufWnNmCjiLmJfTAWWVUKaMZw5HNHqF_7Q2eamY_5nOfC1eHnzm-Y9pZGdkh-vswm-a6l-NXWgxJg6sqTwnBDFnOWcE2jzvHeuXKnFoDvvO37-rRE2XvsPa9AF8FiQgi4BzqLj93JhxCOp8nUYFU4ZsfAlQZN18awv4YLNvK2_WF8AXfzud8EKZc41seQ4ocwOUg"
                ),
                "Content-Type": "application/json"
            }
            
            graphql_payload = {
                "query": graphql_mutation
            }
            
            graphql_response = requests.post(
                url="https://production-omnivoltaic-graphql-api.omnivoltaic.com/graphql",
                json=graphql_payload,
                headers=headers
            )
            graphql_response.raise_for_status()  # Raise if the GraphQL call fails (4xx/5xx)
            
            graphql_data = graphql_response.json()
            print("GraphQL response:", graphql_data)
            
            # Store success result
            results.append({
                "product_id": product_id,
                "graphql_result": graphql_data
            })

        except requests.exceptions.RequestException as e:
            # Catch network, DNS, or request issues
            results.append({
                "product_id": product_id,
                "error": f"Request failed: {str(e)}"
            })
        except json.JSONDecodeError as e:
            # Catch JSON parse errors
            results.append({
                "product_id": product_id,
                "error": f"Failed to parse JSON response: {str(e)}"
            })
        except Exception as e:
            # Catch anything else that might happen
            results.append({
                "product_id": product_id,
                "error": f"Unexpected error: {str(e)}"
            })

    return results


# Example usage with multiple product IDs:
all_product_ids = [
"6678eb245e7e585a50dcbbe7",
"6678eb27b1a37c6ba03f862b",
"6678eb27b1a37c6ba03f862d",
"6678eb28b1a37c6ba03f862e",
"6678eb285e7e585a50dcbbf2",
"6678eb28e9c933a578baf706",
"6678eb28b1a37c6ba03f862f",
"6678eb28d153609cf65c314d",
"6678eb285e7e585a50dcbbf3",
"6678eb28e9c933a578baf707",
"6678eb29b1a37c6ba03f8630",
"6678eb29e9c933a578baf708",
"6678eb29b1a37c6ba03f8631",
"6678eb29d153609cf65c314f",
"6678eb295e7e585a50dcbbf5",
"6678eb29e9c933a578baf709",
"6678eb29b1a37c6ba03f8632",
"6678eb29d153609cf65c3150",
"6678eb2a5e7e585a50dcbbf6",
"6678eb2ae9c933a578baf70a",
"6678eb32e9c933a578baf71f",
"6678eb32b1a37c6ba03f8648",
"6678eb33b1a37c6ba03f864b",
"6678eb33d153609cf65c3169",
"6678eb33b1a37c6ba03f864c",
"6678eb33e9c933a578baf723",
"6678eb33b1a37c6ba03f864c",
"6678eb38d153609cf65c3177",
"6678eb385e7e585a50dcbc1d",
"6678eb39e9c933a578baf731",
"6678eb39b1a37c6ba03f865a",
"6678eb39d153609cf65c3178",
"6678eb395e7e585a50dcbc1e",
"6678eb39e9c933a578baf732",
"6678eb39b1a37c6ba03f865b",
"6678eb39d153609cf65c3179",
"6678eb39b1a37c6ba03f865c",
"6678eb39d153609cf65c317a",
"6678eb3a5e7e585a50dcbc20",
"6678eb3ae9c933a578baf734",
"6678eb3ad153609cf65c317b",
"6678eb3ab1a37c6ba03f865d",
"6678eb3a5e7e585a50dcbc21",
"6678eb3ae9c933a578baf735",
"6678eb3ad153609cf65c317c",
"6678eb3bd153609cf65c317f",
"6678eb3ce9c933a578baf739",
"6678eb3cb1a37c6ba03f8662",
"6678eb3cd153609cf65c3180",
"6678eb3c5e7e585a50dcbc26",
"6678eb3ce9c933a578baf73a",
"6678eb3cb1a37c6ba03f8663",
"6678eb50d153609cf65c31b2",
"6678eb50b1a37c6ba03f8693",
"6678eb50e9c933a578baf76b",
"6678eb50d153609cf65c31b3",
"6678eb50b1a37c6ba03f8694",
"6678eb505e7e585a50dcbc58",
"6678eb50e9c933a578baf76c",
"6678eb50d153609cf65c31b4",
"6678eb50b1a37c6ba03f8695",
"6678eb505e7e585a50dcbc59",
"6678eb51e9c933a578baf76d",
"6678eb51d153609cf65c31b5",
"6678eb51b1a37c6ba03f8696",
"6678eb515e7e585a50dcbc5a",
"6678eb51e9c933a578baf76e",
"6678eb51b1a37c6ba03f8697",
"6678eb515e7e585a50dcbc5b",
"6678eb51e9c933a578baf76f",
"6678eb525e7e585a50dcbc5e",
"6678eb595e7e585a50dcbc70",
"6678eb5c5e7e585a50dcbc75",
"6678eb5de9c933a578baf789",
"6678eb5db1a37c6ba03f86b2",
"6678eb5dd153609cf65c31d2",
"6678eb5d5e7e585a50dcbc76",
"6678eb5de9c933a578baf78a",
"6678eb5db1a37c6ba03f86b4",
"6678eb5dd153609cf65c31d4",
"6678eb5e5e7e585a50dcbc78",
"6678eb5ee9c933a578baf78c",
"6678eb5eb1a37c6ba03f86b5",
"6678eb5ed153609cf65c31d5",
"6678eb5e5e7e585a50dcbc79",
"6678eb685e7e585a50dcbc94",
"6678eb68e9c933a578baf7a8",
"6678eb69d153609cf65c31f1",
"6678eb69b1a37c6ba03f86d1",
"6678eb695e7e585a50dcbc95",
"6678eb69e9c933a578baf7a9",
"6678eb69d153609cf65c31f2",
"6678eb69b1a37c6ba03f86d2",
"6678eb6ae9c933a578baf7ab",
"6678eb6ce9c933a578baf7b1",
"6678eb6eb1a37c6ba03f86e0",
"6678eb6ed153609cf65c3200",
"6678eb6f5e7e585a50dcbca4",
"6678eb6fe9c933a578baf7b8",
"6678eb6fb1a37c6ba03f86e1",
"6678eb6fd153609cf65c3201",
"6678eb77e9c933a578baf7cd",
"6678eb77b1a37c6ba03f86f6",
"6678eb7bd153609cf65c3222",
"6678eb7cb1a37c6ba03f8702",
"6678eb83e9c933a578baf7ec",
"6678eb88e9c933a578baf7f8",
"6678eb88b1a37c6ba03f8721",
"6678eb88d153609cf65c3241",
"6678eb885e7e585a50dcbce5",
"6678eb88e9c933a578baf7f9",
"6678eb88b1a37c6ba03f8722",
"6678eb885e7e585a50dcbce6",
"6678eb88e9c933a578baf7fa",
"6678eb8ad153609cf65c3246",
"6678eb8c5e7e585a50dcbcef",
"6678eb8ce9c933a578baf803",
"6678eb8cb1a37c6ba03f872c",
"6678eb8cd153609cf65c324c",
"6678eb8c5e7e585a50dcbcf0",
"6678eb8ce9c933a578baf804",
"6678eb8db1a37c6ba03f872d",
"6678eb8dd153609cf65c324d",
"6678eb8d5e7e585a50dcbcf1",
"6678eb8de9c933a578baf805",
"6678eb8dd153609cf65c324e",
"6678eb2b5e7e585a50dcbbfa",
"6678eb2be9c933a578baf70e",
"6678eb2bb1a37c6ba03f8637",
"6678eb2bd153609cf65c3155",
"6678eb2b5e7e585a50dcbbfb",
"6678eb2ce9c933a578baf70f",
]

final_results = process_payg_workflow(
    product_qid="PT001885", 
    product_ids=all_product_ids
)

print("\nFINAL RESULTS:")
for item in final_results:
    print(item)
