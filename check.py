with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines[42:80], 43):
    print(i, l.rstrip())