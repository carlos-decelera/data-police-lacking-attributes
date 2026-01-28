```mermaid
graph TD
    A[Webhook de Attio] -->|Envía JSON con eventos| B(main.py: Router Principal)
    
    B --> C{¿Actor humano?}
    C -- No --> D[Ignorar: Evita bucles de bots]
    C -- Sí --> E{¿Qué ocurrió?}

    %% Flujo de Creación
    E -- Nueva Compañía --> F[handle_company_created]
    F -->|Consulta API| G[Descarga datos completos del Record]
    G --> H[Revisa: 'domains' y 'name']
    H --> I{¿Falta información?}
    I -- Sí --> J[slack.py: Envía Alerta]

    %% Flujo de Fast Track
    E -- Movido a Fast Track --> K[handle_fast_track_entry]
    K -->|Consulta API| L[Descarga datos de la Entrada en Lista]
    L -->|Usa parent_record_id| M[Obtiene Nombre de la Empresa]
    M --> N[Revisa: 'owner', 'status' y 'fecha']
    N --> O{¿Campos vacíos?}
    O -- Sí --> J

    %% Detalles de la notificación
    J --> P[Crea link directo a Attio y avisa por canal]

    %% Estilos para que sea vea profesional
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style J fill:#4A154B,color:#fff,stroke:#333
    style F fill:#e1f5fe,stroke:#01579b
    style K fill:#fff3e0,stroke:#e65100
