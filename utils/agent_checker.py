import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd
from .agent_names import owner_pharses, agent_pharses

load_dotenv()

class CheckerResponse(BaseModel):
    status: str = Field(description="owner or agent")
    line_id: Optional[str] = Field(default=None, description="Line ID in the content if there is no line id reply None")

# ======================== Helper functions ==================================
def check_link_null(df: pd.DataFrame) -> pd.DataFrame:
    number_of_data_before_drop = len(df)
    number_null_before_drop = df['post_link'].isna().sum()

    print("\n")
    print(f"There are {number_null_before_drop} null values of {number_of_data_before_drop} data")
    df = df.dropna(subset=['post_link'])
    number_after_drop = len(df)

    print("============== After drop null values ===============")
    print(f"there are remain {number_after_drop} data\n")
    
    return df

def seeker_renter_split(df: pd.DataFrame) -> pd.DataFrame:
    seeker_df = df[df['content'].str.len() <= 150]
    renter_df = df[df['content'].str.len() > 150]
    null_df = df[df['content'].isnull() == True]

    seeker_df = pd.concat([seeker_df, null_df])

    print("------------------- Splitting data ------------------------")
    print(f"Seeker has {len(seeker_df)} data out of {len(df)} in total")
    print(f"Renter has {len(renter_df)} data out of {len(df)} in total")

    return seeker_df, renter_df

def check_content(content):
    content = content.replace("-", " ").lower()
    if 'co agent welcome' in content:
        return "agent"
    if any(keyword in content for keyword in owner_pharses):
        return "owner"
    if any(keyword in content for keyword in agent_pharses):
        return "agent"
    return "not sure"

def add_status(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['status'] = df['content'].apply(check_content)
    return df

# ======================== End Helper functions ===============================

llm = ChatOpenAI(model="gpt-4o-mini")

system_prompt = """
you are content reader assistant, your task is to read the content I provide
and analyze if it real estate agent or owner content
response in JSON format with these key and value
 - "status": owner or agent,
 - "line_id": string, Line ID in the content if there is no line id reply null

if there is "owner post, ยินดีรับ agent, agent welcome" in the content you have to response "status": "owner"
if the content meets one of the following conditions. it's considered as real estate agent content
and you have to reply "status": "agent"

1. there is a word Agent post, Co-agent welcome, welcome co-agent, ยินดีรับ Co-Agent, รับโคเอเจ้น in content
2. there is "Agent" or "AG" in front of or behind the name of content writer for example
   ใหญ่ (Agent), (Agent อร), (Agent ปูน), อรวรรณ บุญลาภ Agent, AG แอน, K.Atom/AG
3. there is a sentence รับฝากขาย-เช่า, รับจัดหาเช่า-ซื้อ, บริการฝากขาย ปล่อยเช่า, ที่ปรึกษาอสังหา, รับฝากปล่อยเช่า ซื้อขาย บ้าน คอนโด or any sentences that have same meaning

otherwise it not meet the condition just reply "status": "owner"
answer as JSON object.
"""

agent_prompt = """
You are classifying property listings.
If the post sounds like it's from a property agent or real estate company, return "agent".
If it's from a homeowner or landlord, return "owner".

response in JSON format with these key and value
 - "status": owner or agent,
 - "line_id": string, Line ID in the content if there is no line id reply null
"""

content = """
ให้เช่าคอนโด 
The Selected Kaset-Ngamwongwan
ตรงข้าม ม.เกษตร เฟอร์ครบ วิวสระ ชั้น 11 พร้อมอยู่
25 ตรม
ตึกดีโครงสร้างแน่น 
นิติดูแลดี 
ความปลอดภัยแน่นหนา
ไมโครเวฟ ทีวี ตู้เย็น เครื่องซักผ้า เครื่องทำน้ำอุ่น
สัญญาเช่า ขั้นต่ำ 2ปี
มัดจำ 2เดือน+1เดือน
ราคา 13,000 บาท
อยู่เกิน 2 ปี ลดเหลือ 12,000 บาท
ต้องการเฟอร์นิเจอหรืออุปกรณ์อำนวยความสะดวกเพิ่มเติมแจ้งเจ้าของก่อนเข้าอยู่ได้ค่ะ
Line : janthebabe
โทร 082-195-9955 
คุณจักร agent
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", agent_prompt),
        ("human", "{input}")
    ]
)
json_parser = JsonOutputParser(pydantic_object=CheckerResponse)

agent_checker = prompt | llm | json_parser

# print(check_content(content))
# print(agent_checker.invoke(content))