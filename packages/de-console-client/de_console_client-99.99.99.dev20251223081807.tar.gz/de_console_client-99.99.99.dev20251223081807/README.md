# Chromia Console Client

A Python client library for interacting with the Chromia Console Vector Database API. This client provides a simple and type-safe way to manage vector collections, perform similarity searches, and work with embeddings.


## Installation

```bash
pip install de_console_client
```

## Quick Start

```python
from de_console_client import Configuration, ApiClient, ChromiaVectorDBApi
from de_console_client.models import VectorCollection

# 1. Configure the client
configuration = Configuration(
    host='https://api.app.deconsole.com',
    brid='YOUR_BLOCKCHAIN_RID',
    network='mainnet',  # or 'testnet' or 'https://node0.testnet.chromia.com'
    chromia_api_key='YOUR_API_KEY'
)

# 2. Create the API client
with ApiClient(configuration) as api_client:
    client = ChromiaVectorDBApi(api_client)
    
    # 3. Create a collection
    collection = VectorCollection(
        name='my_first_collection',
        dimension=384,  # Vector dimension for embeddings
        index='hnsw_cosine',
        query_max_vector=10,
        store_batch_size=100
    )
    client.add_collection(collection)
    
    # 4. Store some text as vector embeddings (batch operation)
    client.create_vector_embedding_batch(
        'my_first_collection',
        [
            'The quick brown fox jumps over the lazy dog',
            'Chromia is a relational blockchain platform',
            'Vector databases enable semantic search'
        ]
    )
    
    # 5. Search using text query
    search_results = client.search_objects(
        collection='my_first_collection',
        body='tell me about Chromia',
        max_vectors=2       # return top 2 results
    )
    
    print('Search results:', search_results.payloads)
```

## Configuration

The `Configuration` object accepts the following parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `host` | str | Yes | Base URL of the Chromia Console API |
| `brid` | str | Yes | Blockchain RID (Identifier) |
| `network` | str | Yes | Network name (e.g., 'mainnet', 'testnet') or url|
| `chromia_api_key` | str | Yes | API key for authentication |

### Environment Variables

You can use environment variables to configure the client:

```python
import os
from de_console_client import Configuration

configuration = Configuration(
    host=os.getenv('CHROMIA_CONSOLE_BASE_PATH'),
    brid=os.getenv('BRID'),
    network=os.getenv('NETWORK', 'mainnet'),
    chromia_api_key=os.getenv('API_KEY')
)
```


## File storage quickstart

```python
import base64
import os
from de_console_client import Configuration, ApiClient, ChromiaFileStorageApi
from de_console_client.models import (
    UploadFileRequest,
    UploadFileBatchRequest,
    DeleteFileBatchRequest,
    DownloadFileBatchRequest
)

# Configuration
configuration = Configuration(
    host='https://api.app.deconsole.com',
    brid='YOUR_BLOCKCHAIN_RID',  # Replace with your blockchain RID
    network='testnet',  # or 'mainnet'
    chromia_api_key='YOUR_API_KEY'  # Replace with your API key
)

# Create API client
with ApiClient(configuration) as api_client:
    client = ChromiaFileStorageApi(api_client)

    # 1. GET USER FILES
    response = client.get_user_files()
    print(f"Retrieved {len(response.files)} file(s)")

    if response.files:
        for idx, file in enumerate(response.files, 1):
            print(f"\n  File {idx}:")
            print(f"    Name: {file.name}")
            print(f"    Hash: {file.file_hash}")
            print(f"    Size: {file.size} bytes" if hasattr(file, 'size') else "    Size: N/A")
            print(f"    Public: {file.is_public}" if hasattr(file, 'is_public') else "    Public: N/A")

    # 2. UPLOAD FILE (JSON with Base64)
    test_content = "Hello, Chromia File Storage! This is a test file!"
    test_filename = "test_file2.txt"
    # Encode to base64
    encoded_data = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
    upload_request = UploadFileRequest(
        name=test_filename,
        data=encoded_data,
        is_public=True
    )
    response = client.upload_file(upload_request)
    print(f"  File Hash: {response.file_hash}")
    uploaded_file_hash = response.file_hash


    # 3. UPLOAD FILE (Multipart)
    multipart_filename = "test_multipart.txt"
    multipart_content = "This file was uploaded using multipart/form-data!"
    temp_file_path = multipart_filename
    with open(temp_file_path, 'w') as f:
        f.write(multipart_content)

    with open(temp_file_path, 'rb') as f:
        file_data = f.read()

    # Upload using multipart - expects tuple of (filename, bytes)
    response = client.upload_file_multipart(
        file=(multipart_filename, file_data)
    )
    print(f"  File Hash: {response.file_hash}")
    multipart_file_hash = response.file_hash


    # 4. DOWNLOAD FILE (Multipart)
    response = client.download_file(multipart_file_hash)
    print(f"  File Name: {response.name}")
    print(f"  File Hash: {response.file_hash}")
    print(f"  File Size: {response.size}")
    print(f"  File Type: {response.content_type}")


    # 5. DOWNLOAD FILE CONTENT (Raw)
    response = client.download_file_content_without_preload_content(multipart_file_hash)
    print(f"  Status Code: {response.status}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")


    # 6. UPLOAD FILES BATCH
    files_to_upload = [
        {
            "name": "batch_file_1.txt",
            "content": "This is batch file 11",
            "is_public": False
        },
        {
            "name": "batch_file_2.txt",
            "content": "This is batch file 22",
            "is_public": False
        }
    ]

    upload_requests = []
    for file_info in files_to_upload:
        encoded_data = base64.b64encode(file_info["content"].encode('utf-8')).decode('utf-8')
        upload_requests.append(
            UploadFileRequest(
                name=file_info["name"],
                data=encoded_data,
                is_public=file_info["is_public"]
            )
        )

    batch_request = UploadFileBatchRequest(files=upload_requests)
    response = client.upload_file_batch(batch_request)
    print(response)


    # 7. DOWNLOAD FILES BATCH
    batch_file_hashes = ['file hash 1', 'file hash 2..']
    batch_request = DownloadFileBatchRequest(file_hashes=batch_file_hashes)
    response = client.download_file_batch(batch_request)
    print(f"Batch download completed! {len(response.files)} file(s) downloaded")

    # # 8. DELETE FILE
    uploaded_file_hash = 'file hash to delete..'
    response = client.delete_file(uploaded_file_hash)
    print(response)

    # 9. DELETE FILES BATCH
    batch_file_hashes = ['file hash 1', 'file hash 2...']
    batch_request = DeleteFileBatchRequest(file_hashes=batch_file_hashes)
    response = client.delete_file_batch(batch_request)
    print(response)

```


