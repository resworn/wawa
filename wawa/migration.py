# migration.py - simple script to replace 'wawa' with 'wawa' in files
import os
for root, dirs, files in os.walk('.'):
    for name in files:
        if name.endswith('.py') or name.endswith('.json') or name.endswith('.md'):
            path = os.path.join(root, name)
            try:
                s = open(path, 'r', encoding='utf-8').read()
                s2 = s.replace('wawa', 'wawa')
                if s != s2:
                    open(path, 'w', encoding='utf-8').write(s2)
            except Exception as e:
                print('skip', path, e)
