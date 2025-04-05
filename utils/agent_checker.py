import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()

class CheckerResponse(BaseModel):
    status: str = Field(description="owner or agent")
    line_id: str = Field(description="Line ID in the content if there is no line id reply None")

llm = ChatOpenAI(model="gpt-4o-mini")

system_prompt = """
you are content reader assistant, your task is to read the content I provide
and analyze if it real estate agent or owner content
response in JSON format with these key and value
 - "status": owner or agent,
 - "line_id": string, Line ID in the content if there is no line id reply None

if there is "owner post" in the content you have to response "status": "owner"
if the content meets one of the following conditions. it's considered as real estate agent content
and you have to reply "status": "agent"

1. there is a word Agent post, Co-agent welcome, welcome co-agent, ยินดีรับ Co-Agent, รับโคเอเจ้น in content
2. there is "Agent" or "AG" in front of or behind the name of content writer for example
   ใหญ่ (Agent), (Agent อร), (Agent ปูน), อรวรรณ บุญลาภ Agent, AG แอน, K.Atom/AG
3. there is a sentence รับฝากขาย-เช่า, รับจัดหาเช่า-ซื้อ, บริการฝากขาย ปล่อยเช่า, ที่ปรึกษาอสังหา, รับฝากปล่อยเช่า ซื้อขาย บ้าน คอนโด or any sentences that have same meaning

otherwise it not meet the condition just reply "status": "owner"
answer as JSON object.
"""

content = """
ให้เช่าศุภาลัย ลอฟท์ @สถานีแคราย (Supalai Loft @Khaerai Station) #ใกล้MRTแคราย
🚩ค่าเช่า 6,500 บาท/เดือน 
รายละเอียด #S12
ชั้น 9 ขนาด 30 ตร.ม.
✅เฟอร์นิเจอร์ครบ
✅แอร์ 1 เครื่อง 
✅ตู้เย็น 
✅เครื่องทำน้ำอุ่น
🚘🛵จอดรถฟรี 2 คัน
👇🏻👇🏻👇🏻👇🏻
สอบถามเพิ่มเติม
📞065-5922254 (คุณแอน) AG
ID line : @paisitcenter
📌สิ่งอำนวยความสะดวก
โถงต้อนรับ,ห้องตู้จดหมาย,ฟิตเนส, สระว่ายน้ำ,สวนพักผ่อน,ที่จอดรถ, กล้องวงจรปิด,ระบบรักษาความปลอดภัยตลอด 24 ชม. 
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}")
    ]
)
json_parser = JsonOutputParser(pydantic_object=CheckerResponse)

agent_checker = prompt | llm | json_parser

res = agent_checker.invoke(content)
print(res)