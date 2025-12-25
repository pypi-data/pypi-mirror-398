import pandas as pd
import asyncio
import aiohttp
from fudstop4.apis.polygonio.polygon_options import PolygonOptions
from .models import CaseCitations, UserHistory
db = PolygonOptions()




class VlexSDK:
    def __init__(self, cookie:str):
        self.cookie=cookie




    async def get_user_history(self):
        await db.connect()
        url = f"https://us-vincent.vlex.com/user_history/"


        async with aiohttp.ClientSession(headers={'cookie': self.cookie}) as session:
            async with session.get(url) as response:
                data = await response.json()
                items = data['items']
                data = UserHistory(items)

                await db.batch_upsert_dataframe(data.as_dataframe, table_name='vlex_user_history', unique_columns=['task_id'])

                return data
            

    async def get_citations(self):
        await db.connect()
        url = f"https://app.vlex.com/vid/892339216/citations.json?type=link&locale=en&t=1764259413"

        async with aiohttp.ClientSession(headers={'cookie': self.cookie}) as session:
            async with session.get(url) as response:
                data = await response.json()
                data = CaseCitations(data)

                await db.batch_upsert_dataframe(data.as_dataframe, table_name='vlex_citations', unique_columns=['source_id', 'target_id', 'snippet'])


                return data


    async def research_assignment(self):
        await db.connect()
        data = await self.get_user_history()

        task_ids = list(data.task_id)

        sem = asyncio.Semaphore(10)  # <-- set concurrency here

        async def fetch_one(session: aiohttp.ClientSession, tid: str):
            url = f"https://us-vincent.vlex.com/research_assignment/{tid}/"
            async with sem:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    return tid, await resp.json()

        async with aiohttp.ClientSession(headers={"cookie": self.cookie}) as session:
            results = await asyncio.gather(
                *(fetch_one(session, tid) for tid in task_ids),
                return_exceptions=True,
            )

        # handle results
        ok = {}
        errors = {}
        for item in results:
            if isinstance(item, Exception):
                # gather-level exception (rare here), bucket it
                errors["gather"] = errors.get("gather", []) + [repr(item)]
                continue

            tid, payload = item
            if isinstance(payload, Exception):
                errors[tid] = payload
            else:
                ok[tid] = payload


        return ok, errors
    

    def parse_vlex_citations(self, payload: dict) -> pd.DataFrame:
        authorities = payload.get("authorities") or []

        rows = []
        for a in authorities:
            treatment = a.get("treatment") or {}

            rows.append({
                # join keys (from top-level + per-authority)
                "conversation_id": payload.get("conversation_id"),
                "assignment_id": payload.get("id"),              # top-level id from response
                "authority_id": a.get("id"),                     # vLex internal id string

                # main identifiers
                "vid": a.get("vid"),
                "content_type": a.get("contentType"),

                # citation / label fields
                "title": a.get("title"),
                "citation": a.get("citation"),
                "full_citation": a.get("full_citation"),
                "date": a.get("date"),
                "court": a.get("court"),

                # ranking / tagging
                "relevancy": a.get("relevancy"),
                "score": a.get("score"),
                "source": a.get("source"),

                # text fields
                "context": a.get("context"),
                "rationale": a.get("rationale"),

                # legislation breadcrumb (optional)
                "breadcrumb": " > ".join(a.get("breadcrumb") or []) or None,

                # treatment (optional)
                "treatment_aggregate": treatment.get("aggregate_treatment"),
                "treatment_attitude": treatment.get("attitude"),
                "treatment_case_full_citation": treatment.get("case_full_citation"),
                "treatment_case_to_case": treatment.get("case_to_case_treatment"),
                "treatment_vid": treatment.get("vid"),
            })

        df = pd.DataFrame(rows)

        # optional: keep only the most useful columns (edit as you like)
        keep = [
            "conversation_id", "assignment_id",
            "vid", "content_type",
            "title", "citation", "full_citation",
            "date", "court",
            "relevancy", "score", "source",
            "treatment_aggregate", "treatment_attitude", "treatment_vid",
            "breadcrumb",
            "context", "rationale",
            "authority_id",
        ]
        return df[keep] if not df.empty else df