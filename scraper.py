#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JW.ORG Scraper COMPLETO → Todoist
Monitora TODAS as seções do jw.org e cria tarefas automaticamente
Versão: 3.0 - Completa
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

# ============================================================
# CONFIGURAÇÕES
# ============================================================

TODOIST_TOKEN = os.environ['TODOIST_TOKEN']
STATE_FILE = 'state.json'

# Todas as seções para monitorar
SECTIONS = {
    'homepage': {
        'url': 'https://www.jw.org/pt/',
        'name': '🏠 Página Principal',
        'priority': 2,
        'label': 'destaque'
    },
    'sentinela': {
        'url': 'https://www.jw.org/pt/biblioteca/revistas/w/',
        'name': '📖 A Sentinela',
        'priority': 2,
        'label': 'sentinela'
    },
    'despertai': {
        'url': 'https://www.jw.org/pt/biblioteca/revistas/g/',
        'name': '📖 Despertai',
        'priority': 2,
        'label': 'despertai'
    },
    'videos': {
        'url': 'https://www.jw.org/pt/biblioteca/videos/',
        'name': '🎥 Vídeos JW',
        'priority': 3,
        'label': 'videos'
    },
    'noticias': {
        'url': 'https://www.jw.org/pt/noticias/',
        'name': '📰 Notícias',
        'priority': 3,
        'label': 'noticias'
    },
    'apostila': {
        'url': 'https://www.jw.org/pt/biblioteca/jw-apostila-do-mes/',
        'name': '📋 Apostila da Reunião',
        'priority': 1,
        'label': 'apostila'
    },
    'livros': {
        'url': 'https://www.jw.org/pt/biblioteca/livros/',
        'name': '📚 Publicações',
        'priority': 3,
        'label': 'publicacoes'
    }
}

# ============================================================
# FUNÇÕES
# ============================================================

def load_state():
    """Carrega estado anterior (conteúdos já vistos)"""
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    """Salva estado atual"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def scrape_section(url, section_name):
    """Extrai conteúdos de uma seção do jw.org"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
    }

    try:
        print(f"   📡 Acessando {section_name}...")
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Procurar links de conteúdo
        all_links = soup.find_all('a', href=True)

        items = []
        seen_urls = set()

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Filtrar conteúdo válido
            if not text or len(text) < 15:  # Título muito curto
                continue

            # Montar URL completa
            if href.startswith('/'):
                full_url = f"https://www.jw.org{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                continue

            # Apenas conteúdo do jw.org
            if 'jw.org' not in full_url:
                continue

            # Excluir links de navegação/menu
            exclude_keywords = [
                '/contato', '/ajuda', '/idiomas', '/busca', '/sobre',
                '/termos-de-uso', '/politica-de-privacidade', '/copyright',
                '/ajustes', '/login', '/conta', 'javascript:', '#'
            ]

            if any(keyword in href.lower() for keyword in exclude_keywords):
                continue

            # Evitar duplicatas
            if full_url in seen_urls:
                continue

            seen_urls.add(full_url)

            # Criar hash único
            item_hash = hashlib.md5(full_url.encode()).hexdigest()

            items.append({
                'title': text[:100],  # Limitar tamanho
                'url': full_url,
                'hash': item_hash
            })

        print(f"   ✅ {len(items)} itens encontrados")
        return items

    except requests.Timeout:
        print(f"   ⚠️ Timeout ao acessar {section_name}")
        return []
    except Exception as e:
        print(f"   ❌ Erro ao acessar {section_name}: {str(e)[:50]}")
        return []

def create_todoist_task(title, url, section_name, priority, label):
    """Cria tarefa no Todoist"""
    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
        "Content-Type": "application/json"
    }

    # Limpar título (remover caracteres problemáticos)
    clean_title = title.replace('\n', ' ').replace('\t', ' ').strip()
    clean_title = ' '.join(clean_title.split())  # Remover espaços múltiplos

    payload = {
        "content": f"{section_name}: {clean_title}",
        "description": f"🔗 Link: {url}\n\n📅 Adicionado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n🏷️ Seção: {section_name}",
        "priority": priority,
        "labels": ["jw.org", label]
    }

    try:
        response = requests.post(
            "https://api.todoist.com/rest/v2/tasks",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"      ❌ Erro ao criar tarefa: {str(e)[:50]}")
        return None

def main():
    """Função principal"""
    print("=" * 70)
    print("🔍 JW.ORG SCRAPER COMPLETO → TODOIST")
    print(f"📅 Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)
    print()

    # Carregar estado
    state = load_state()

    total_new = 0

    # Processar cada seção
    for section_key, section_config in SECTIONS.items():
        print(f"🔎 {section_config['name']}")

        # Obter estado anterior desta seção
        section_state = state.get(section_key, {'seen_hashes': []})
        seen_hashes = section_state.get('seen_hashes', [])

        # Fazer scraping
        items = scrape_section(section_config['url'], section_config['name'])

        new_count = 0

        # Verificar novos itens
        for item in items:
            if item['hash'] not in seen_hashes:
                print(f"   🆕 Novo: {item['title'][:55]}...")

                # Criar tarefa
                task = create_todoist_task(
                    item['title'],
                    item['url'],
                    section_config['name'],
                    section_config['priority'],
                    section_config['label']
                )

                if task:
                    print(f"      ✅ Tarefa criada (ID: {task['id']})")
                    new_count += 1
                    total_new += 1
                    seen_hashes.append(item['hash'])

        if new_count == 0:
            print(f"   ℹ️ Nenhum conteúdo novo")

        # Limitar histórico (últimos 100 itens por seção)
        seen_hashes = seen_hashes[-100:]

        # Atualizar estado da seção
        section_state['seen_hashes'] = seen_hashes
        section_state['last_check'] = datetime.now().isoformat()
        state[section_key] = section_state

        print()

    # Salvar estado geral
    state['last_run'] = datetime.now().isoformat()
    save_state(state)

    print("=" * 70)
    print(f"✅ FINALIZADO: {total_new} nova(s) tarefa(s) criada(s)")
    print("=" * 70)

if __name__ == "__main__":
    main()
