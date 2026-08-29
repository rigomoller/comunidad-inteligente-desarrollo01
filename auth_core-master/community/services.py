import json
import os
from urllib import error, request


def _community_context(neighborhood):
    posts = list(neighborhood.posts.filter(is_published=True).order_by("-created_at").values_list("title", "content")[:5])
    activities = list(neighborhood.activities.order_by("starts_at").values_list("title", "starts_at", "location")[:5])
    documents = list(neighborhood.documents.order_by("-created_at").values_list("title", "category")[:5])
    return {"junta": neighborhood.name, "publicaciones": posts, "actividades": activities, "documentos": documents}


def _external_ai_answer(question, neighborhood):
    api_url = os.getenv("AI_API_URL", "").strip()
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_url or not api_key:
        return None
    payload = {
        "model": os.getenv("AI_MODEL", "gpt-4.1-mini"),
        "messages": [
            {
                "role": "system",
                "content": "Responde en español de Chile. Usa solo los datos comunitarios entregados. No inventes datos personales.",
            },
            {"role": "user", "content": f"Datos: {json.dumps(_community_context(neighborhood), ensure_ascii=False, default=str)}\nPregunta: {question}"},
        ],
        "temperature": 0.2,
    }
    http_request = request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except (error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
        return None


def answer_community_question(question, neighborhood):
    external_answer = _external_ai_answer(question, neighborhood)
    if external_answer:
        return external_answer
    text = question.lower().strip()
    if "actividad" in text or "evento" in text:
        activity = neighborhood.activities.order_by("starts_at").first()
        return f"La próxima actividad es {activity.title} en {activity.location}." if activity else "No existen actividades registradas."
    if "publicación" in text or "noticia" in text:
        post = neighborhood.posts.filter(is_published=True).order_by("-created_at").first()
        return f"La publicación más reciente es: {post.title}." if post else "No existen publicaciones disponibles."
    if "documento" in text or "estatuto" in text:
        return f"Existen {neighborhood.documents.count()} documentos disponibles para consultar."
    return "Puedo ayudarte con actividades, publicaciones y documentos autorizados de tu junta de vecinos."
