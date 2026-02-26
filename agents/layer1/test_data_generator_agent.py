"""ContractIQ Test Data Generator Agent - Layer 1

Generates contextual, domain-aware test data for API and UI tests.
Supports data generation from specs, schemas, and AI-based realistic data.
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid


class TestDataGeneratorAgent:
    """
    Layer 1 Orchestrator: Test Data Generator Agent
    
    Responsibilities:
    - Parse data schemas from OpenAPI/GraphQL specs
    - Generate realistic test data based on field types and constraints
    - Create boundary value test cases
    - Support data templates and AI-generated contextual data
    - Handle relationships and dependencies between data fields
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_generators = self._initialize_generators()
        self.templates = {}
        
    def _initialize_generators(self) -> Dict[str, callable]:
        """Initialize type-specific data generators."""
        return {
            'string': self._generate_string,
            'integer': self._generate_integer,
            'number': self._generate_number,
            'boolean': self._generate_boolean,
            'email': self._generate_email,
            'url': self._generate_url,
            'uuid': lambda: str(uuid.uuid4()),
            'date': self._generate_date,
            'datetime': self._generate_datetime,
            'phone': self._generate_phone,
        }
    
    def generate_from_schema(self, schema: Dict[str, Any], 
                            count: int = 1) -> List[Dict[str, Any]]:
        """
        Generate test data from a JSON schema.
        
        Args:
            schema: JSON schema defining data structure
            count: Number of data instances to generate
            
        Returns:
            List of generated data dictionaries
        """
        generated_data = []
        
        for _ in range(count):
            instance = self._generate_object_from_schema(schema)
            generated_data.append(instance)
            
        return generated_data
    
    def _generate_object_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single object instance from schema."""
        obj = {}
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        for field_name, field_schema in properties.items():
            if field_name in required_fields or random.random() > 0.3:
                obj[field_name] = self._generate_value(field_schema)
                
        return obj
    
    def _generate_value(self, field_schema: Dict[str, Any]) -> Any:
        """Generate value based on field schema."""
        field_type = field_schema.get('type', 'string')
        field_format = field_schema.get('format')
        
        # Use format-specific generator if available
        if field_format and field_format in self.data_generators:
            return self.data_generators[field_format]()
        
        # Use type-specific generator
        if field_type in self.data_generators:
            return self.data_generators[field_type](field_schema)
        
        return None
    
    def _generate_string(self, schema: Dict[str, Any]) -> str:
        """Generate string value."""
        min_length = schema.get('minLength', 5)
        max_length = schema.get('maxLength', 20)
        pattern = schema.get('pattern')
        enum_values = schema.get('enum')
        
        if enum_values:
            return random.choice(enum_values)
        
        if pattern:
            # Basic pattern support - can be extended
            return f"pattern_match_{random.randint(1000, 9999)}"
        
        length = random.randint(min_length, max_length)
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))
    
    def _generate_integer(self, schema: Dict[str, Any]) -> int:
        """Generate integer value."""
        minimum = schema.get('minimum', 0)
        maximum = schema.get('maximum', 1000)
        return random.randint(minimum, maximum)
    
    def _generate_number(self, schema: Dict[str, Any]) -> float:
        """Generate float value."""
        minimum = schema.get('minimum', 0.0)
        maximum = schema.get('maximum', 1000.0)
        return round(random.uniform(minimum, maximum), 2)
    
    def _generate_boolean(self, schema: Dict[str, Any] = None) -> bool:
        """Generate boolean value."""
        return random.choice([True, False])
    
    def _generate_email(self) -> str:
        """Generate realistic email address."""
        domains = ['example.com', 'test.com', 'demo.org', 'sample.net']
        username = f"user{random.randint(100, 999)}"
        return f"{username}@{random.choice(domains)}"
    
    def _generate_url(self) -> str:
        """Generate URL."""
        protocols = ['https']
        domains = ['api.example.com', 'service.test.io', 'app.demo.org']
        paths = ['users', 'products', 'orders', 'items']
        return f"{random.choice(protocols)}://{random.choice(domains)}/{random.choice(paths)}"
    
    def _generate_date(self) -> str:
        """Generate date in ISO format."""
        days_offset = random.randint(-365, 365)
        date = datetime.now() + timedelta(days=days_offset)
        return date.strftime('%Y-%m-%d')
    
    def _generate_datetime(self) -> str:
        """Generate datetime in ISO format."""
        days_offset = random.randint(-365, 365)
        dt = datetime.now() + timedelta(days=days_offset)
        return dt.isoformat()
    
    def _generate_phone(self) -> str:
        """Generate phone number."""
        return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
    
    def generate_boundary_values(self, field_schema: Dict[str, Any]) -> List[Any]:
        """
        Generate boundary value test cases.
        
        Args:
            field_schema: Schema for the field
            
        Returns:
            List of boundary values
        """
        field_type = field_schema.get('type', 'string')
        values = []
        
        if field_type == 'integer':
            minimum = field_schema.get('minimum', 0)
            maximum = field_schema.get('maximum', 100)
            values = [minimum, minimum + 1, maximum - 1, maximum]
            
        elif field_type == 'string':
            min_length = field_schema.get('minLength', 0)
            max_length = field_schema.get('maxLength', 100)
            values = [
                'a' * min_length,
                'a' * (min_length + 1),
                'a' * (max_length - 1),
                'a' * max_length,
            ]
            
        return values
    
    def load_template(self, template_name: str, template_data: Dict[str, Any]):
        """Load a data generation template."""
        self.templates[template_name] = template_data
    
    def generate_from_template(self, template_name: str, count: int = 1) -> List[Dict[str, Any]]:
        """Generate data from a saved template."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        return self.generate_from_schema(template, count)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data generation statistics."""
        return {
            'total_templates': len(self.templates),
            'available_generators': list(self.data_generators.keys()),
            'agent_type': 'TestDataGeneratorAgent',
            'layer': 1,
        }


if __name__ == '__main__':
    # Example usage
    agent = TestDataGeneratorAgent()
    
    # Example schema
    user_schema = {
        'type': 'object',
        'properties': {
            'id': {'type': 'integer'},
            'name': {'type': 'string', 'minLength': 3, 'maxLength': 50},
            'email': {'type': 'string', 'format': 'email'},
            'age': {'type': 'integer', 'minimum': 18, 'maximum': 100},
            'active': {'type': 'boolean'},
        },
        'required': ['id', 'name', 'email']
    }
    
    # Generate test data
    test_data = agent.generate_from_schema(user_schema, count=3)
    print(json.dumps(test_data, indent=2))
