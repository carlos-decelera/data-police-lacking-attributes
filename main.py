from fastapi import FastAPI, Request, BackgroundTasks
from services.attio import AttioService
from services.slack import send_slack_alert

app = FastAPI()
attio = AttioService()

# --- TUS CAMPOS A VIGILAR ---
REQUIRED_FIELDS_COMPANY = ["domains", "name"]
REQUIRED_FIELDS_FAST_TRACK = ["fast_track_status_6", "owner", "date_first_contact_1"]

# --- LÓGICA DE NEGOCIO ---

async def handle_company_created(event: dict):
    # El ID está dentro de 'id' en creación de records
    record_id = event.get("id", {}).get("record_id")
    if not record_id: return

    record = await attio.get_record("companies", record_id)
    if not record: return

    missing = attio.validate_fields(record, REQUIRED_FIELDS_COMPANY)

    if missing:
        name = get_record_name(record)
        msg = f"Nueva compañía *{name}* incompleta. Faltan: `{', '.join(missing)}`"
        url = f"https://app.attio.com/deceleraventures/company/{record_id}"
        await send_slack_alert(msg, url)


async def handle_fast_track_entry(event: dict):
    """Caso 2: Se añade una entrada a la lista Fast Tracks"""
    # Obtenemos IDs del evento
    list_id = event.get("id", {}).get("list_id")
    entry_id = event.get("id", {}).get("entry_id")
    parent_record_id = event.get("parent_record_id") # Para el link

    if not list_id or not entry_id: return

    # 1. Obtenemos la ENTRADA de la lista (Aquí usas tu nuevo método)
    # Esto traerá 'entry_values' (datos de la lista) y 'values' (datos del padre)
    entry_data = await attio.get_entry(list_id, entry_id)
    if not entry_data: return

    # 2. Validamos (Tu validate_fields buscará en 'entry_values' gracias al cambio que hicimos)
    missing = attio.validate_fields(entry_data, REQUIRED_FIELDS_FAST_TRACK)

    if missing:
        name = get_record_name(entry_data)
        msg = f"*{name}* movida a Fast Tracks sin datos. Faltan: `{', '.join(missing)}`"
        
        # Usamos el parent_id para que el link lleve a la ficha de la empresa
        url = f"https://app.attio.com/deceleraventures/company/{parent_record_id}"
        await send_slack_alert(msg, url)


def get_record_name(data: dict) -> str:
    """
    Intenta extraer el nombre del registro, soportando dos formatos:
    1. Objeto directo (ej: Company) -> Busca en 'values.name'
    2. Entrada de lista (ej: Entry) -> Busca en 'parent_record.values.name'
    """
    try:
        # ESTRATEGIA 1: Es un registro normal (Company)
        # El nombre está directamente en 'values'
        if "values" in data and "name" in data["values"]:
            # Verificamos que la lista no esté vacía
            if len(data["values"]["name"]) > 0:
                return data["values"]["name"][0]["value"]
        
        # ESTRATEGIA 2: Es una entrada de lista (Entry)
        # Los datos de la empresa suelen venir dentro de 'parent_record'
        if "parent_record" in data:
            parent = data["parent_record"]
            # Repetimos la búsqueda dentro del padre
            if "values" in parent and "name" in parent["values"]:
                if len(parent["values"]["name"]) > 0:
                    return parent["values"]["name"][0]["value"]
            
        # Fallback si no encuentra nada
        return "Compañía"

    except Exception:
        # Si la estructura JSON cambia o es inesperada, no rompemos el programa
        return "Compañía"


# --- ROUTER PRINCIPAL ---

@app.post("/missing-fields")
async def receive_attio_webhook(request: Request, bg_tasks: BackgroundTasks):
    payload = await request.json()
    events = payload.get("events", [])

    for event in events:
        # 1. Filtro Humano (workspace-member)
        actor_type = event.get("actor", {}).get("type")
        if actor_type != "workspace-member":
            continue

        event_type = event.get("event_type")

        # 2. Distribuidor de Tareas
        if event_type == "record.created":
            bg_tasks.add_task(handle_company_created, event)
        
        elif event_type == "list-entry.created":
            bg_tasks.add_task(handle_fast_track_entry, event)


    return {"status": "ok"}

