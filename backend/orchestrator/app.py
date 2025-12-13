# app.py (improved)
import os
import json
import traceback
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import ast
from agents.master import run_agent, run_agent_stream

# --- App setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "static", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"))
# Allow your frontend origin (adjust if needed). Using "*" is OK for local dev.
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "pdf_dir": PDF_DIR})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get("message", "")
        session_id = data.get("session_id", "guest")

        # run the multi-agent workflow (may raise)
        raw_response = run_agent(message, session_id)

        # Normalize response types:
        cleaned_response = None

        # If run_agent returned a dict/list (structured state), try to extract final text
        if isinstance(raw_response, dict):
            # try common keys
            for key in ("final_response", "response", "text"):
                if key in raw_response:
                    cleaned_response = raw_response[key]
                    break
            if cleaned_response is None:
                # fallback: stringify meaningful parts
                cleaned_response = json.dumps(raw_response)
        elif isinstance(raw_response, list):
            cleaned_response = " ".join([str(x) for x in raw_response])
        elif isinstance(raw_response, str):
            stripped = raw_response.strip()
            # If Gemini returns a stringified dict like "{'type': 'text', 'text': 'hi'}"
            if stripped.startswith("{") and "'type': 'text'" in stripped:
                try:
                    parsed = ast.literal_eval(stripped)
                    cleaned_response = parsed.get("text", raw_response)
                except Exception:
                    cleaned_response = raw_response
            else:
                cleaned_response = raw_response
        else:
            cleaned_response = str(raw_response)

        return jsonify({"response": cleaned_response})

    except Exception as e:
        # Print stacktrace to terminal for debugging
        tb = traceback.format_exc()
        print("ERROR in /chat:", tb)
        return jsonify({"response": f"System Error: {str(e)}", "trace": tb}), 500


@app.route("/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming endpoint using Server-Sent Events (SSE).
    
    This endpoint streams responses in real-time as they are generated,
    providing a more responsive user experience.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        message = data.get("message", "")
        session_id = data.get("session_id", "guest")
        
        def generate():
            """Generator function for SSE streaming."""
            try:
                for chunk in run_agent_stream(message, session_id):
                    if chunk:
                        # Format as SSE data event
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Send done signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR in /chat/stream:", tb)
        return jsonify({"error": f"System Error: {str(e)}", "trace": tb}), 500


@app.route("/static/pdfs/<path:filename>")
def serve_pdf(filename):
    # Safe serving from absolute PDF_DIR
    return send_from_directory(PDF_DIR, filename, as_attachment=False)


if __name__ == "__main__":
    print("Starting backend on http://127.0.0.1:5000")
    # IMPORTANT: run from backend/orchestrator so imports work
    app.run(host="127.0.0.1", port=5000, debug=True)

