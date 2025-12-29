from src.helpers.comparison import fuzzy_intersection

# Your false positive examples
test_cases = [
    (['functools', 'text', 'collections'], ['Status', 'Context', 'Options', 'Decision']),
    (['pack', 'tags', 'convert', 'unpack'], ['Status', 'Context', 'Consequences']),
    (['compat', 'tests', 'command', 'compilers'], ['Security-Fragen', 'Compliance', 'Datenschutz']),
    (['compat', 'tests', 'command', 'compilers'], ['Cloud Provider', 'Compliance', 'CostReference']),
    (['AbrechnungsId', 'SystemId', 'Abrechnungsdaten'], ['ILV', 'KVT', 'Kundenabrechnung', 'Technische Sicht']),
]

print('Testing false positive cases (all should be False):')
print('='*60)
for i, (files, docs) in enumerate(test_cases, 1):
    result = fuzzy_intersection(files, docs, debug=False)
    status = 'PASS' if not result else 'FAIL (false positive)'
    print(f'{i}. {status}')
    print(f'   Files: {files}')
    print(f'   Docs:  {docs}')
    print(f'   Result: {result}')
    print()
