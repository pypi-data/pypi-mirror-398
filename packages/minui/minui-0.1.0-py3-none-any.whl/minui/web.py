import logging
import webbrowser
from flask import Flask, render_template, jsonify, request, Response

from .core.context import generate_tree_markdown
from .core.llm import stream_chat

def create_app(root_path=None):
    target_repo_path = root_path or "."
    app = Flask(__name__)

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/api/context', methods=['GET'])
    def get_context():
        try:
            content = generate_tree_markdown(target_repo_path)
            return jsonify({"content": content, "size": len(content)})
        except Exception as e:
            logging.error(f"Context generation failed: {e}")
            return jsonify({"error": "Failed to generate context"}), 500

    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Extract config from request payload (Stateless Backend)
        messages = data.get('messages', [])
        config = {
            'provider': data.get('provider', 'openai'),
            'api_url': data.get('api_url'),
            'api_key': data.get('api_key'),
            'model': data.get('model'),
            'system_prompt': data.get('system_prompt', 'You are a helpful coding assistant.')
        }

        if not config['api_key']:
             return jsonify({"error": "API Key is missing. Please check Settings."}), 401

        return Response(
            stream_chat(messages, config),
            mimetype='application/x-ndjson'
        )

    return app

def open_browser(url):
    webbrowser.open_new(url)