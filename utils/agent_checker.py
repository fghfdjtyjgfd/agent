import os
from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd
from .agent_names import owner_pharses, agent_pharses
from .welcome_agent import welcome_agent_combinations

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
    if any(keyword.lower() in content for keyword in welcome_agent_combinations):
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