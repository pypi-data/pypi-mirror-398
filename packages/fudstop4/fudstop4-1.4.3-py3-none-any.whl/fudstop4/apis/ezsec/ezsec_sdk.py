import pandas as pd
import aiohttp
import asyncio
from fudstop4.apis.polygonio.polygon_options import PolygonOptions


df = pd.read_csv(r"C:\Users\chuck\OneDrive\Desktop\FUDSTOP\fudstop\files\ciks.csv")
db = PolygonOptions()