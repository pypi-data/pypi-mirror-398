import yaml
import glob
import os

repo_root = os.path.dirname(os.path.dirname(__file__))
examples_dir = os.path.join(repo_root, 'examples')

problems = []

for path in glob.glob(os.path.join(examples_dir, '**', '*.y*ml'), recursive=True):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
    except Exception as e:
        # skip files we can't parse
        continue
    if not content or 'agents' not in content:
        continue
    for agent in content['agents']:
        if not isinstance(agent, dict):
            continue
        if agent.get('type') == 'local_llm':
            # provider and model_url can be top-level keys or under params
            provider = agent.get('provider')
            model_url = agent.get('model_url')
            params = agent.get('params') or {}
            if not provider and 'provider' in params:
                provider = params.get('provider')
            if not model_url and 'model_url' in params:
                model_url = params.get('model_url')
            if not provider or not model_url:
                problems.append({'file': os.path.relpath(path, repo_root), 'agent_id': agent.get('id'), 'provider': provider, 'model_url': model_url})

if problems:
    print('Found local_llm agents missing provider or model_url:')
    for p in problems:
        print(f"- {p['file']} -> agent '{p['agent_id']}' provider={p['provider']!r} model_url={p['model_url']!r}")
else:
    print('No issues found: all local_llm agents specify provider and model_url')
