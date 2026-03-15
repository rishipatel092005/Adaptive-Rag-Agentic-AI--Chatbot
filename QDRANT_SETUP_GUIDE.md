# Qdrant Setup Guide - Free Tier Account & API Keys

## 📋 Overview

This guide will walk you through setting up a **Qdrant** account with the free tier, creating a cluster, and obtaining the necessary API keys to use Qdrant as your vector database instead of FAISS.

---

## 🔍 What is Qdrant?

**Qdrant** is a high-performance vector database designed specifically for similarity search and AI applications. It provides:

- ✅ **Fast vector similarity search** (cosine, dot product, Euclidean)
- ✅ **Horizontal scalability** with distributed clusters
- ✅ **RESTful API** and multiple client libraries
- ✅ **Persistent storage** with backup/restore
- ✅ **Real-time updates** and filtering capabilities
- ✅ **Free tier** for development and small projects

---

## 🚀 Step 1: Create Qdrant Account

### **1.1 Visit Qdrant Cloud**
Navigate to: https://cloud.qdrant.io/

### **1.2 Sign Up**
1. Click **"Sign Up"** or **"Get Started"**
2. Choose your preferred sign-up method:
   - **GitHub** (recommended for developers)
   - **Google**
   - **Email**

### **1.3 Verify Email**
1. Check your email for verification link
2. Click the verification link
3. Complete your profile setup

---

## 💰 Step 2: Set Up Free Tier

### **2.1 Access Dashboard**
After verification, you'll be redirected to the Qdrant Cloud dashboard.

### **2.2 Create Your First Cluster**
1. Click **"Create cluster"** or **"New Cluster"**
2. Choose **"Free Tier"** plan
   - **Name**: `adaptive-rag-dev` (or your preferred name)
   - **Provider**: Choose the closest region (e.g., `AWS us-east-1`)
   - **Version**: Latest stable version

### **2.3 Configure Cluster**
```
Cluster Configuration:
├── Name: adaptive-rag-dev
├── Provider: AWS/GCP/Azure (choose closest)
├── Region: us-east-1 / eu-west-1 / etc.
├── Version: Latest (e.g., v1.9.x)
└── Plan: Free Tier
```

### **2.4 Create Cluster**
1. Review configuration
2. Click **"Create Cluster"**
3. Wait 2-5 minutes for provisioning

---

## 🔑 Step 3: Get API Keys

### **3.1 Access API Keys**
1. In your dashboard, go to **"API Keys"** section
2. Click **"Create API Key"**

### **3.2 Create API Key**
```
API Key Configuration:
├── Name: adaptive-rag-key
├── Permissions: Full Access (for development)
└── Expiration: Never (or set as needed)
```

### **3.3 Save Your Credentials**
After creation, you'll get:
- **API Key**: `your-api-key-here`
- **URL**: `https://your-cluster-id.aws-us-east-1.qdrant.io:6333`

**⚠️ IMPORTANT**: Save these credentials securely - you'll need them for your application!

---

## ⚙️ Step 4: Configure Your Application

### **4.1 Update Environment Variables**

Create or update your `.env` file:

```env
# Qdrant Configuration
QDRANT_URL=https://your-cluster-id.aws-us-east-1.qdrant.io:6333
QDRANT_API_KEY=your-api-key-here
QDRANT_CODE_COLLECTION=code_documents
QDRANT_DOCS_COLLECTION=documents
```

### **4.2 Verify Connection**

Test your Qdrant connection with a simple script:

```python
from qdrant_client import QdrantClient

# Test connection
client = QdrantClient(
    url="https://your-cluster-id.aws-us-east-1.qdrant.io:6333",
    api_key="your-api-key-here"
)

# List collections
collections = client.get_collections()
print("Connected successfully!")
print(f"Collections: {collections}")
```

---

## 🔄 Step 5: Switch from FAISS to Qdrant

### **5.1 Update retriever_setup.py**

Uncomment the Qdrant code and comment out FAISS:

```python
# In src/rag/retriever_setup.py

# Uncomment these lines:
from langchain_qdrant import QdrantVectorStore

# Comment out this line:
# from langchain_community.vectorstores import FAISS

# In retriever_chain() function:
# Uncomment:
vectorstore = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    collection_name=settings.CODE_COLLECTION,
)

# Comment out:
# vectorstore = FAISS.from_documents(
#     documents=chunks,
#     embedding=embeddings
# )

# In get_retriever() function:
# Uncomment:
vectorstore = QdrantVectorStore.from_documents(
    documents=[],
    embedding=embeddings,
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    collection_name=settings.CODE_COLLECTION,
)
retriever = vectorstore.as_retriever()

# Comment out the FAISS dummy creation code
```

### **5.2 Update Requirements**

Add Qdrant to your requirements.txt:
```txt
qdrant-client>=1.7.0
langchain-qdrant>=0.1.0
```

Install:
```bash
pip install qdrant-client langchain-qdrant
```

### **5.3 Test the Switch**

1. Restart your application
2. Upload a document
3. Query it to verify Qdrant is working

---

