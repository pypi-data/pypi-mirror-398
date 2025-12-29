import asyncio
import pandas as pd
import json
import time
import requests
import copy
from typing import Any, Dict, Optional, Tuple, List
import re
from pathlib import Path
import webbrowser

class ComfyUISDK:
    def __init__(self, base_url="http://localhost:8000", client_id="fudstop"):
        self.base_url = base_url
        self.client_id = client_id

    def load_workflow(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def clone_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        return copy.deepcopy(workflow)

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}
        r = requests.post(f"{self.base_url}/prompt", json=payload, timeout=60)

        if r.status_code != 200:
            print("STATUS:", r.status_code)
            print("RESPONSE:", r.text[:5000])
            r.raise_for_status()

        data = r.json()
        if "prompt_id" not in data:
            raise RuntimeError(f"No prompt_id in response: {data}")
        return data["prompt_id"]

    def wait_for_result(self, prompt_id: str, poll_interval: float = 0.5) -> Dict[str, Any]:
        while True:
            r = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=60)
            r.raise_for_status()
            history = r.json()
            if prompt_id in history:
                return history[prompt_id]  # includes outputs + status + meta (varies by setup)
            time.sleep(poll_interval)

    # ----------------------------
    # Workflow mutation helpers
    # ----------------------------
    def _get_node(self, workflow: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        if node_id not in workflow:
            raise KeyError(f"node_id {node_id!r} not found in workflow")
        node = workflow[node_id]
        if not isinstance(node, dict):
            raise TypeError(f"workflow[{node_id}] is not a dict node")
        node.setdefault("inputs", {})
        return node

    def set_prompt_text(self, workflow: Dict[str, Any], node_id: str, text: str, input_key: str = "text") -> None:
        """
        Typical node: class_type 'CLIPTextEncode' with inputs: {'text': '...', 'clip': [..]}
        If your workflow uses a different key, pass input_key.
        """
        node = self._get_node(workflow, node_id)
        node["inputs"][input_key] = text

    def set_seed(self, workflow: Dict[str, Any], node_id: str, seed: int, input_key: str = "seed") -> None:
        """
        Typical node: class_type 'KSampler' with inputs containing 'seed'.
        """
        node = self._get_node(workflow, node_id)
        node["inputs"][input_key] = int(seed)

    def set_lora(
        self,
        workflow: Dict[str, Any],
        node_id: str,
        name: str,
        strength_model: float = 1.0,
        strength_clip: Optional[float] = None,
        name_key_candidates: Tuple[str, ...] = ("lora_name", "model_name", "name"),
        model_strength_key_candidates: Tuple[str, ...] = ("strength_model", "lora_strength", "strength"),
        clip_strength_key_candidates: Tuple[str, ...] = ("strength_clip",),
    ) -> None:
        """
        Tries to handle common LoRA loader nodes:
        - 'LoraLoader' usually has inputs:
            { 'lora_name': 'xxx.safetensors', 'strength_model': 1.0, 'strength_clip': 1.0, ... }
        Some custom nodes vary, so we use candidate keys.
        """
        node = self._get_node(workflow, node_id)
        inputs = node["inputs"]

        # set name
        name_key = next((k for k in name_key_candidates if k in inputs), None) or name_key_candidates[0]
        inputs[name_key] = name

        # set model strength
        ms_key = next((k for k in model_strength_key_candidates if k in inputs), None) or model_strength_key_candidates[0]
        inputs[ms_key] = float(strength_model)

        # set clip strength
        if strength_clip is None:
            strength_clip = strength_model
        cs_key = next((k for k in clip_strength_key_candidates if k in inputs), None) or clip_strength_key_candidates[0]
        inputs[cs_key] = float(strength_clip)

    # ----------------------------
    # Discovery / printing helpers
    # ----------------------------
    def list_nodes_by_class(self, workflow: Dict[str, Any], class_type: str) -> List[Tuple[str, Dict[str, Any]]]:
        out = []
        for nid, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == class_type:
                out.append((nid, node))
        return out

    def print_loras(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prints LoRA usage found in the workflow by scanning nodes whose class_type contains 'lora'
        (case-insensitive) and grabbing any likely name/strength fields.
        Returns a list of dicts describing matches.
        """
        matches: List[Dict[str, Any]] = []

        for nid, node in workflow.items():
            if not isinstance(node, dict):
                continue

            ctype = str(node.get("class_type", ""))
            if "lora" not in ctype.lower():
                continue

            inputs = node.get("inputs", {}) or {}
            # best-effort extraction of common fields
            lora_name = (
                inputs.get("lora_name")
                or inputs.get("model_name")
                or inputs.get("name")
                or inputs.get("lora")
            )
            strength_model = inputs.get("strength_model") or inputs.get("lora_strength") or inputs.get("strength")
            strength_clip = inputs.get("strength_clip")

            info = {
                "node_id": nid,
                "class_type": ctype,
                "lora_name": lora_name,
                "strength_model": strength_model,
                "strength_clip": strength_clip,
            }
            matches.append(info)

        if not matches:
            print("No LoRA-like nodes found in this workflow.")
            return []

        print("LoRAs found in workflow:")
        for m in matches:
            print(
                f"  node {m['node_id']} ({m['class_type']}): "
                f"name={m['lora_name']!r}, strength_model={m['strength_model']}, strength_clip={m['strength_clip']}"
            )
        return matches
    

    def get_object_info(self, refresh: bool = False) -> dict:
        if self._object_info_cache is None or refresh:
            r = requests.get(f"{self.base_url}/object_info", timeout=60)
            r.raise_for_status()
            self._object_info_cache = r.json()
        return self._object_info_cache

    # --------- Model listing (generic + specific) ----------

    def list_all_selectable_inputs(self, refresh: bool = False) -> dict:
        """
        Returns:
          { "NodeName.input_name": [values...] }
        for any input that exposes a 'values' list in /object_info.
        """
        info = self.get_object_info(refresh=refresh)
        out = {}

        for node_name, node_meta in info.items():
            inputs = (node_meta or {}).get("input", {}) or {}
            for input_name, input_meta in inputs.items():
                values = (input_meta or {}).get("values", None)
                if isinstance(values, list) and values:
                    out[f"{node_name}.{input_name}"] = values

        return out

    def print_all_models(self, refresh: bool = False, only_modelish: bool = True) -> dict:
        """
        Prints selectable values that look like model file picks.
        If only_modelish=True, filters to inputs whose name hints model selection.
        """
        combos = self.list_all_selectable_inputs(refresh=refresh)

        # Heuristics: keys that typically represent model pickers
        modelish_key_re = re.compile(
            r"(ckpt|checkpoint|model|unet|lora|vae|clip|controlnet|embedding|upscale|upscaler|refiner)",
            re.IGNORECASE
        )

        # Heuristics: values that look like filenames (safetensors, ckpt, pt, pth, bin, gguf, etc.)
        value_file_re = re.compile(r"\.(safetensors|ckpt|pt|pth|bin|gguf|onnx|yaml|yml)$", re.IGNORECASE)

        filtered = {}
        for k, values in combos.items():
            if only_modelish and not modelish_key_re.search(k):
                continue

            # keep if at least one value looks like a file, OR the key is strongly modelish
            if any(isinstance(v, str) and value_file_re.search(v) for v in values) or modelish_key_re.search(k):
                filtered[k] = values

        # Print nicely
        for k in sorted(filtered.keys()):
            print(f"\n{k} ({len(filtered[k])})")
            for v in filtered[k]:
                print("  ", v)

        return filtered

    def list_models_by_input_name(self, input_name: str, refresh: bool = False) -> dict:
        """
        Example: input_name='lora_name' or 'ckpt_name' or 'vae_name'
        Returns nodes that expose that input and their values list.
        """
        info = self.get_object_info(refresh=refresh)
        hits = {}

        for node_name, node_meta in info.items():
            inputs = (node_meta or {}).get("input", {}) or {}
            if input_name in inputs:
                values = (inputs[input_name] or {}).get("values", None)
                if isinstance(values, list) and values:
                    hits[node_name] = values

        return hits

    def print_loras_from_object_info(self, refresh: bool = False) -> dict:
        """
        Prints LoRA lists from ANY node that exposes a lora selector input.
        Works across CR/rgthree/PM/etc.
        """
        candidates = ["lora_name", "lora", "lora_model", "lora_list", "loras"]
        found = {}

        for cname in candidates:
            hits = self.list_models_by_input_name(cname, refresh=refresh)
            if hits:
                found[cname] = hits

        if not found:
            print("No obvious LoRA picker inputs found in /object_info.")
            return {}

        for input_key, nodes in found.items():
            print(f"\n=== LoRA inputs via '{input_key}' ===")
            for node_name, values in nodes.items():
                print(f"{node_name} ({len(values)})")
                for v in values:
                    print("  ", v)

        return found
    


    def get_history(self, prompt_id: str) -> dict:
        r = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=60)
        r.raise_for_status()
        return r.json()

    def extract_image_files(self, history_item: dict) -> list[dict]:
        """
        Returns a list of dicts like:
          {"filename": "...png", "subfolder": "", "type": "output"}
        Works with typical ComfyUI history format.
        """
        files = []
        outputs = (history_item or {}).get("outputs", {}) or {}

        for node_id, out in outputs.items():
            # Most save nodes put images under out["images"] = [{filename, subfolder, type}, ...]
            imgs = (out or {}).get("images", None)
            if isinstance(imgs, list):
                for im in imgs:
                    if isinstance(im, dict) and "filename" in im:
                        files.append(im)

        return files

    def view_url(self, filename: str, subfolder: str = "", file_type: str = "output") -> str:
        """
        Builds a /view URL.
        """
        return (
            f"{self.base_url}/view"
            f"?filename={requests.utils.quote(filename)}"
            f"&subfolder={requests.utils.quote(subfolder or '')}"
            f"&type={requests.utils.quote(file_type or 'output')}"
        )

    def download_image(self, file_meta: dict, out_path: str) -> str:
        """
        Downloads one image described by file_meta into out_path.
        """
        filename = file_meta.get("filename")
        subfolder = file_meta.get("subfolder", "")
        file_type = file_meta.get("type", "output")

        url = self.view_url(filename, subfolder=subfolder, file_type=file_type)

        r = requests.get(url, timeout=120)
        r.raise_for_status()

        out_path = str(out_path)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(r.content)

        return out_path

    def open_in_browser(self, file_meta: dict) -> None:
        """
        Opens the /view link in your default browser (quick sanity check).
        """
        url = self.view_url(
            file_meta.get("filename"),
            subfolder=file_meta.get("subfolder", ""),
            file_type=file_meta.get("type", "output"),
        )
        webbrowser.open(url)