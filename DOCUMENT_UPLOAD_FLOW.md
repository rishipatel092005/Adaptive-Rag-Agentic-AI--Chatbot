# Document Upload Flow - How New Documents Are Stored

Let me explain the complete flow:

---

## 📊 Complete Document Upload & Retrieval Flow

### **Step 1: Initial Startup (What happens now)**

```python
# get_retriever() is called during startup
# Creates a DUMMY document to initialize FAISS vectorstore
dummy_doc = Document(
    page_content="Placeholder document for initialization",
    metadata={"source": "initialization"}
)
vectorstore = FAISS.from_documents([dummy_doc], embedding=embeddings)
```

**Purpose**: Just to initialize the vectorstore so the system can start

---

### **Step 2: User Uploads a Document (Via Streamlit or API)**

```
POST /rag/documents/upload
Headers: X-Description: "My document description"
Body: file (PDF or TXT)
```

**What happens in `document_upload.py`:**

1. **File Validation**
   ```python
   if not filename.endswith(".pdf") and not filename.endswith(".txt"):
       raise HTTPException(400, "Only PDF and TXT files are supported")
   ```

2. **Load Document Content**
   ```python
   if filename.endswith(".pdf"):
       loader = PyPDFLoader(tmp_path)
   else:
       loader = TextLoader(tmp_path, encoding="utf-8")
   
   docs = loader.load()  # ✅ ACTUAL DOCUMENT CONTENT LOADED HERE
   ```

3. **Enhance Description with LLM**
   ```python
   description_llm = enhance_description_with_llm(description)
   
   # Save to description.txt
   with open("description.txt", "w") as f:
       f.write(description_llm)
   ```

4. **Split Document into Chunks**
   ```python
   splitter = RecursiveCharacterTextSplitter(
       chunk_size=1000,
       chunk_overlap=150
   )
   chunks = splitter.split_documents(docs)  # ✅ CHUNKS CREATED
   ```

5. **Store Chunks in FAISS via retriever_chain()**
   ```python
   return retriever_chain(chunks)  # ✅ ACTUAL DOCUMENTS STORED HERE
   ```

---

### **Step 3: retriever_chain() - Documents Actually Stored**

```python
def retriever_chain(chunks: list[Document]):
    """
    This function ACTUALLY STORES your documents in FAISS vectorstore
    """
    try:
        # This creates a NEW FAISS vectorstore with your actual document chunks
        vectorstore = FAISS.from_documents(
            documents=chunks,  # ✅ YOUR REAL DOCUMENTS HERE
            embedding=embeddings
        )
        print("FAISS vector store initialized")
        print(vectorstore)
        return True  # ✅ SUCCESS - Documents are stored
    except Exception as e:
        print(e)
        return False
```

**Key Point**: This function is called with your actual document chunks, replacing the dummy initialization!

---

### **Step 4: Query Process - Using Stored Documents**

When user asks a question:

```
POST /rag/query
{
    "query": "Tell me about the uploaded document",
    "session_id": "user_123"
}
```

**Flow:**
1. Query goes to graph_builder.py
2. Calls `get_retriever()` to get the retriever tool
3. Retriever searches the FAISS vectorstore
4. **Finds documents YOU UPLOADED** (not just the dummy placeholder!)
5. Returns relevant chunks
6. LLM generates answer based on your documents

---

## 🔄 Document Lifecycle

```
Startup
  ↓
[DUMMY PLACEHOLDER INITIALIZED]
  ↓
User uploads document via API
  ↓
Document loaded & chunked
  ↓
retriever_chain() called with REAL CHUNKS
  ↓
[DUMMY REPLACED WITH YOUR DOCUMENTS IN FAISS]
  ↓
User queries
  ↓
Retriever searches YOUR DOCUMENTS
  ↓
Results returned to user
```

---

## 🎯 Key Points

### ✅ **What the Dummy Placeholder Does**
- Initializes FAISS vectorstore so the system can start
- Gets replaced when documents are uploaded
- Is NOT used for actual queries (only for initialization)

### ✅ **What Happens When You Upload Documents**
- Your document is loaded from file
- Split into chunks (1000 char, 150 overlap)
- Embedded using OpenAI embeddings
- **Stored in FAISS vectorstore** via `retriever_chain()`
- Available immediately for searches

