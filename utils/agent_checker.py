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
2. there is "Agent" in front of or behind the name of content writer for example
   ใหญ่ (Agent), (Agent อร), (Agent ปูน), อรวรรณ บุญลาภ Agent
3. there is a sentence รับฝากขาย-เช่า, รับจัดหาเช่า-ซื้อ, บริการฝากขาย ปล่อยเช่า, ที่ปรึกษาอสังหา, รับฝากปล่อยเช่า ซื้อขาย บ้าน คอนโด or any sentences that have same meaning

otherwise it not meet the condition just reply "status": "owner"
answer as JSON object.
"""

content = """
#ปล่อยเช่า Elio del moss พหลโยธิน 34 (พร้อมอยู่ 1 มิ.ย)
ใกล้ BTS เสนานิคม (นั่งวิน 10-15 บาท)
 ค่าเช่า 12,500 บาท/เดือน (ฟรีส่วนกลาง ที่จอดรถ)
1 ห้องนอน 1 ห้องนั่งเล่น ตึก A ชั้น 7 ขนาด 31 ตร.ม.
 เข้าอยู่ชำระ 3 เดือน แบ่งเป็นค่าเช่าล่วงห
ขออนุญาตให้สิทธิ์คนโอนจองก่อน
รับจองผ่านบัญชีเจ้าของห้องโดยตรง
มีเอกสารยืนยันเจ้าของห้อง สามารถขอเช็คได้
สอบถามข้อมูลเพิ่มเติม ติดต่อได้ที่
นายสมชาย สมหวัง

รับฝากขาย ที่ดิน ตึก คอนโด
Tel : 081-710-3257
Line ID : @286adfey
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