import pandas as pd
import re

def clean_snippet(snippet: str) -> str:
    """
    Cleans legal text snippets for database insertion by:
    - Removing <ref> and <match> tags
    - Preserving inner text
    - Normalizing whitespace
    """

    if not snippet:
        return ""

    # Remove opening/closing ref and match tags but keep content
    cleaned = re.sub(r"</?(ref|match)>", "", snippet)

    # Collapse multiple spaces/newlines
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Trim leading/trailing whitespace
    return cleaned.strip()


class CaseCitations:
    def __init__(self, data: dict):

        self.type = [i.get('type') for i in data]
        self.id = [i.get('id') for i in data]
        self.strength = [i.get('strength') for i in data]
        self.count = [i.get('count') for i in data]
        self.cited_as = [i.get('cited_as') for i in data]
        self.jurisdiction = [i.get('jurisdiction') for i in data]
        self.snippet = [clean_snippet(i.get('snippet')) for i in data]
        self.treatment = [i.get('treatment') for i in data]
        target = [i.get('target') for i in data]
        source = [i.get('source') for i in data]
        self.source_id = [i.get('id') for i in source]
        self.source_title = [i.get('title') for i in source]
        self.source_published = [i.get('published_at') for i in source]
        self.target_title = [i.get('title') for i in source]
        self.target_published = [i.get('published_at') for i in source]
        self.target_id = [i.get('id') for i in target]


        self.data_dict = { 
            'type': self.type,
            'id': self.id,
            'strength': self.strength,
            'count': self.count,
            'cited_as': self.cited_as,
            'jurisdiction': self.jurisdiction,
            'snippet': self.snippet,
            'treatment': self.treatment,
            'source_id': self.source_id,
            'source_title': self.source_title,
            'source_published': self.source_published,
            'target_id': self.target_id,
            'target_title': self.target_title,
            'target_published': self.target_published


        }


        self.as_dataframe = pd.DataFrame(self.data_dict)




class UserHistory:
    def __init__(self, data: list[dict]):
        rows = []

        for convo in data:
            skill = convo.get("skill")
            question = convo.get("question")
            conversationId = convo.get("conversationId")

            tasks = convo.get("tasks") or []
            for task in tasks:
                if not isinstance(task, dict):
                    continue

                task_id = task.get("task_id")

                t = task.get("text")
                if isinstance(t, list):
                    text = ",".join(str(x) for x in t if x is not None)
                elif t is None:
                    text = ""
                else:
                    text = str(t)

                rows.append({
                    "skill": skill,
                    "question": question,
                    "conversationId": conversationId,
                    "task_id": task_id,
                    "text": text,
                })

        self.as_dataframe = pd.DataFrame(
            rows,
            columns=["skill", "question", "conversationId", "task_id", "text"]
        )



        # expose attributes via dot notation
        self.skill = self.as_dataframe["skill"].tolist()
        self.question = self.as_dataframe["question"].tolist()
        self.conversationId = self.as_dataframe["conversationId"].tolist()
        self.task_id = self.as_dataframe["task_id"].tolist()
        self.text = self.as_dataframe["text"].tolist()

        self.as_dataframe = pd.DataFrame(rows)
        self.as_dataframe["text"] = self.as_dataframe["text"].str.replace("\n", ": ", regex=False)
        self.as_dataframe["question"] = self.as_dataframe["question"].str.replace("\n", ": ", regex=False)