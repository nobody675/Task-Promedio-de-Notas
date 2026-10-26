
from flask import Flask, render_template, request, jsonify
from threading import Lock

app = Flask(__name__)

# Datos temporales en memoria.
# Para un proyecto con varios usuarios se recomienda una base de datos.
tasks = []
history = []
next_task_id = 1
data_lock = Lock()

MAX_GRADE = 5.0
PASS_GRADE = 3.0


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/promedio", methods=["POST"])
def calcular_promedio():
    data = request.get_json(silent=True) or {}

    nombre = str(data.get("nombre", "")).strip()
    notas = data.get("notas")

    if not nombre:
        return jsonify({"error": "Ingresa el nombre del estudiante."}), 400

    if not isinstance(notas, list) or not 1 <= len(notas) <= 50:
        return jsonify({
            "error": "Debes ingresar entre 1 y 50 notas."
        }), 400

    try:
        calificaciones = [float(nota) for nota in notas]
    except (ValueError, TypeError):
        return jsonify({"error": "Todas las notas deben ser números."}), 400

    if any(not 0 <= nota <= MAX_GRADE for nota in calificaciones):
        return jsonify({
            "error": f"Las notas deben estar entre 0 y {MAX_GRADE}."
        }), 400

    promedio = sum(calificaciones) / len(calificaciones)
    resultado = {
        "nombre": nombre,
        "notas": calificaciones,
        "cantidad": len(calificaciones),
        "promedio": round(promedio, 2),
        "aprobado": promedio >= PASS_GRADE
    }

    with data_lock:
        history.insert(0, resultado.copy())

    return jsonify(resultado)


@app.route("/api/historial", methods=["GET"])
def obtener_historial():
    with data_lock:
        return jsonify(history)


@app.route("/api/historial", methods=["DELETE"])
def borrar_historial():
    with data_lock:
        history.clear()
    return jsonify({"mensaje": "Historial eliminado."})


@app.route("/api/tareas", methods=["GET"])
def obtener_tareas():
    with data_lock:
        return jsonify(tasks)


@app.route("/api/tareas", methods=["POST"])
def crear_tarea():
    global next_task_id

    data = request.get_json(silent=True) or {}
    titulo = str(data.get("titulo", "")).strip()

    if not titulo:
        return jsonify({"error": "Escribe el nombre de la tarea."}), 400

    if len(titulo) > 120:
        return jsonify({"error": "La tarea no puede superar 120 caracteres."}), 400

    with data_lock:
        tarea = {
            "id": next_task_id,
            "titulo": titulo,
            "completada": False
        }
        next_task_id += 1
        tasks.append(tarea)

    return jsonify(tarea), 201


@app.route("/api/tareas/<int:tarea_id>", methods=["PATCH"])
def actualizar_tarea(tarea_id):
    data = request.get_json(silent=True) or {}

    with data_lock:
        tarea = next(
            (item for item in tasks if item["id"] == tarea_id),
            None
        )

        if tarea is None:
            return jsonify({"error": "Tarea no encontrada."}), 404

        if "completada" in data:
            if not isinstance(data["completada"], bool):
                return jsonify({
                    "error": "El estado debe ser verdadero o falso."
                }), 400
            tarea["completada"] = data["completada"]

    return jsonify(tarea)


@app.route("/api/tareas/<int:tarea_id>", methods=["DELETE"])
def eliminar_tarea(tarea_id):
    with data_lock:
        for indice, tarea in enumerate(tasks):
            if tarea["id"] == tarea_id:
                tasks.pop(indice)
                return jsonify({"mensaje": "Tarea eliminada."})

    return jsonify({"error": "Tarea no encontrada."}), 404


if __name__ == "__main__":
    app.run(debug=True)