## 📊 Free Tier Limits & Features

### **Free Tier Specifications**
```
Storage: 1 GB
Vectors: 100,000 vectors
Collections: Unlimited
Requests: 1,000,000/month
Backup: Manual only
Support: Community
```

### **When to Upgrade**
Consider upgrading when you need:
- More storage (>1GB)
- Higher request limits
- Automatic backups
- Priority support
- Advanced features

---

## 🔧 Troubleshooting

### **Connection Issues**
```python
# Test connection
from qdrant_client import QdrantClient

try:
    client = QdrantClient(
        url="your-url",
        api_key="your-key"
    )
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

### **Common Errors**

#### **401 Unauthorized**
- Check your API key is correct
- Ensure the key has proper permissions
- Verify the key hasn't expired

#### **Connection Timeout**
- Check your internet connection
- Verify the URL is correct
- Try a different region if issues persist

#### **Collection Not Found**
- Ensure collection name matches
- Check if collection was created successfully
- Verify API key permissions

### **Performance Tips**
- Choose regions closest to your users
- Use appropriate vector dimensions
- Implement proper indexing strategies
- Monitor usage in Qdrant dashboard

---

## 📈 Scaling Up (When Needed)

### **Paid Plans**
```
Starter: $25/month
├── Storage: 10 GB
├── Vectors: 1M
└── Requests: 10M/month

Professional: $99/month
├── Storage: 100 GB
├── Vectors: 10M
└── Requests: 100M/month

Enterprise: Custom pricing
├── Unlimited storage
├── Advanced features
└── Dedicated support
```

### **Migration Strategy**
1. Export data from current vectorstore
2. Create new Qdrant cluster
3. Import data to Qdrant
4. Update application configuration
5. Test thoroughly before switching

---

## 🔐 Security Best Practices

### **API Key Management**
- Never commit API keys to version control
- Use environment variables
- Rotate keys regularly
- Use separate keys for different environments

### **Network Security**
- Use HTTPS for all connections
- Implement proper authentication
- Monitor access logs
- Set up alerts for unusual activity

### **Data Protection**
- Enable encryption at rest
- Implement proper backup strategies
- Use VPC peering for enhanced security
- Regular security audits

---

## 📚 Additional Resources

### **Official Documentation**
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Cloud Guide](https://qdrant.tech/documentation/cloud/)
- [API Reference](https://qdrant.tech/documentation/interfaces/)

### **LangChain Integration**
- [LangChain Qdrant](https://python.langchain.com/docs/integrations/vectorstores/qdrant)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)

### **Community Resources**
- [Qdrant Discord](https://qdrant.to/discord)
- [GitHub Issues](https://github.com/qdrant/qdrant/issues)
- [Blog & Tutorials](https://qdrant.tech/blog/)

---

## 🎯 Quick Setup Checklist

- [ ] Visit https://cloud.qdrant.io/
- [ ] Create account (GitHub/Google/Email)
- [ ] Verify email
- [ ] Create free tier cluster
- [ ] Get API key and URL
- [ ] Update .env file
- [ ] Test connection
- [ ] Switch code from FAISS to Qdrant
- [ ] Restart application
- [ ] Test document upload and queries

---

## 💡 Pro Tips

### **Development Setup**
- Use separate clusters for dev/staging/prod
- Set up monitoring and alerts
- Implement proper error handling
- Use environment-specific configurations

### **Performance Optimization**
- Choose optimal vector dimensions
- Implement proper indexing
- Use batch operations for large datasets
- Monitor query performance

### **Cost Management**
- Monitor usage in dashboard
- Set up billing alerts
- Clean up unused collections
- Use appropriate cluster sizes

---

## 🚀 Next Steps

1. **Set up your Qdrant account** using this guide
2. **Get your API credentials**
3. **Update your application configuration**
4. **Switch from FAISS to Qdrant** in the code
5. **Test thoroughly** with document uploads and queries
6. **Monitor performance** in the Qdrant dashboard

---

## 📞 Support

If you encounter issues:
1. Check the [Qdrant Status Page](https://status.qdrant.io/)
2. Review the [Troubleshooting Guide](https://qdrant.tech/documentation/guides/troubleshooting/)
3. Join the [Qdrant Discord](https://qdrant.to/discord)
4. Open issues on [GitHub](https://github.com/qdrant/qdrant/issues)

---

## ✅ Summary

**Qdrant Free Tier Setup:**
- ✅ Create account at cloud.qdrant.io
- ✅ Set up free cluster (1GB storage, 100K vectors)
- ✅ Generate API key
- ✅ Configure application
- ✅ Switch from FAISS to Qdrant
- ✅ Test functionality

**Benefits of Qdrant:**
- ✅ Production-ready vector database
- ✅ Scalable and performant
- ✅ RESTful API
- ✅ Free tier for development
- ✅ Enterprise features available

---

**Your Qdrant setup is now complete!** 🎉

**Ready to switch from FAISS to production-ready vector storage!** 🚀

---

**Date**: March 9, 2026  
**Guide Version**: 1.0  
**Status**: ✅ Complete and Ready to Use
