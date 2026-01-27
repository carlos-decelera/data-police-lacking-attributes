```mermaid
graph TD
    A[Webhook de Attio] -->|POST /missing-fields| B(main.py: receive_attio_webhook)
    B --> C{¿Actor es miembro?}
    C -- No --> D[Ignorar Evento]
    C -- Sí --> E{Tipo de Evento}

    %% Caso 1: Creación de Empresa
    E -- record.created --> F[handle_company_created]
    F --> G[AttioService: get_record]
    G --> H[AttioService: validate_fields]
    H --> I{¿Faltan campos?}
    I -- Sí --> J[slack.py: send_slack_alert]

    %% Caso 2: Entrada en Fast Track
    E -- list-entry.created --> K[handle_fast_track_entry]
    K --> L[AttioService: get_entry]
    L --> M[AttioService: get_record ID Padre]
    M --> N[AttioService: validate_fields]
    N --> O{¿Faltan campos?}
    O -- Sí --> J

    %% Estilos
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style J fill:#4A154B,color:#fff,stroke:#333
    style G fill:#fff,stroke:#333
    style L fill:#fff,stroke:#333
