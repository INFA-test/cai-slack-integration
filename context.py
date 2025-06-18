import os
import time
import re
from pinecone import Pinecone, ServerlessSpec
from docx import Document
import google.generativeai as genai


def sanitize_id(id_string):
    ascii_only = re.sub(r'[^\x00-\x7F]+', '_', id_string)
    clean_id = re.sub(r'[^a-zA-Z0-9_-]', '_', ascii_only)
    clean_id = re.sub(r'_+', '_', clean_id)
    clean_id = clean_id.strip('_')
    return clean_id


def create_index_pinecone(index_name: str):
    if index_name not in pc.list_indexes().names():
        print(f"Creating index with name: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=768,  # gemeini's text-embedding-004 uses 768 dims
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        # Wait for index to be ready
        while not pc.describe_index(index_name).status['ready']:
            print("Waiting for index to be ready...")
            time.sleep(1)
    else:
        print(f"Index with name: {index_name} already exists")
    
    index = pc.Index(index_name)
    return index


def create_embedding_for_all_files_and_store():
    if not os.path.exists(file_path):
        print(f"Directory {file_path} does not exist!")
        return
    
    docx_files = [f for f in os.listdir(file_path) if f.endswith('.docx')]
    print(f"Found {len(docx_files)} DOCX files: {docx_files}")
    
    for file in docx_files:
        doc_id = file.split('.')[0].strip()
        doc_path = os.path.join(file_path, file)
        print(f"Processing file: {file}")
        embed_and_store(doc_path, doc_id)


def embed_and_store(file_path, doc_id):
    try:
        # doc_id can only be ASCII for Pinecone IDs
        clean_doc_id = sanitize_id(doc_id)
        
        # read and chunk the document
        content = read_docx(file_path)
        if not content.strip():
            print(f"Warning: No content found in {file_path}")
            return
        
        chunks = split_into_chunks_with_overlap(content)
        print(f"Created {len(chunks)} chunks for document {doc_id}")
        
        # could increase it but kept it small to avoid rate limits
        batch_size = 5
        
        for batch_start in range(0, len(chunks), batch_size):
            batch_chunks = chunks[batch_start:batch_start + batch_size]
            
            try:
                vectors_to_upsert = []
                
                for i, chunk in enumerate(batch_chunks):
                    try:
                        # generate embedding for single chunk
                        result = genai.embed_content(
                            model="models/text-embedding-004",
                            content=chunk,
                            task_type="retrieval_document"
                        )
                        
                        chunk_id = f"{clean_doc_id}_{batch_start + i}"
                        vectors_to_upsert.append({
                            "id": chunk_id,
                            "values": result['embedding'],
                            "metadata": {
                                "doc_id": doc_id,
                                "chunk": chunk,
                                "chunk_index": batch_start + i
                            }
                        })
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"Error embedding chunk {batch_start + i}: {str(e)}")
                        continue
                
                # batch upsert to pinecone
                if vectors_to_upsert:
                    index.upsert(vectors_to_upsert)
                    print(f"Stored batch {batch_start//batch_size + 1} ({len(vectors_to_upsert)} chunks) for document '{doc_id}'")
                
                time.sleep(2)
                
            except Exception as e:
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    print(f"Rate limit hit for document {doc_id}. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                else:
                    print(f"Error processing batch for document {doc_id}: {str(e)}")
                    continue
        
        print(f"Successfully stored document '{doc_id}' in Pinecone.")
        
    except Exception as e:
        print(f"Error processing document {doc_id}: {str(e)}")


def read_docx(file_path):
    try:
        doc = Document(file_path)
        content = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                content.append(text)
        return " ".join(content)
    except Exception as e:
        print(f"Error reading DOCX file {file_path}: {str(e)}")
        return ""


def split_into_chunks_with_overlap(text, max_length=500, overlap=50):
    if not text.strip():
        return []
    
    # split by sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_length = len(sentence)
        
        if current_length + sentence_length <= max_length:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            if current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
            
            #new chunk with overlap
            overlap_sentences = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_sentences + [sentence]
            current_length = sum(len(s) for s in current_chunk)
    
    #last chunk
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks


def query_similar_chunks(query_text, top_k=5):
    """Query the index for similar chunks"""
    try:
        # generate embedding for query
        query_result = genai.embed_content(
            model="models/text-embedding-004",
            content=query_text,
            task_type="retrieval_query"
        )
        
        # search in Pinecone
        results = index.query(
            vector=query_result['embedding'],
            top_k=top_k,
            include_metadata=True
        )
        
        return results
    except Exception as e:
        print(f"Error querying: {str(e)}")
        return None


# keys and stuff 
PINECONE_API_KEY = "pcsk_Jh58L_Q9ZRnf7aDZ5HTiaNxHzLieydmA2VksBpXv8veWrna9ZzvoF1QBdcHxTxfsxgXpt" #get this from pincone once you create an account 
GOOGLE_API_KEY = "AIzaSyDlz1yQMxWfkYteOW3W4SDdgZi54BX6e-0"  # get this from your gemini studio

index_name = 'pokemon-gemini'  #index name on pinecone; replace with what you want 
file_path = os.path.join(os.getcwd(),"pokedoc")


pc = Pinecone(api_key=PINECONE_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

# create or get index
index = create_index_pinecone(index_name=index_name)

# Process all documents
print("Starting document processing with Google Gemini embeddings...")
create_embedding_for_all_files_and_store()
print("Document processing completed!")

# test query
print("\n--- Testing... ---")
question = "What are electric type Pokemon?"   #update as needed
query_results = query_similar_chunks(question)
if query_results:
    for match in query_results['matches']:
        print(f"Score: {match['score']:.4f}")
        print(f"Document: {match['metadata']['doc_id']}")
        print(f"Chunk: {match['metadata']['chunk'][:100]}...")
        print("---")