<a name="readme-top"></a>

<h1 align="center"> Lumigo: A Q&A Chatbot for Academic Document Exploration </h1>

<p align="center">
    <a href="https://github.com/FlagOpen/FlagEmbedding">
            <img alt="Build" src="https://img.shields.io/badge/Contribution-Welcome-lightblue">
    </a>
    <a href="https://github.com/stephanie0324/Lumigo/stargazers">
        <img alt="Build" src="https://img.shields.io/github/stars/stephanie0324/Lumigo.svg?color=yellow&style=flat&label=Stars&logoColor=white">
    </a>
    <a href="https://github.com/stephanie0324/Lumigo/forks">
        <img alt="badge" src="https://img.shields.io/github/forks/stephanie0324/Lumigo.svg?style=flat&label=Forks">
    </a>
    <a href="https://github.com/stephanie0324/Lumigo/issues">
        <img alt="badge" src="https://img.shields.io/github/issues/stephanie0324/Lumigo.svg?style=flat&label=Issues&color=lightpink">
    </a>
    <a href="https://github.com/stephanie0324/Lumigo/tree/main?tab=readme-ov-file#MIT-1-ov-file">
        <img alt="badge" src="https://img.shields.io/badge/Licence-MIT-lightgreen">
    </a>
</p>
<div align="center">

  <p>This is a chatbot built with Retrieval-Augmented Generation (RAG) for in-depth semantic search across research papers and theses.</p>

  <p>Ask freely — Lumigo will return grounded answers with trusted reference documents.</p>

  <p>
    🌐 <a href="https://lumigo-service-flkbnf43xq-uc.a.run.app" target="_blank"><strong>Live Demo</strong></a>
  </p>

  <br>

  <h4>
    <a href="#about-the-project">About</a> |
    <a href="#new-updates">News</a> |
    <a href="#project-lists">Projects</a> |
    <a href="#getting-started">Getting Started</a> |
    <a href="#usage">Usage</a> |
    <a href="#roadmap">Roadmap</a> |
    <a href="#contributing">Contributing</a> |
    <a href="#license">License</a>
  </h4>

</div>

# About the project

> 🔍 Tech Stack  
>  Built with Streamlit, LangChain, MongoDB, and Google Vertex AI.

**Lumigo** is an intelligent academic research assistant powered by Retrieval-Augmented Generation (RAG). Designed for precision and explainability, it helps users **search**, **explore**, and **question academic documents** with context awareness.

Unlike generic RAG systems, **Lumigo** supports **document-specific queries**, generates **follow-up questions**, and provides **transparent source attribution** for all responses. It also features a **Thesis Fallback Retrieval Module** that automatically searches and incorporates **open-access academic theses** when internal documents are insufficient, enriching the knowledge base dynamically. Leveraging **MongoDB**, **HuggingFace Embeddings**, and **Vertex AI**, it delivers semantically grounded insights through a clean, interactive UI.

Lumigo is ideal for researchers, students, and professionals navigating complex literature with a focus on rigor and clarity.

It leverages:

🗃️ MongoDB for document storage and vector search  
🌐 HuggingFace Embeddings for semantic search  
🤖 Vertex AI for LLM-based summarization and QA  
🚀 GitLab for CI/CD, automates testing and deployment.

<div align="center">
  <p class="image-cropper">
    <img src="Lumigo.gif" alt="Lumigo Interface" width="600"/>
  </p>
  <em>Lumigo Interface</em>
</div>

| Area                       | Description                                                                                                                |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 🔍 **Search Panel**        | Input your research question to perform **semantic academic search** across indexed papers.                                |
| 📚 **Source Documents**    | Displays retrieved academic documents with **LLM-generated summaries** and an “Add to Ref” button for selective reference. |
| 📌 **Reference Docs**      | Lists documents you've selected as references. These are used to generate answers and offer **traceable, cited content**.  |
| ❓ **Follow-up Questions** | Suggests relevant follow-up research questions based on your current query and selected references.                        |

## ✨ Key Features

- **Document Ingestion Module**: Supports loading academic documents in JSON and PDF formats. Upon ingestion, documents undergo chunking based on fixed character counts to create manageable text segments.
- **Metadata Tagging Module**: Enriches each text chunk with relevant metadata, including document title, section headers, file source, and author details, enabling precise context retrieval and transparent source attribution.
- **Summarization Module**: Utilizes Vertex AI large language models to generate concise summaries for each chunk, improving document preview capabilities and supporting efficient user exploration.
- **Embedding and Indexing Module**: Employs HuggingFace embedding models to convert each chunk into dense semantic vectors. These embeddings, alongside metadata, are stored in MongoDB Atlas configured with vector search indexes. This supports rapid similarity queries that drive Lumigo’s semantic search.
- **Retrieval-Augmented Generation (RAG) Module**: Combines retrieved document chunks with large language models to generate contextually grounded, explainable answers. Users can interactively select which reference documents to include, ensuring transparency and control over the sources informing responses.
- **Thesis Auto-Retrieval Fallback**: When internal search returns no results, Lumigo automatically fetches related research papers using CrossRef and Open Access Button APIs. It downloads PDF files, extracts and summarizes their content using Vertex AI, and stores them in the vector database — fully autonomously.
  - 📄 Each PDF is saved with a **sanitized title** for traceability.
  - 🗂️ Downloaded files are saved in a **temporary, isolated subfolder** per request to avoid conflicts under async execution.
  - 🧹 After ingestion, all files are automatically deleted from disk.
