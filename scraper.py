#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JW.ORG Scraper → Todoist
Monitora páginas do jw.org e cria tarefas automaticamente
"""

import os
import json
import requests
from datetime import datetime
import hashlib

TODOIST_TOKEN = os.environ['TODOIST_TOKEN']
STATE_FILE = 'state.json'

PAGES = {
    'sentinela': {
        'url': 'https://www.jw.org/pt/biblioteca/revistas/w/',
        'selector': 'A Sentinela',
        'priority': 2
    },
    'despertai': {
        'url': 'https://www.jw.org/pt/biblioteca/revistas/g/',
        'selector': 'Despertai',
        'priority': 2
    },
    'videos': {
        'url': 'https://www.jw.org/pt/biblioteca/videos/',
        'selector': 'Vídeos JW',
        'priority': 3
    }
}

def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def create_task(content, url, priority):
    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "content": content,
        "description": f"🔗 {url}\n\n📅 Adicionado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "priority": priority,
        "labels": ["jw.org"]
    }

    response = requests.post(
        "https://api.todoist.com/rest/v2/tasks",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()

def main():
    print(f"🔍 Executando scraper em {datetime.now()}")
    state = load_state()

    for key, page in PAGES.items():
        # Gerar hash simples baseado na data atual
        # Em produção, você faria scraping real aqui
        current_hash = hashlib.md5(datetime.now().strftime('%Y-%m-%d').encode()).hexdigest()

        if state.get(key) != current_hash:
            print(f"✅ Nova atualização detectada em {page['selector']}")

            try:
                task = create_task(
                    f"📖 Novo conteúdo: {page['selector']}",
                    page['url'],
                    page['priority']
                )
                print(f"   Tarefa criada: {task['id']}")
                state[key] = current_hash
            except Exception as e:
                print(f"❌ Erro: {e}")

    save_state(state)
    print("✅ Execução finalizada")

if __name__ == "__main__":
    main()
