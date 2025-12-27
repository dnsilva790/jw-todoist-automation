import requests
import json
import os
from datetime import datetime

# Todoist API
TODOIST_TOKEN = os.environ.get("TODOIST_TOKEN")
TODOIST_API = "https://api.todoist.com/rest/v2/tasks"

# JW.org CDN API
JW_BASE = "https://b.jw-cdn.org/apis/mediator/v1"

# Categorias de vídeos para monitorar
VIDEO_CATEGORIES = {
    "LatestVideos": {
        "name": "🎬 Novos Vídeos",
        "priority": 3,
        "label": "jw-videos"
    },
    "VODStudio": {
        "name": "📺 JW Broadcasting",
        "priority": 2,
        "label": "jw-broadcasting"
    },
    "VODBibleTeachings": {
        "name": "📖 Ensinos Bíblicos",
        "priority": 3,
        "label": "jw-teachings"
    },
    "VODMovies": {
        "name": "🎥 Filmes",
        "priority": 4,
        "label": "jw-movies"
    },
    "VODChildren": {
        "name": "👶 Crianças",
        "priority": 3,
        "label": "jw-kids"
    },
    "VODProgramsEvents": {
        "name": "🎪 Programas e Eventos",
        "priority": 3,
        "label": "jw-programs"
    },
    "MidweekMeeting": {
        "name": "📅 Reunião Meio de Semana",
        "priority": 1,
        "label": "jw-meeting"
    }
}

# Arquivo para rastrear vídeos já processados
TRACKING_FILE = "jw_videos_tracked.json"

def load_tracked_videos():
    """Carrega lista de vídeos já processados"""
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tracked_videos(tracked):
    """Salva lista de vídeos processados"""
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracked, f, indent=2, ensure_ascii=False)

def fetch_videos(category):
    """Busca vídeos de uma categoria"""
    url = f"{JW_BASE}/categories/T/{category}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar {category}: {e}")
        return None

def create_todoist_task(title, description, priority, label):
    """Cria tarefa no Todoist"""
    headers = {
        "Authorization": f"Bearer {TODOIST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "content": title,
        "description": description,
        "priority": priority,
        "labels": [label]
    }
    
    try:
        response = requests.post(TODOIST_API, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao criar tarefa: {e}")
        return None

def process_videos():
    """Processa vídeos de todas as categorias"""
    
    print(f"🔍 JW.ORG VÍDEOS SCRAPER")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)
    print()
    
    tracked = load_tracked_videos()
    new_tasks_count = 0
    
    for category, cat_info in VIDEO_CATEGORIES.items():
        print(f"📡 {cat_info['name']}")
        
        data = fetch_videos(category)
        
        if not data or 'category' not in data:
            print(f"   ❌ Nenhum conteúdo")
            print()
            continue
        
        videos = data['category'].get('media', [])
        print(f"   📊 {len(videos)} vídeos encontrados")
        
        if not videos:
            print()
            continue
        
        # Processar vídeos (máximo 5 mais recentes por categoria)
        for video in videos[:5]:
            video_key = video.get('languageAgnosticNaturalKey', video.get('title', ''))
            
            if video_key in tracked:
                continue
            
            title = video.get('title', 'Sem título')
            first_published = video.get('firstPublished', datetime.now().isoformat())
            
            description = f"""🎬 {cat_info['name']}

📌 {title}
📅 {first_published}

🔗 Categoria: {category}
🏷️ Etiqueta: {cat_info['label']}

---
⚙️ Criado automaticamente por JW Scraper"""
            
            print(f"   ✅ Novo: {title[:50]}...")
            task = create_todoist_task(
                title=f"{cat_info['name']} - {title}",
                description=description,
                priority=cat_info['priority'],
                label=cat_info['label']
            )
            
            if task:
                tracked[video_key] = {
                    'title': title,
                    'category': category,
                    'date_tracked': datetime.now().isoformat()
                }
                new_tasks_count += 1
        
        print()
    
    save_tracked_videos(tracked)
    
    print("=" * 70)
    print(f"✅ FINALIZADO: {new_tasks_count} nova(s) tarefa(s) criada(s)")
    print("=" * 70)

if __name__ == "__main__":
    if not TODOIST_TOKEN:
        print("❌ ERRO: Variável TODOIST_TOKEN não configurada!")
        exit(1)
    
    process_videos()
