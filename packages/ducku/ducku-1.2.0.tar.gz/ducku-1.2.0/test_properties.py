from src.core.code.dispatcher import collect_code_entities_from_content

# Test Python code with properties
python_code = """
class Person:
    def __init__(self, name):
        self.name = name
        self.age = 0
        self.email = None
    
    def set_contact(self, email, phone):
        self.email = email
        self.phone = phone
"""

entities = []
collect_code_entities_from_content(python_code, entities, "person.py")

print(f"Total containers: {len(entities)}")
for container in entities:
    entity_names = [str(e) for e in container.entities]
    print(f"\n{container.type} ({container.parent}):")
    print(f"  Entities: {entity_names}")
