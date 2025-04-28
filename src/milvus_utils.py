import os

from langchain_community.document_loaders import PyPDFLoader
# from langchain_community.vectorstores import FAISS, Milvus
# from milvus import IndexType, MetricType, Milvus
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility


def process_and_upload(pdf_folder_path, embedding, collection_name, connection_args):
    # Connect to Milvus
    connections.connect(**connection_args)

    # Define the collection schema if not already defined
    collection = None

    if not utility.has_collection(collection_name):
        # Define the schema
        fields = [
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="page", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),
        ]
        schema = CollectionSchema(
            fields=fields, description="Onboarding documents collection"
        )
        collection = Collection(name=collection_name, schema=schema)
    else:
        collection = Collection(name=collection_name)
        # collection.load()

    # Load and process the PDF files
    documents = []
    for file in os.listdir(pdf_folder_path):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder_path, file)
            loader = PyPDFLoader(pdf_path)
            docs = loader.load_and_split()
            for page, doc in enumerate(docs):
                print(page, doc)
                # documents.append({
                #     "source": doc.metadata.get("source") or pdf_path,
                #     "page": page,
                #     "text": doc,
                #     "vector": embedding.embed_documents(doc.page_content)
                # })
                documents.append(
                    {
                        "source": doc.metadata.get("source"),
                        "page": doc.metadata.get("page"),
                        "text": doc.page_content,
                        "vector": embedding.embed_documents(doc.page_content),
                    }
                )

    # Extract sources to be deleted
    new_sources = [doc["source"] for doc in documents]

    # Delete existing documents for the same sources
    query_expr = f"source in {new_sources}"
    collection.delete(expr=query_expr)

    # Prepare data for insertion
    sources = [doc["source"] for doc in documents]
    pages = [doc["page"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    vectors = [doc["vector"] for doc in documents]

    # Insert the new data
    entities = [sources, pages, texts, vectors]  # source  # page  # text  # vector
    collection.insert(entities)

    # Optional: Create index
    index_params = {
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024},
        "metric_type": "L2",
    }
    collection.create_index(field_name="vector", index_params=index_params)

    return "Upload successful"


# pdf_folder_path = "./data"
# collection_name = os.getenv("MILVUS_COLLECTION")
# process_and_upload(pdf_folder_path, self.embedding, collection_name, self.connection_args)
