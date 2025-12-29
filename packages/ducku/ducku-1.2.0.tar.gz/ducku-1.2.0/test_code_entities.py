from src.core.code.dispatcher import collect_code_entities_from_content

# Test Python code
python_code = """
class MyClass:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self, message):
        return f"Hello {self.name}: {message}"

def standalone_function(param1, param2, param3):
    return param1 + param2

def another_function():
    pass
"""

entities = []
collect_code_entities_from_content(python_code, entities, "test.py")

print(f"Total containers: {len(entities)}")
for container in entities:
    entity_names = [str(e) for e in container.entities]
    print(f"\n{container.type} ({container.parent}):")
    print(f"  Entities: {entity_names}")
