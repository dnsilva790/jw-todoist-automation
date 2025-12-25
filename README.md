# 🔔 JW.ORG → Todoist Automático

Monitora automaticamente atualizações no jw.org e cria tarefas no Todoist.

## 📋 Como Configurar

### 1. Fork este repositório

Clique em "Fork" no canto superior direito do GitHub.

### 2. Adicionar Token do Todoist

1. Vá em **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret**
3. Nome: `TODOIST_TOKEN`
4. Valor: `176f894d399b02b2a765c31bd210c138157425c3`
5. Salvar

### 3. Ativar GitHub Actions

1. Vá na aba **Actions**
2. Clique em "I understand my workflows, go ahead and enable them"

### 4. Testar execução manual

1. Na aba **Actions**, clique no workflow "JW.ORG Scraper"
2. Clique em "Run workflow"
3. Aguarde execução (1-2 minutos)
4. Verifique tarefas criadas no Todoist

## ⚙️ Configuração

### Horários de execução

Atualmente roda **2x por dia**:
- 09:00 (horário de Brasília)
- 18:00 (horário de Brasília)

Para alterar, edite o arquivo `.github/workflows/scraper.yml`:

```yaml
schedule:
  - cron: '0 6,15 * * *'  # Altere os números aqui
```

### Páginas monitoradas

- 📖 A Sentinela
- 📖 Despertai
- 🎥 Vídeos JW.org

Para adicionar mais, edite `scraper.py` na seção `PAGES`.

## 📊 Status

O scraper armazena estado em `state.json` para evitar duplicatas.

## 🐛 Problemas?

- Verifique os logs em **Actions** → última execução
- Confirme que o token está correto
- Teste execução manual primeiro
