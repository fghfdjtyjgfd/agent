import pandas as pd

sheet_name = 'Agent' # replace with your own sheet name
sheet_id = '1QXAKFfXR8oBMXL_mVJx3SkqEpN0qIRG5davdcwCq1-0' # replace with your sheet's ID
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

def is_agent(fullname: str, prefixes: list) -> bool:
    normalized_fullname = fullname.replace(" ", "").lower()
    return any(prefix.replace(" ", "").lower() in normalized_fullname for prefix in prefixes)

agent_list = pd.read_csv(url)

agent_name_list = agent_list['agent name'].dropna().str.lower().tolist()
prefix_name = agent_list['prefix_name'].dropna().str.lower().tolist()
owner_pharses = agent_list['owner_pharses'].dropna().str.lower().tolist()
agent_pharses = agent_list['agent_pharses'].dropna().str.lower().tolist()

# print(len(agent_name_list))
# print(len(prefix_name))
# print(len(owner_pharses))
# print(len(agent_pharses))