## API Reference

### File storage operations

- `get_user_files()` Get user files
- `upload_file(upload_file_request)` - Upload a file
- `upload_file_batch(upload_file_batch_request)` - Upload multiple files in batch
- `upload_file_batch_multipart(files)` - Upload a files in batch using multipart form data
- `upload_file_multipart(file)` - Upload a file using multipart form data
- `download_file(file_hash)` - Download a file
- `download_file_batch(download_file_batch_request)` - Download multiple files in batch
- `download_file_content(file_hash)` - Download raw file content
- `delete_file(file_hash)` - Delete a file
- `delete_file_batch(delete_file_batch_request)` - Delete multiple files in batch

### Entity DB operations

- `create_record(entity_name, obj)` Create a new record in an entity
- `delete_record_by_id(entity_name, id)` Delete a record by ID
- `get_record_by_id(entity_name, id)` Get a specific record by ID
- `get_records(entity_name)` Get all records from an entity
- `get_records_by_ids(entity_name, ids)` Get a list of records by IDs
- `update_record_by_id(entity_name, id, obj)` Update a record by ID

### Collection Management

- `get_collections()` - Get all available collections
- `add_collection(collection)` - Create a new collection
- `change_collection(changes)` - Update collection configuration
- `remove_collection(name)` - Remove a collection

### Vector Operations

- `create_vector(collection, vector_request)` - Create a single vector
- `create_vector_batch(collection, batch_request)` - Create multiple vectors
- `create_vector_batch_chunked(collection, batch_request)` - Create vectors in chunks
- `delete_vector(collection, payload)` - Delete a vector
- `delete_vector_batch(collection, payloads)` - Delete multiple vectors

### Embedding Operations

- `create_vector_embedding(collection, payload)` - Create text embedding
- `create_vector_embedding_batch(collection, payloads)` - Create text embeddings batch
- `create_vector_embedding_batch_chunked(collection, payloads)` - Create text embeddings in chunks
- `create_image_embedding(collection, image_request)` - Create image embedding
- `create_image_embedding_batch(collection, batch_request)` - Create image embeddings batch

### Search Operations

- `search_objects(collection, query, max_distance=None, max_vectors=None)` - Search by text
- `get_closest_objects(collection, vector_request, max_distance=None, max_vectors=None)` - Search by vector
- `get_closest_objects_with_distance(collection, vector_request, max_distance=None, max_vectors=None)` - Search with distances
- `get_closest_objects_with_filter(collection, filter_request, max_distance=None, max_vectors=None)` - Search with filter
- `search_images(collection, image_request, max_distance=None, max_vectors=None)` - Search similar images

### Import Operations

- `get_default_data_with_embedding()` - Get default import data
- `import_default_data(collection)` - Import default data

## Response Types

### TransactionResultBody

All write operations return a `TransactionResultBody`:

```python
{
    'tx_rid': str,         # Transaction ID
    'status': str,         # 'confirmed', 'waiting', 'pending', or 'rejected'
    'reject_reason': str   # Only present if status is 'rejected' (optional)
}
```

### GetClosestResponse

Search operations return a `GetClosestResponse`:

```python
{
    'payloads': [str]      # Array of matched payloads
}
```

### PayloadDistance

Distance-aware searches return `List[PayloadDistance]`:

```python
{
    'text': str,           # Payload text
    'distance': float      # Distance from query vector
}
```

## Error Handling

The client uses standard Python exceptions. Handle errors using try-except:

```python
from de_console_client import ApiClient, ChromiaVectorDBApi, Configuration
from de_console_client.rest import ApiException

configuration = Configuration(
    host='https://api.app.deconsole.com',
    brid='YOUR_BLOCKCHAIN_RID',
    network='mainnet',
    chromia_api_key='YOUR_API_KEY'
)

try:
    with ApiClient(configuration) as api_client:
        client = ChromiaVectorDBApi(api_client)
        response = client.create_vector(
            'my_collection',
            vector_request
        )
        print('Success:', response)
except ApiException as e:
    # API-specific error occurred
    print(f'API Exception: {e.status}')
    print(f'Reason: {e.reason}')
    print(f'Body: {e.body}')
except Exception as e:
    # General error occurred
    print(f'Error: {str(e)}')
```
