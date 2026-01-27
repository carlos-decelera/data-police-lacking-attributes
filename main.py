from fastapi import FastAPI, Request, BackgroundTasks
from services.attio import AttioService
from services.slack import send_slack_alert

app = FastAPI()
attio = AttioService()

# --- TUS CAMPOS A VIGILAR ---
REQUIRED_FIELDS_COMPANY = ["domain", "description", "linkedin"]
REQUIRED_FIELDS_FAST_TRACK = ["deal_owner", "next_step", "estimated_arr"]

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
        url = f"https://app.attio.com/w/workspace/record/{record_id}"
        await send_slack_alert(msg, url)


async def handle_fast_track_entry(event: dict):
    # ¡OPTIMIZACIÓN GRACIAS A TU JSON!
    # El ID de la empresa ya viene directo en el evento
    parent_record_id = event.get("parent_record_id")
    
    if not parent_record_id: return

    # Directamente consultamos los datos de la empresa
    record = await attio.get_record("companies", parent_record_id)
    if not record: return

    missing = attio.validate_fields(record, REQUIRED_FIELDS_FAST_TRACK)

    if missing:
        name = get_record_name(record)
        msg = f"*{name}* movida a Fast Tracks sin datos. Faltan: `{', '.join(missing)}`"
        url = f"https://app.attio.com/w/workspace/record/{parent_record_id}"
        await send_slack_alert(msg, url)


def get_record_name(record: dict) -> str:
    try:
        return record["values"]["name"][0]["value"]
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