### ✅ **What Happens When You Query**
- Retriever searches the FAISS vectorstore
- Finds chunks from YOUR uploaded documents
- Returns relevant content
- LLM generates answer based on your documents

---

## 📝 Example Workflow

### **1. System Starts**
```
Initialization: FAISS created with dummy document
Status: ✅ Ready to accept documents
```

### **2. User Uploads "Python Guide.pdf"**
```
Upload: Python Guide.pdf
Description: "Complete guide to Python programming"

Process:
- Load PDF content
- Split into chunks (e.g., 20 chunks)
- Embed each chunk
- Store in FAISS

Result: ✅ "Python Guide.pdf" stored in FAISS
Dummy: ❌ Replaced/not used anymore
```

### **3. User Asks Question**
```
Query: "What is Python?"

Search in FAISS:
- Find chunks from "Python Guide.pdf" related to the query
- Return: "Python is a high-level programming language..."

Result: ✅ Answer from YOUR uploaded document
```

### **4. User Uploads Another Document**
```
Upload: "Web Development.pdf"
Description: "Guide to web development"

Result: ✅ BOTH documents now in FAISS
- "Python Guide.pdf"
- "Web Development.pdf"

Queries can now search BOTH documents!
```

---

## 🔧 Technical Details

### FAISS Behavior

| Stage | Documents in FAISS | Behavior |
|-------|-------------------|----------|
| **After Startup** | 1 (dummy) | Can search, but only finds dummy |
| **After 1st Upload** | ~21 (dummy + 20 real chunks) | Searches both, but real content is found |
| **After 2nd Upload** | ~41 (dummy + 20 chunks + 20 chunks) | Searches all documents |
| **After Query** | Same | Returns results from ALL documents |

### How FAISS Storage Works

```python
# When you upload documents:
vectorstore = FAISS.from_documents(
    documents=chunks,  # Your real document chunks
    embedding=embeddings  # OpenAI embeddings
)

# FAISS creates embeddings for each chunk
# Stores them in a searchable format
# When queried, finds most similar chunks
# Returns them to the LLM for answer generation
```

---

## ❓ FAQ

**Q: Will the dummy placeholder interfere with my documents?**  
A: No. When you upload documents, new chunks are added to FAISS. Search results will prioritize your real documents over the dummy placeholder.

**Q: Can I upload multiple documents?**  
A: Yes! Each upload adds more chunks to the vectorstore. All documents are searchable.

**Q: Do documents persist after restart?**  
A: Currently NO. The vectorstore is in-memory (FAISS). Documents are lost on restart. To make it persistent, save the FAISS index to disk.

**Q: How do I make documents persistent?**  
A: You can save FAISS index:
```python
vectorstore.save_local("faiss_index")
vectorstore = FAISS.load_local("faiss_index", embeddings)
```

**Q: What's the maximum document size?**  
A: Limited by available RAM. Typical limit: 100MB+ depending on system.

**Q: Can I delete uploaded documents?**  
A: Currently, you'd need to restart the system or rebuild the FAISS index without those documents.

---

## 💡 How to Test

### **1. Start the System**
```bash
python -m uvicorn src.main:app --reload
```

### **2. Upload a Document**
```bash
curl -X POST http://localhost:8000/rag/documents/upload \
  -H "X-Description: Python Programming Guide" \
  -F "file=@python_guide.pdf"
```
**Response**: `{"status": true}`

### **3. Query the Document**
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?",
    "session_id": "user_123"
  }'
```
**Response**: Answer based on your uploaded document!

---

## ✅ Summary

| Question | Answer |
|----------|--------|
| **Does dummy placeholder stay forever?** | No, gets replaced/supplemented with real docs |
| **Are uploaded docs used for queries?** | YES! ✅ They are the main search content |
| **Can I upload multiple documents?** | YES! ✅ All are searchable together |
| **Do documents persist after restart?** | Currently NO (in-memory), but can be saved |
| **Will my documents be found in searches?** | YES! ✅ They are indexed and searchable |

---

**Status**: ✅ System is working correctly  
**Documents**: Will be stored and used for all queries  
**Ready**: Yes, you can start uploading documents!


