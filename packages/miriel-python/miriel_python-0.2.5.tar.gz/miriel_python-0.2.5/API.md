
## `class Miriel`

This class provides a Python interface to interact with the Miriel API. It includes methods to send queries, add documents, retrieve documents, and manage users.

### **Constructor**
```python
Miriel(api_key, base_url="https://api.miriel.ai")
```
- **Parameters**:
  - `api_key` (str): Your API key for authenticating requests.
  - `base_url` (str, optional): The base URL for the API (default: `"https://api.miriel.ai"`).

---

### **Methods**

#### `query(query, user_id, input_images=None)`
Sends a query to the API, with optional image inputs.

- **Parameters**:
  - `query` (str): The query text.
  - `user_id` (str, optional): The ID of the user sending the query.
  - `input_images` (list of str, optional): URLs of images to include in the query.
  - `response_format` (json of return format, optional): JSON format for the format of the llm_result.  note that must be in the following format: { 'name': 'type' } where type is ('string', 'integer', 'float', 'boolean', 'object', 'array')
      
- **Returns**:
  - `dict`: The response from the API.

---

#### `add_string_as_document(user_id, document, metadata=None, discoverable=True, grant_ids=["*"])`
Adds a string (document) as a new entry in the user's document collection.

- **Parameters**:
  - `document` (str): The string document to add.
  - `user_id` (str, optional): The ID of the user.
  - `metadata` (dict, optional): Additional metadata associated with the document.
  - `discoverable` (bool, optional): Indicates if the document should be discoverable by others (default: `True`).
  - `grant_ids` (list of str, optional): List of user IDs granted access to the document (default: `["*"]`).
  
- **Returns**:
  - `dict`: The response from the API.

---

#### `add_image_as_document(user_id, image_url, metadata=None, discoverable=True, grant_ids=["*"])`
Adds an image (specified by URL) as a new document in the user's collection.

- **Parameters**:
  - `image_url` (str): The URL of the image to add.
  - `user_id` (str, optional): The ID of the user.
  - `metadata` (dict, optional): Additional metadata for the image.
  - `discoverable` (bool, optional): Indicates if the image should be discoverable by others (default: `True`).
  - `grant_ids` (list of str, optional): List of user IDs granted access to the image (default: `["*"]`).
  
- **Returns**:
  - `dict`: The response from the API.

---

#### `get_document_by_id(user_id, document_id)`
Retrieves a document by its unique ID.

- **Parameters**:
  - `document_id` (str): The ID of the document to retrieve.
  - `user_id` (str, optional): The ID of the user requesting the document.
  
- **Returns**:
  - `dict`: The requested document data.

---

#### `get_monitor_sources(user_id)`
Fetches the sources being monitored for a specific user.

- **Parameters**:
  - `user_id` (str, optional): The ID of the user.
  
- **Returns**:
  - `dict`: The list of monitor sources.

---

#### `remove_all_documents(user_id)`
Removes all documents associated with the specified user.

- **Parameters**:
  - `user_id` (str, optional): The ID of the user.
  
- **Returns**:
  - `dict`: The response from the API confirming the removal of documents.

---

#### `get_users()`
Retrieves a list of all users in the system.

- **Parameters**: None.

- **Returns**:
  - `dict`: The list of users.

---

#### `delete_user(user_id)`
Deletes a user by their unique ID.

- **Parameters**:
  - `user_id` (str): The ID of the user to delete.
  
- **Returns**:
  - `dict`: The response from the API confirming the deletion of the user.

---

#### `get_graph_for_query(query, user_id)`
Retrieves a graph structure related to a specific query.

- **Parameters**:
  - `query` (str): The query to visualize.
  - `user_id` (str, optional): The ID of the user making the request.
  
- **Returns**:
  - `dict`: The graph data related to the query.

---

#### `get_docs_for_query(query, user_id)`
Retrieves documents related to a given query.

- **Parameters**:
  - `query` (str): The search query.
  - `user_id` (str, optional): The ID of the user making the query.
  
- **Returns**:
  - `dict`: The list of documents related to the query.
