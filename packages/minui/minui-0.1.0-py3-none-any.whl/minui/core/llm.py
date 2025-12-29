import json
import logging
import requests

def stream_chat(messages, config):
    """
    Generic streaming wrapper.
    Routes to specific provider handlers based on config.
    """
    provider = config.get('provider', 'openai')
    
    if provider == 'anthropic':
        return stream_anthropic(messages, config)
    else:
        # Default to OpenAI format (Works for OpenAI, OpenRouter, DeepSeek, Ollama, etc)
        return stream_openai_compat(messages, config)

def stream_openai_compat(messages, config):
    """Handler for OpenAI-compatible APIs"""
    
    # Prepend system prompt
    full_messages = [{"role": "system", "content": config['system_prompt']}] + messages

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/example/minui",
        "X-Title": "MinUI"
    }

    payload = {
        "model": config['model'],
        "messages": full_messages,
        "stream": True
    }

    # OpenRouter specific reasoning flag
    if "openrouter" in config.get('api_url', ''):
        payload["include_reasoning"] = True

    try:
        # Handle trailing slash issues in user input
        api_url = config['api_url'].rstrip('/')
        if not api_url.endswith('/chat/completions'):
             # Auto-append endpoint if user just gave the base (common user error)
             api_url += '/chat/completions'

        with requests.post(
            api_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        ) as response:
            if response.status_code != 200:
                yield _err(f"API Error {response.status_code}: {response.text}")
                return

            for line in response.iter_lines():
                if not line: continue
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    data_str = decoded[6:]
                    if data_str == '[DONE]': return
                    try:
                        data = json.loads(data_str)
                        if data.get('choices'):
                            delta = data['choices'][0]['delta']
                            content = delta.get('content', '')
                            reasoning = delta.get('reasoning', '') 
                            
                            if content: yield _emit("content", content)
                            if reasoning: yield _emit("reasoning", reasoning)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield _err(f"Connection failed: {str(e)}")

def stream_anthropic(messages, config):
    """Handler for Anthropic API"""
    headers = {
        "x-api-key": config['api_key'],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Anthropic separates system prompt
    payload = {
        "model": config['model'],
        "system": config['system_prompt'],
        "messages": messages,
        "stream": True,
        "max_tokens": 4096
    }
    
    api_url = config['api_url'].rstrip('/')
    if not api_url.endswith('/messages'):
        api_url += '/messages'

    try:
        with requests.post(
            api_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        ) as response:
            if response.status_code != 200:
                yield _err(f"Anthropic Error {response.status_code}: {response.text}")
                return

            for line in response.iter_lines():
                if not line: continue
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    try:
                        data = json.loads(decoded[6:])
                        if data['type'] == 'content_block_delta':
                            yield _emit("content", data['delta']['text'])
                    except: continue
    except Exception as e:
        yield _err(f"Connection failed: {str(e)}")

def _emit(type_, payload):
    return json.dumps({"type": type_, "payload": payload}) + "\n"

def _err(msg):
    logging.error(msg)
    return json.dumps({"type": "error", "payload": msg}) + "\n"