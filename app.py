import gradio as gr
import ollama
import os

os.makedirs("logs", exist_ok=True)

def extract_text(content):
    """Extract text from Gradio's content format"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Gradio 6.0 sends [{'text': '...', 'type': 'text'}]
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                return item['text']
    elif isinstance(content, dict):
        return content.get('text', str(content))
    return str(content)

def chat(message, history):
    if history is None:
        history = []
    
    # 1. Build messages for Ollama
    ollama_messages = []
    for msg in history:
        role = msg.get("role", "user")
        content = extract_text(msg.get("content", ""))
        ollama_messages.append({"role": role, "content": content})
    
    # Add current user message
    ollama_messages.append({"role": "user", "content": message})
    
    # 2. Call Ollama
    try:
        response = ollama.chat(model='mia:latest', messages=ollama_messages)
        answer = response['message']['content'].strip()
    except Exception as e:
        answer = f"Error: {str(e)}"
    
    # 3. Add DIL Warning
    final_answer = answer + "\n\n⚠️ [DIL REQUIRED] — Verify with physician."
    
    # 4. Log
    with open("logs/queries.log", "a", encoding="utf-8") as f:
        f.write(f"Q: {message}\nA: {final_answer}\n---\n")
    
    # 5. Update History (Gradio 6.0 format)
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": final_answer}
    ]
    
    return new_history

with gr.Blocks(title="Nurse Assistant") as app:
    gr.Markdown("## 🩺 Triage Assistant (With Memory)")
    with gr.Row():
        btn1 = gr.Button("🤒 Fever + Cough?")
        btn2 = gr.Button("💔 Chest Pain?")
    
    chatbot = gr.Chatbot(label="Conversation History", height=300)
    msg = gr.Textbox(label="Type patient concern...", placeholder="e.g., Patient has fever...")
    btn = gr.Button("🚀 Send", variant="primary")
    
    btn.click(chat, inputs=[msg, chatbot], outputs=[chatbot])
    msg.submit(chat, inputs=[msg, chatbot], outputs=[chatbot])
    btn1.click(lambda: "Patient has fever and cough", None, msg)
    btn2.click(lambda: "Patient has chest pain", None, msg)

app.launch(server_name="0.0.0.0", server_port=7870, css="footer {visibility: hidden}")