- **Analytics Dashboard**: A new page that displays the most frequently searched topics and documents, providing insights into research trends, with interactive filters.

<p align="center">
<img src="./img/model_structure_explain.gif" alt="drawing" width="400" height="200"/>
<br> The Implementation of RAG </br>

- **User Interface Module**: Provides a responsive, user-friendly frontend where users can perform semantic searches, view document previews and summaries, manage reference documents, and pose targeted questions. The interface emphasizes clarity and traceability, with explicit source citations for all generated answers.
- **CI/CD Pipeline**: GitLab pipelines automate testing, building, and deployment, ensuring continuous integration and delivery for robust development workflows.

---

# New Updates

> 🎉 　 Lumigo is born on May 21, 2025

## 🆕 Recent Updates

- **2025/06/29** – Added fallback module for automatic academic document retrieval via **CrossRef + Open Access API**. When no related documents are found in the internal DB, Lumigo now searches, downloads, summarizes, and appends up to 5 papers directly into the vector DB.
- **2025/06/24** – `Analytics Dashboard` is now available with interactive filters for top queries and documents!
- **2025/06/22** – `Chat History` is now available.

<details>
  <summary>📜 Timeline (older updates)</summary>

- **2025/06/15** – Added **Multi-Agent** workflow for better search and query expansion.
- **2025/06/05** – Integrated **Vertex AI** as our model inference backend.
- **2025/05/27** – Added PDF reader, footnotes, and reference support for better search.

</details>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🚀 Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/stephanie0324/Lumigo.git
   cd Lumigo
   ```

2. Install dependencies:

   ```bash
   bash script/build-docker-image.sh
   ```

3. Set up your `.env` file:

   - The `.env` file is under `deploy/` folder
   - Fill in the required keys:
     - `MONGODB_URI`
     - `MONGODB_NAME`
     - `COLLECTION`
     - `INDEX_NAME`
     - `OPENAI_API_KEY`
     - `VERTEX_PROJECT_ID`
     - `VERTEX_LOCATION`
     - `VERTEX_MODEL_NAME`
     - `GOOGLE_APPLICATION_CREDENTIALS` (credential filepath)

4. Launch the app:

   ```bash
   cd deploy
   docker-compose up -d

   # for development
   bash script/run-dev-mode.sh
   streamlit run main.py --server.port=7860
   ```

   > [! Note]
   > Prod Mode (docker compose): the credential.json should be in the `deploy/` folder
   > Dev Mode: the credential file under `src/` folder

---

## 🛠️ How to Use

1. **Search for academic content**  
   Enter your question in the search panel. The system performs semantic search over ingested JSON/PDF documents.

2. **Explore and select references**  
   Browse the retrieved documents and their AI-generated summaries. Choose relevant ones by clicking **"Add to Ref"**.

3. **Ask your question**  
   With references selected, ask a question. The system uses only those documents to generate accurate, grounded answers.

4. **View source and follow-ups**  
   Check the sources of the answer, and explore suggested follow-up questions to continue your research.

> 💡 Tip: If your query returns no results from internal documents, Lumigo will automatically search for new open-access papers to fill the gap.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

# License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Other Projects

- [Microsoft 2025 LLM Agent Hackathon](https://github.com/stephanie0324/llm-agent-hack)
- [LLM-RAG-UniApply](https://github.com/stephanie0324/LLM_RAG_UniApply)
- [LLM_Projects](https://github.com/stephanie0324/LLM_Projects)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<h3 align="left">Connect with me:</h3>
<p align="left">
<a href="https://github.com/stephanie0324/" target="blank"><img align='center' src= "https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="steph0324"  /></a> <a href="https://www.facebook.com/profile.php?id=100005029028402&locale=zh_TW" target="blank"><img align="center" src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" alt="steph0324" /></a>
<a href="https://www.linkedin.com/in/stephanie-chiang-42100b165/" target="blank"><img align="center" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="steph0324"/></a>
<a href="https://www.instagram.com/yrs_2499?igsh=MXJ5MHNpc2ZxNHh5NA%3D%3D&utm_source=qr" target="blank"><img align="center" src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" alt="steph0324" /></a>
<a href="https://www.youtube.com/channel/UCpIrOv7O2R7HfpCEMQEOOKQ" target="blank"><img align="center" src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="steph0324" /></a>
</p>
