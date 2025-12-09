# RNI-InfoEngine

Motor unificado de información y analítica para la Red Nacional de Información (RNI).  
El proyecto integra:

- **Backend:** Django (API, lógica de negocio, conexión a PostgreSQL)
- **Frontend:** React + Vite (interfaz moderna para dashboards y módulos operativos)
- **IA (próxima fase):** consultas en lenguaje natural con generación segura de SQL.

---

## 🚀 Estructura del repositorio

```

RNI-InfoEngine/
│
├── backend/     → Proyecto Django (API, modelos, vistas, autenticación)
├── frontend/    → Aplicación React (UI, dashboards)
└── README.md

````

---

## ▶️ Cómo ejecutar

### Backend (Django)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
````

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

---

## 👥 Flujo de trabajo

* Daniel → Backend (ramas `backend/*`)
* Brandon → Frontend (ramas `frontend/*`)

```bash
git checkout -b frontend/nueva-funcionalidad
git add .
git commit -m "Descripción"
git push
```

---

## 🌐 URL de desarrollo (ngrok)

Backend expuesto temporalmente para integración:

```
https://srni-backend.ngrok.io/
```

---

## 📌 Estado del proyecto

* ✔ Backend organizado en estructura limpia
* ✔ Frontend inicial con React
* ⏳ Integración API
* ⏳ Implementación de IA para consultas SQL

---

## 👤 Autores

* **Daniel Campos** — Backend / Arquitectura
* **Brandon Niño** — Frontend

---

