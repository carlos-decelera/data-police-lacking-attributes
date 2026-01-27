import os
import httpx

class AttioService:
    def __init__(self):
        self.api_key = os.getenv("ATTIO_API_KEY")
        self.base_url = "https://api.attio.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def get_record(self, object_slug: str, record_id: str):
        """Descarga los datos de una Compañía"""
        url = f"{self.base_url}/objects/{object_slug}/records/{record_id}"
        
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code == 200:
                return res.json().get("data")
            return None

    async def get_entry(self, list_slug: str, entry_id: str):
        """Descargamos los datos de la entrada de la lista"""
        url = f"{self.base_url}/lists/{list_slug}/entries/{entry_id}"

        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code == 200:
                return res.json().get("data")
            return None

    def validate_fields(self, record_data: dict, required_slugs: list):
        """Revisa qué campos faltan"""
        missing = []
        if not record_data: return missing

        values = record_data.get("values", {}) or record_data.get("entry_values", {})
        for slug in required_slugs:
            field_val = values.get(slug)
            if not field_val or len(field_val) == 0:
                missing.append(slug)
        return missing