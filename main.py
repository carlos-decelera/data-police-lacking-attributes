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
    """Caso 2: Entrada en lista (Fast Tracks)"""
    list_id = event.get("id", {}).get("list_id")
    entry_id = event.get("id", {}).get("entry_id")
    
    # IMPORTANTE: El ID de la empresa viene en el evento
    parent_record_id = event.get("parent_record_id")

    if not list_id or not entry_id or not parent_record_id: return

    # 1. Obtenemos la ENTRADA (para validar los campos de lista: ARR, Deal Owner...)
    entry_data = await attio.get_entry(list_id, entry_id)
    if not entry_data: return

    # 2. Validamos sobre la entrada
    missing = attio.validate_fields(entry_data, REQUIRED_FIELDS_FAST_TRACK)

    if missing:
        # 3. EL CAMBIO CLAVE:
        # Como entry_data no tiene el nombre, descargamos la EMPRESA usando el ID padre
        company_record = await attio.get_record("companies", parent_record_id)
        
        # Ahora sacamos el nombre de la empresa (si falla la descarga, ponemos "Compañía")
        name = get_record_name(company_record) if company_record else "Compañía"
        
        msg = f"*{name}* movida a Fast Tracks sin datos. Faltan: `{', '.join(missing)}`"
        url = f"https://app.attio.com/deceleraventures/company/{parent_record_id}"
        await send_slack_alert(msg, url)


def get_record_name(record: dict) -> str:
    """Extrae el nombre de un registro de empresa estándar"""
    try:
        # Ahora siempre recibiremos un record completo (con values)
        if "values" in record and "name" in record["values"]:
            vals = record["values"]["name"]
            if len(vals) > 0:
                return vals[0]["value"]
        return "Compañía"
    except:
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

