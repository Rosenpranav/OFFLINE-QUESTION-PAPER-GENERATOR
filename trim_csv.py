from pathlib import Path
p = Path(__file__).parents[1] / 'data' / 'question_bank.csv'
text = p.read_text(encoding='utf-8')
# Split into lines, remove trailing blank lines
lines = text.splitlines()
while lines and lines[-1].strip() == '':
    lines.pop()
# Write back with single newline at end
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Trimmed trailing blank lines. Total lines now:', len(lines))
