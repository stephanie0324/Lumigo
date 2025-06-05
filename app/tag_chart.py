import os
from collections import Counter
import matplotlib.pyplot as plt
from pymongo import MongoClient
from dotenv import load_dotenv
from config import settings


# 連接 MongoDB
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_NAME]
collection = db[settings.COLLECTION]

# 取得所有 tags
all_tags = []
for doc in collection.find({}, {"tags": 1}):
    tags = doc.get("tags", [])
    all_tags.extend(tags)

# 計算 tag 出現次數
tag_counts = Counter(all_tags)
most_common_tags = tag_counts.most_common(20)  # 前 20 名 tag

# 畫出 bar chart
tags, counts = zip(*most_common_tags)
plt.figure(figsize=(12, 6))
plt.bar(tags, counts, color='skyblue')
plt.xticks(rotation=45, ha='right')
plt.xlabel("Tags")
plt.ylabel("Count")
plt.title("Top 20 Most Common Tags")
plt.tight_layout()
plt.savefig("tag_chart.png")
plt.show()
