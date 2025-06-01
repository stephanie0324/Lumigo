import os
from pathlib import Path
from typing import TypedDict, List, Dict, Any

from langchain.agents import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# ======== 定義 Tools =========

@tool
def read_pdf(file_path: str) -> Dict[str, Any]:
    """Read a PDF file and return a dictionary with doc_id and content."""
    # 這裡模擬讀取 pdf 實際可換真實解析邏輯
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"doc_id": Path(file_path).stem, "content": content}

@tool
def read_json(file_path: str) -> Dict[str, Any]:
    """Read a JSON file and return a dictionary with doc_id and content."""
    import json
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"doc_id": Path(file_path).stem, "content": data}

# ======== LLM Controller =========

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def control_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    file_path = state["file_path"]
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return {"next_tool": "read_pdf", "file_path": file_path}
    elif ext == ".json":
        return {"next_tool": "read_json", "file_path": file_path}
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

# ======== 定義 Graph State =========

class FileState(TypedDict):
    file_path: str
    next_tool: str

def build_graph():
    builder = StateGraph(state_schema=FileState)
    builder.add_node("control", control_agent)
    builder.add_node("read_pdf", read_pdf)
    builder.add_node("read_json", read_json)

    builder.set_entry_point("control")
    builder.add_conditional_edges(
        "control",
        lambda state: state["next_tool"],
        {
            "read_pdf": "read_pdf",
            "read_json": "read_json",
        },
    )

    builder.add_edge("read_pdf", END)
    builder.add_edge("read_json", END)

    return builder.compile()

graph = build_graph()

# ======== 主程式，讀資料夾中所有檔案，呼叫 graph =========

if __name__ == "__main__":
    data_folder = "./data"
    results = []

    for filename in os.listdir(data_folder):
        filepath = os.path.join(data_folder, filename)
        print(f"Processing file: {filename}")
        try:
            # 進入 graph 執行流程
            result = graph.invoke({"file_path": filepath})
            results.append(result)
            print("Result:", result)
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("\nAll results:")
    print(results)
