# 🕸️ Trapnet — Honeypot + Pipeline de análisis de ataques

**Trapnet** es un proyecto de ciberseguridad orientado al aprendizaje que captura ataques reales en un honeypot (Cowrie) y los procesa a través de un pipeline.

---

## 🚀 Qué hace actualmente

- Exponer un honeypot SSH real usando **Cowrie**
- Capturar intentos de conexión, credenciales y comandos
- Procesar eventos en tiempo real
- Transformar eventos a un formato propio
- Enviar eventos a un backend central
- Persistir eventos en **PostgreSQL**
- Consultar eventos a través de una API REST

---

## 🧠 Arquitectura

```text
[ atacante ]
     ↓
[ Cowrie (honeypot SSH) ]
     ↓
[ cowrie.json (logs estructurados) ]
     ↓
[ Forwarder (parser + sender) ]
     ↓
[ Collector API ]
     ↓
[ PostgreSQL ]
     ↓
[ endpoints de consulta ]
```

---

## 🧩 Componentes

### 🐍 Cowrie (honeypot)

- Simula un servidor SSH vulnerable
- Acepta conexiones reales
- Registra:
  - intentos de login
  - credenciales
  - comandos ejecutados
- Escribe eventos en:
  /cowrie/cowrie-git/var/log/cowrie/cowrie.json

---

### 🔄 Forwarder

Servicio en Python que:

- Lee el fichero `cowrie.json` en tiempo real
- Procesa cada evento
- Lo transforma a formato interno (Trapnet)
- Envía eventos al collector vía HTTP

---

### 🌐 Collector API

Backend con FastAPI que:

- Recibe eventos (`POST /events`)
- Valida datos con Pydantic
- Guarda eventos en PostgreSQL
- Expone endpoints:

GET /events  
GET /sessions/{session_id}  
GET /stats/source-ip  
GET /health  

---

### 🗄️ PostgreSQL

Base de datos donde se almacenan los eventos de forma persistente.

Permite:

- mantener histórico
- consultar por sesión
- analizar actividad por IP
- escalar el sistema

---

## 📦 Ejemplo de evento

```json
{
  "event_source": "cowrie",
  "event_type": "ssh_command_input",
  "source_ip": "172.18.0.1",
  "timestamp": "2026-03-17T23:18:34.795561Z",
  "session_id": "c217cfeecc9c",
  "command": "ls"
}
```

---

## ⚙️ Cómo ejecutar el proyecto

Desde la raíz:

```bash
docker compose -f infra/docker-compose.local.yml up --build
```

---

## 🧪 Probar el honeypot

```bash
ssh -p 2222 root@localhost
```

Introduce cualquier contraseña y ejecuta comandos.

---

## 🔍 Ver datos

Eventos:
http://localhost:8000/events

Health:
http://localhost:8000/health

---

## 🚧 Próximos pasos

- Analyzer de sesiones
- Clasificación de ataques
- IA para explicación de eventos
- Dashboard
- Mejora de arquitectura (services, repositories)

---

## 🧠 Estado actual

✔ Honeypot real funcionando  
✔ Pipeline de eventos completo  
✔ Persistencia en PostgreSQL  
✔ Endpoints de consulta operativos  
