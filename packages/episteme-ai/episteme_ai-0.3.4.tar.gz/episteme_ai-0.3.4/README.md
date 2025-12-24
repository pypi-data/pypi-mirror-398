# 🧠 Episteme AI — Hybrid Reasoning & Proof Verification Engine

Episteme es un motor de razonamiento híbrido (lógico + heurístico + estructural) diseñado para:

- ✔ Verificar **demostraciones formales y semiformales**
- ✔ Analizar **argumentos en lenguaje natural**
- ✔ Detectar **inferencias inválidas**, **contradicciones** y **pasos débiles**
- ✔ Ofrecer trazabilidad paso a paso mediante **ASTs y grafos**
- ✔ Integrar teoremas externos a través de una **Theory DB**

Episteme está pensado como **framework de investigación y análisis**, con aplicaciones en:

- educación en lógica y matemáticas  
- auditoría de razonamientos y argumentos  
- investigación en razonamiento automático  
- sistemas híbridos (reglas + LLMs, en el futuro)

---

## 🚀 Características principales (v0.3)

### 🔹 1. Proof Engine
- Parser estructurado para proofs con pasos numerados
- Checker basado en reglas clásicas:
  - Modus Ponens
  - Modus Tollens
  - Contraposición
  - Instanciación Universal
  - Doble negación
  - Silogismo hipotético
  - Eliminación de conjunción
- Normalización léxica de expresiones (`A->B`, `A → B`, `¬A`, etc.)
- Soporte para teoremas con `invoke_theorem`
- Theory DB en JSON
- Construcción de **ProofGraph** (nodos + dependencias)

---

### 🔹 2. Natural Reasoning Engine
- Parser heurístico de texto natural
- Identificación de:
  - hipótesis
  - claims
  - tesis
  - evidencia
- Detección de contradicciones
- Detección de relaciones evidencia → afirmación
- Construcción de **ArgumentGraph**
- Flags de rigor:
  - score heurístico
  - fortalezas
  - debilidades

---

### 🔹 3. API (FastAPI)
Endpoints principales:

- `POST /evaluate_proof`
- `POST /proof/check_step`
- `POST /parse_proof`
- `POST /check_proof`
- `POST /reasoning/analyze`
- `GET /theory/list`
- `GET /theory/get`

La API devuelve:
- resultados paso a paso
- grafos estructurados
- metadata y versionado (`api_version`)

Documentación interactiva disponible en `/docs`.

---

### 🔹 4. UI Next.js (v0.3)
Incluye:

- dos modos: **Proof | Reasoning**
- editor de texto
- evaluación paso a paso
- visualización de **ProofGraph** y **ArgumentGraph**
- layout automático de grafos
- interacción:
  - click en nodos
  - resaltado de dependencias
  - sincronización lista ↔ grafo

---

## 📦 Instalación y ejecución

### Instalación desde PyPI

```bash
pip install episteme-ai
```

> Nota: el paquete publicado en PyPI se llama `episteme-ai`, pero el paquete importable en código sigue siendo `episteme` (por ejemplo `from episteme.core.checker import ProofChecker`).

---

### 1) Clonar el repositorio (instalación desde código fuente)

```bash
git clone https://github.com/victor-mateu/episteme.git
cd episteme
```

---

## 🖥 Backend (FastAPI)

### Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

### Ejecutar API

```bash
uvicorn episteme.api.main:app --reload
```

La API estará disponible en:

```bash
http://127.0.0.1:8000
```

Documentación interactiva en:

```bash
http://127.0.0.1:8000/docs
```

---

# 🌐 Frontend (Next.js)

Entrar en el directorio de la UI:

```bash
cd episteme-ui
npm install
npm run dev
```

Front disponible en:

```bash
http://localhost:3000
```

---

# 🧩 Formato de Proofs

Los proofs siguen esta sintaxis:

```css
1. assume A
2. assume A -> B
3. derive B from 1,2 using modus_ponens
```

Documentación completa:

`👉 docs/proof_format.md`

---

# 📚 Theory DB

Los teoremas se almacenan en:

```bash
episteme/theory/<theory_name>.json
```

Ejemplo:

```json
{
  "name": "Basic Real Analysis",
  "version": "0.1",
  "theorems": {
    "EVT": "Every continuous function on a closed interval [a,b] attains a maximum and a minimum."
  }
}
```

Se cargan así:

```python
checker = ProofChecker(theory_name="basic_analysis")
```

Documentación completa:

`👉 docs/theories.md`

---

# 🧠 Natural Reasoning

Para analizar argumentos en lenguaje natural:

```bash
POST /reasoning/analyze
```

Ejemplo:

```json
{
  "text": "Supongamos que X. Sin embargo, no X."
}
```

Salida esperada:

* frases clasificadas (claim, hypothesis, …)

* contradicciones detectadas

* relaciones evidencia → conclusión

* flags de rigor

Documentación completa:

`👉 docs/api_usage.md`

---

# 🧪 Tests

Ejecutar tests:

```bash
pytest
```

Coverage:

```bash
pytest --cov=episteme
```

Los tests cubren:

* Parsers

* Checker y Reglas

* Normalización

* Grafos

* Theory loader

* API

---

# 🛠 Estructura del repositorio

```
episteme/
  api/
  core/
  docs/
  parsers/
  reasoning/
  theory/

episteme-ui/
examples/
notebooks/
tests/
```

---

# 🧭 Roadmap resumido

**v0.4**

* Exportación a Lean/Coq (proof sketch → formal)

* Añadir más reglas de inferencia

* Integración con RAG (retrieval de teoremas/documentos)

* Versionado de API (`/v1`)

* CI/CD

**v0.5**

* Modo estricto avanzado (niveles de confianza)

* Integración opcional con LLM para revisión argumental

* Análisis argumental asistido

* Scoring avanzado

**v1.0**

* Episteme Cloud (API SaaS)

* Multiusuario, logs, organización, dashboards

* Plugins externos de teorías

---

# 🤝 Contribuir

Pull requests y sugerencias son bienvenidas.

Para contribuciones:

**1.** Crear rama: `feat/...`, `fix/...`, `docs/...`

**2.** Ejecutar tests antes del commit

**3.** Mantener consistencia con los estilos del repo

**4.** Añadir documentación si se introduce una nueva feature

---

# 📬 Contacto

Para preguntas, ideas o colaboraciones:

[EMAIL / GITHUB / WEB]: [- / victor-mateu / -]
