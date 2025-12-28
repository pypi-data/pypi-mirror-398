# util-rpa

Librería de utilidades corporativas en Python orientada a **automatización operativa (RPA)**,  
procesos **batch**, **RPA** y **pipelines backend**.


Incluye módulos para:

* 📧 Envío de correos SMTP
* 🗄️ Conexión a SQL Server(SQLCMD y BCP)
* 📜 Configuración de logging centralizado

> Diseñado para entornos productivos: scripts backend, ETLs, servicios batch y jobs automatizados.

---

## ✨ Objetivos

* Simplificar tareas repetitivas en proyectos Python empresariales
* Reducir boilerplate en envío de correos o ejecución SQL
* Mantener estandarización y buenas prácticas
* Facilitar adopción por equipos heterogéneos

---

# 🚀 Instalación

```bash
pip install util-rpa
```

> Requiere Python **>= 3.9 y < 3.13**

---

# 📁 Estructura del paquete

```
util_rpa/
│
├── mail/
│   ├── smtp_client.py
│   ├── smtp_notifier.py
│
├── sql/
│   ├── sqlcmd.py        # sqlcmd (batch SQL)
│   ├── bcp.py           # BCP (bulk IN/OUT)
│   ├── parsers.py       # parseo de logs SQL
│
├── logging_utils.py
├── __init__.py
└── bin/
    └── mail.exe  (legacy)
```

---

# ✉️ Módulo Mail

Este módulo provee un cliente SMTP estándar y opcionalmente plantillas simples.

### Ejemplo: envío básico

```python
from util_rpa.mail.smtp_client import SMTPClient
from util_rpa.mail.smtp_notifier import SMTPNotifier

EMAIL_SUBJECT = "Proceso RPA - ${FECHA}"

EMAIL_BODY = """
<h2>Hola ${USUARIO}</h2>
<p>Este es un test de envío desde util-rpa.</p>
<b>Estado:</b> ${ESTADO}
<br><br>
<small>Mensaje generado automáticamente.</small>
"""

client = SMTPClient()

notifier = SMTPNotifier(
    smtp=client,
    sender="robot.bolo@movistar.com.pe",
    to=["jonathan.bolo@integratel.com.pe"],
    cc=None,
    subject_template=EMAIL_SUBJECT,
    body_template=EMAIL_BODY,
)

resultado = notifier.notify(
    context={
        "FECHA": "2025/01/01",
        "USUARIO": "Jonathan",
        "ESTADO": "✔️ OK",
    }
)
print("Resultado envío normal: success=%s error=%s",
    resultado.success,
    resultado.error,
)
```

---

# 🗄️ Módulo SQL

## 1️⃣ SQLCMD (batch SQL)

Para scripts .sql complejos:

* múltiples batches
* prints
* :setvar
* ejecución operacional

```python
from util_rpa.sql.sqlcmd import SQLCmd
from pathlib import Path

sqlcmd = SQLCmd(ctx.secrets.db)

sqlcmd.run(
    sql_file=Path("scripts/proceso.sql"),
    output_log=Path("logs/sqlcmd.log"),
    variables={"${FECHA}": "20250101"}
)
```

2️⃣ BCP (bulk IN / OUT)

Para cargas y descargas masivas.

```python
from util_rpa.sql.bcp import BCP

bcp = BCP(ctx.secrets.db)
bcp.run(
    table="dbo.tabla",
    file=Path("data/salida.txt"),
    operation="OUT",
    error_log=Path("logs/bcp.err")
)
```

3️⃣ Parsers (parseo de logs SQL)

Extrae data desde logs generados por **sqlcmd** o **bcp**.

```python
from util_rpa.sql.parsers import extract_prefixed_lines

extract_prefixed_lines(
    sql_log=Path("logs/sqlcmd.log"),
    output_file=Path("data/resultado.txt"),
    prefix="DATA:"
)
```

# 📝 Logging

Inicializa logger raíz reutilizable.

```python
from util_rpa.logging_utils import init_logging

log = init_logging(
    level="INFO",
    log_file="process.log",
    max_bytes=10*1024*1024,
    backup_count=3
)
```

Ahora puedes usar:

```python
log.info("Iniciando proceso")
log.error("Error crítico", exc_info=True)
```

> Logging rotativo para procesos batch/cron grandes.

---

# ⚠️ Sobre `mail.exe` (legacy)

`util_rpa/bin/mail.exe` es un envío SMTP alternativo para entornos Windows sin relay o TLS.

* Úsalo solo como fallback
* No recomendado en Linux ni Docker
* No recomendado en entornos CI/CD

---

# 📦 Requerimientos

Dependencias mínimas:

```
pandas>=2.0,<3.0
python-dateutil>=2.8,<3.0
```

---

# 🏛️ Versionamiento

> El paquete sigue **Semantic Versioning (SemVer)**.

* **2.0.0** → Primera versión modular (breaking changes respecto a 1.x)
* **2.1.x** → Nuevas funcionalidades sin romper compatibilidad
* **2.1.1** → Hotfix

---

# 🧪 Desarrollo

Instalar dependencias de desarrollo:

```bash
pip install .[dev]
```

Correr tests:

```bash
pytest -q
```

---

# 📌 Buenas prácticas recomendadas

* Inicializa logging una sola vez en `main.py`
* Usa plantillas para correos en vez de concatenación manual
* No expongas credenciales en código
* No uses `mail.exe` si tienes SMTP normal

---

# 📜 Licencia

MIT — Uso libre con atribución.

---

# ✉️ Contacto / Autor

* **Jonathan Bolo**
* Especialista en ingeniería, Python, automatización corporativa
* Integratel Perú

---

# 📎 Ejemplos listos para copiar

> Puedes crear un script `main.py`:

```python
from util_rpa.logging_utils import init_logging
from util_rpa.mail.smtp import SMTPClient
from util_rpa.sql.sqlserver import SQLServer

log = init_logging()

# Notificación
smtp = SMTPClient("10.10.10.1", port=25)
smtp.send(...)
```

---

# 🛡️ Disclaimer

`util-rpa` es una librería **técnica**.
No se recomienda para UI, web frameworks o interfaces HMI.
Diseñada para **backend operativo, batch y automatización con RPAs**.