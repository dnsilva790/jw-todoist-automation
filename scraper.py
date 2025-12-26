#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JW.ORG Scraper ROBUSTO → Todoist
Versão: 4.0 - Anti-timeout + Retry
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
import time

# ============================================================
# CONFIGURAÇÕES
# ============================================================

TODOIST_TOKEN = os.environ['TODOIST_TOKEN']
STATE_FILE = 'state.json'

# Timeout e retry
REQUEST_TIMEOUT = 60  # 60 segundos
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 3  # 3 segundos entre requests

# Seções para monitorar
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
    """Carrega estado anterior"""
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    """Salva estado atual"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_realistic_headers():
    """Headers mais realistas para evitar bloqueio"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

def fetch_with_retry(url, max_retries=MAX_RETRIES):
    """Faz request com retry automático"""
    headers = get_realistic_headers()

    for attempt in range(1, max_retries + 1):
        try:
            print(f"      Tentativa {attempt}/{max_retries}...")

            response = requests.get(
                url, 
                headers=headers, 
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()

            print(f"      ✅ Sucesso! ({len(response.content)} bytes)")
            return response

        except requests.Timeout:
            print(f"      ⏱️ Timeout na tentativa {attempt}")
            if attempt < max_retries:
                wait_time = attempt * 5  # Espera progressiva: 5s, 10s, 15s
                print(f"      ⏳ Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)

        except requests.RequestException as e:
            print(f"      ❌ Erro: {str(e)[:50]}")
            if attempt < max_retries:
                time.sleep(5)

    return None

def scrape_section(url, section_name):
    """Extrai conteúdos de uma seção"""
    print(f"   📡 Acessando {section_name}...")

    response = fetch_with_retry(url)

    if not response:
        print(f"   ❌ Falha após {MAX_RETRIES} tentativas")
        return []

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a', href=True)

        items = []
        seen_urls = set()

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            if not text or len(text) < 15:
                continue

            # URL completa
            if href.startswith('/'):
                full_url = f"https://www.jw.org{href}"
            elif href.startswith('http'):
                full_url = href
            else:
                continue

            if 'jw.org' not in full_url:
                continue

            # Excluir navegação
            exclude = ['/contato', '/ajuda', '/idiomas', '/busca', '/sobre',
                      '/termos-de-uso', '/politica-de-privacidade', '/copyright',
                      'javascript:', '#']

            if any(ex in href.lower() for ex in exclude):
                continue

            if full_url in seen_urls:
                continue

            seen_urls.add(full_url)

            items.append({
                'title': text[:100],
                'url': full_url,
                'hash': hashlib.md5(full_url.encode()).hexdigest()
            })

        print(f"   ✅ {len(items)} itens encontrados")
        return items

    except Exception as e:
        print(f"   ❌ Erro no parsing: {str(e)[:50]}")
        return []

def create_todoist_task(title, url, section_name, priority, label):
    """Cria tarefa no Todoist"""
    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
        "Content-Type": "application/json"
    }

    clean_title = title.replace('\n', ' ').replace('\t', ' ').strip()
    clean_title = ' '.join(clean_title.split())

    payload = {
        "content": f"{section_name}: {clean_title}",
        "description": f"🔗 {url}\n\n📅 Adicionado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n🏷️ Seção: {section_name}",
        "priority": priority,
        "labels": ["jw-org", label]
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
    print("🔍 JW.ORG SCRAPER ROBUSTO → TODOIST")
    print(f"📅 Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⚙️ Timeout: {REQUEST_TIMEOUT}s | Retries: {MAX_RETRIES}")
    print("=" * 70)
    print()

    state = load_state()
    total_new = 0

    for section_key, section_config in SECTIONS.items():
        print(f"🔎 {section_config['name']}")

        section_state = state.get(section_key, {'seen_hashes': []})
        seen_hashes = section_state.get('seen_hashes', [])

        # Scraping
        items = scrape_section(section_config['url'], section_config['name'])

        new_count = 0

        for item in items:
            if item['hash'] not in seen_hashes:
                print(f"   🆕 Novo: {item['title'][:55]}...")

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

        # Limitar histórico
        seen_hashes = seen_hashes[-100:]

        section_state['seen_hashes'] = seen_hashes
        section_state['last_check'] = datetime.now().isoformat()
        state[section_key] = section_state

        # Delay entre seções
        if section_key != list(SECTIONS.keys())[-1]:  # Não esperar na última
            print(f"   ⏳ Aguardando {DELAY_BETWEEN_REQUESTS}s...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

        print()

    state['last_run'] = datetime.now().isoformat()
    save_state(state)

    print("=" * 70)
    print(f"✅ FINALIZADO: {total_new} nova(s) tarefa(s) criada(s)")
    print("=" * 70)

if __name__ == "__main__":
    main()

