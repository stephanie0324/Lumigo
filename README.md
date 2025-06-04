<a name="readme-top"></a>

<h1 align="center"> KnowBot </h1>

<p align="center">
    <a href="https://github.com/FlagOpen/FlagEmbedding">
            <img alt="Build" src="https://img.shields.io/badge/Contribution-Welcome-lightblue">
    </a>
    <a href="https://github.com/stephanie0324/KnowBot/stargazers">
        <img alt="Build" src="https://img.shields.io/github/stars/stephanie0324/KnowBot.svg?color=yellow&style=flat&label=Stars&logoColor=white">
    </a>
    <a href="https://github.com/stephanie0324/KnowBot/forks">
        <img alt="badge" src="https://img.shields.io/github/forks/stephanie0324/KnowBot.svg?style=flat&label=Forks">
    </a>
    <a href="https://github.com/stephanie0324/KnowBot/issues">
        <img alt="badge" src="https://img.shields.io/github/issues/stephanie0324/KnowBot.svg?style=flat&label=Issues&color=lightpink">
    </a>
    <a href="https://github.com/stephanie0324/KnowBot/tree/main?tab=readme-ov-file#MIT-1-ov-file">
        <img alt="badge" src="https://img.shields.io/badge/Licence-MIT-lightgreen">
    </a>
</p>

<div align="center">
    <img src="" width=160, height=150>
    <p>
    This is a Q&A Chatbot built with RAG.
    <br>  
    Ask freely and get the most accurate information with link.
    <br>
    <h4 align="center">
    <p>
        <a href=#about-the-project>About</a> |
        <a href=#new-updates>News</a> |
        <a href="#project-lists">Projects</a> |
        <a href=#getting-started>Getting Started</a> |
        <a href=#usage>Usage</a> |
        <a href="#roadmap">Roadmap</a> |
        <a href="#contributing">Contributing</a> |
        <a href="#license">License</a> 
    </p>
  </h4>
  </p>
</div>

# About the project

> 🔍 Tech Stack  
>  Built with Streamlit, LangChain, MongoDB, and Google Vertex AI.

KnowBot is an interactive, intelligent RAG (Retrieval-Augmented Generation) chatbot designed to help users search, explore, and question academic documents with ease. It combines the power of semantic search, natural language understanding, and a user-friendly interface to deliver grounded, explainable answers.

It leverages:

🗃️ MongoDB for document storage and vector search  
🌐 HuggingFace Embeddings for semantic search  
🤖 Vertex AI for LLM-based summarization and QA  
🚀 GitLab for CI/CD, automates testing and deployment.

<div align="center">
  <p class="image-cropper">
    <img src="knowbot.gif" alt="KnowBot Interface" width="600"/>
  </p>
  <em>KnowBot Interface</em>
</div>

| Area                       | Description                                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| 🔍 **Search Panel**        | Input your question to search for semantically related academic documents.               |
| 📚 **Source Documents**    | Displays retrieved documents with LLM-generated summaries and buttons like “Add to Ref”. |
| 📌 **Reference Docs**      | Shows documents that are currently selected as references for answering your question.   |
| ❓ **Follow-up Questions** | Suggested next questions based on your current query and selected references.            |

### ✨ Key Features

- 📄 Semantic Search  
 Retrieve documents based on meaning—not just keywords.
<p align="center">
<img src="./img/model_structure_explain.gif" alt="drawing" width="400" height="200"/>
<br> The Implementation of RAG </br>

- 🧠 Reference-Based QA  
   Ask questions using only your selected source documents for grounded, reliable answers.
- 🧾 LLM-Powered Summaries  
  Automatically generate concise document overviews using Vertex AI.
- 🎛️ Intuitive UI  
  Search, preview, and manage documents through a clean and responsive interface.
- 💾 Persistent Storag  
  Save useful papers for future reference and reuse.
- 🧩 Modular Backen  
  Built for easy expansion—supports future integrations like PDFs, JSONs, and more.
- 🤝 Multi-Agent Read
  Engineered to support planning and coordination via LangGraph.

# New Updates

> 🎉 　 KnowBot is born on May 21, 2025

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Getting Started

> For data preparing and processing : [read here](README_DataProcess.md)

To deploy the application simply go to `deploy` folder.

1. Modify `.env` file

   - OPENAI_API_KEY
   - HOST_PORT
   - DEVICE

   (MONGODB related settings)

   - MONGODB_URI
   - MONGODB_NAME
   - COLLECTION
   - INDEX_NAME

2. Build image
   > [!INFO]
   > First build will always take longer to run

```
bash script/build-docker-image.sh
```

3. Start the application

```
docker-compose up -d
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

# License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Other Projects

- [LLM Projects](https://github.com/stephanie0324/Finetune_LLM)
- [Web-Scraping](https://github.com/stephanie0324/Web-Scraping-)
- [Machine Learning with me](https://github.com/stephanie0324/ML_practrice)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<h3 align="left">Connect with me:</h3>
<p align="left">
<a href="https://github.com/stephanie0324/" target="blank"><img align='center' src= "https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="steph0324"  /></a> <a href="https://www.facebook.com/profile.php?id=100005029028402&locale=zh_TW" target="blank"><img align="center" src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" alt="steph0324" /></a>
<a href="https://www.linkedin.com/in/stephanie-chiang-42100b165/" target="blank"><img align="center" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="steph0324"/></a>
<a href="https://www.instagram.com/yrs_2499?igsh=MXJ5MHNpc2ZxNHh5NA%3D%3D&utm_source=qr" target="blank"><img align="center" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" alt="steph0324" /></a>
<a href="https://www.youtube.com/channel/UCpIrOv7O2R7HfpCEMQEOOKQ" target="blank"><img align="center" src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="steph0324" /></a>
</p>
