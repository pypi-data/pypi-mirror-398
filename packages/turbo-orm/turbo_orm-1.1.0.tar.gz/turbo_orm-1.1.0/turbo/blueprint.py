"""
Model Blueprints - AI-Powered Realistic Test Data Generation

Generate contextually appropriate test data based on your model definitions.
Unlike traditional factories, blueprints understand context and generate realistic data.
"""

import random
import datetime
import string


class Blueprint:
    """Base blueprint class"""

    STYLES = {
        "e-commerce": {
            "product_names": [
                "Wireless Headphones",
                "Running Shoes",
                "Smart Watch",
                "Laptop Bag",
                "Phone Case",
                "Water Bottle",
                "Yoga Mat",
                "Desk Lamp",
                "Keyboard",
                "Coffee Maker",
                "Backpack",
                "Sunglasses",
                "Notebook",
                "Power Bank",
            ],
            "categories": ["Electronics", "Fashion", "Sports", "Home", "Office"],
            "price_range": (9.99, 999.99),
        },
        "social": {
            "post_titles": [
                "Just finished an amazing workout!",
                "Check out this sunset",
                "New project launch",
                "Weekend vibes",
                "Thoughts on AI",
                "Best coffee in town",
                "Travel memories",
                "Coding tips",
            ],
            "hashtags": ["#life", "#tech", "#fitness", "#travel", "#food", "#art"],
            "reactions": ["like", "love", "wow", "haha", "sad", "angry"],
        },
        "finance": {
            "transaction_types": ["deposit", "withdrawal", "transfer", "payment"],
            "categories": [
                "groceries",
                "rent",
                "utilities",
                "entertainment",
                "savings",
            ],
            "amount_range": (5.00, 5000.00),
        },
        "healthcare": {
            "conditions": ["Checkup", "Flu", "Injury", "Chronic Care", "Emergency"],
            "departments": ["Cardiology", "Neurology", "Pediatrics", "Orthopedics"],
            "priorities": ["Low", "Medium", "High", "Critical"],
        },
    }

    FIRST_NAMES = [
        "Emma",
        "Liam",
        "Olivia",
        "Noah",
        "Ava",
        "Ethan",
        "Sophia",
        "Mason",
        "Isabella",
        "William",
        "Mia",
        "James",
        "Charlotte",
        "Benjamin",
        "Amelia",
        "Lucas",
        "Harper",
        "Henry",
        "Evelyn",
        "Alexander",
    ]

    LAST_NAMES = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
        "Gonzalez",
        "Wilson",
        "Anderson",
        "Thomas",
        "Taylor",
        "Moore",
        "Jackson",
        "Martin",
    ]

    def __init__(self, model_class, style="general"):
        self.model_class = model_class
        self.style = style
        self.counter = 0

    def generate(self, db, count=1, **overrides):
        """Generate realistic model instances"""
        instances = []

        for i in range(count):
            self.counter += 1
            data = self._generate_data(overrides)
            instance = self.model_class(**data)
            instance.save(db)
            instances.append(instance)

        print(f"✓ Generated {count} {self.model_class.__name__} instances")
        return instances

    def _generate_data(self, overrides):
        """Generate data for one instance"""
        data = {}

        for field_name, field in self.model_class._fields.items():
            if field.__class__.__name__ == "ManyToManyField":
                continue  # Skip M2M

            if field_name in overrides:
                data[field_name] = overrides[field_name]
            else:
                data[field_name] = self._generate_field_value(field_name, field)

        return data

    def _generate_field_value(self, field_name, field):
        """Generate value for a specific field"""
        field_type = field.__class__.__name__

        # Context-aware generation
        if "name" in field_name.lower():
            if "first" in field_name.lower():
                return random.choice(self.FIRST_NAMES)
            elif "last" in field_name.lower():
                return random.choice(self.LAST_NAMES)
            elif "user" in field_name.lower() or "person" in field_name.lower():
                return f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}"
            elif self.style == "e-commerce" and "product" in field_name.lower():
                return random.choice(self.STYLES["e-commerce"]["product_names"])
            else:
                return f"{random.choice(self.FIRST_NAMES)} {self.counter}"

        elif "email" in field_name.lower():
            name = random.choice(self.FIRST_NAMES).lower()
            domain = random.choice(
                ["gmail.com", "yahoo.com", "outlook.com", "company.com"]
            )
            return f"{name}{self.counter}@{domain}"

        elif "title" in field_name.lower():
            if self.style == "social":
                return random.choice(self.STYLES["social"]["post_titles"])
            return f"Title {self.counter}"

        elif "description" in field_name.lower() or "content" in field_name.lower():
            templates = [
                "This is a great example of quality content.",
                "Interesting information about this topic.",
                "Check out these amazing details.",
                "Everything you need to know about this.",
            ]
            return random.choice(templates)

        elif "price" in field_name.lower() or "amount" in field_name.lower():
            if self.style == "e-commerce":
                min_val, max_val = self.STYLES["e-commerce"]["price_range"]
            else:
                min_val, max_val = 10, 1000
            return round(random.uniform(min_val, max_val), 2)

        elif "age" in field_name.lower():
            return random.randint(18, 80)

        elif "priority" in field_name.lower():
            return random.randint(1, 3)

        elif "status" in field_name.lower():
            return random.choice(["active", "inactive", "pending", "completed"])

        elif field_type == "TextField":
            return f"{field_name}_{self.counter}"

        elif field_type == "IntegerField":
            return random.randint(1, 100)

        elif field_type == "FloatField":
            return round(random.uniform(1, 100), 2)

        elif field_type == "BooleanField":
            return random.choice([True, False])

        elif field_type == "DateTimeField":
            days_ago = random.randint(0, 365)
            return datetime.datetime.now() - datetime.timedelta(days=days_ago)

        elif field_type == "JSONField":
            return {"generated": True, "index": self.counter}

        return None


def blueprint(style="general"):
    """Decorator to add blueprint functionality to a model"""

    def decorator(cls):
        @classmethod
        def generate_realistic_data(model_cls, db, count=1, **kwargs):
            """Generate realistic test data"""
            bp = Blueprint(model_cls, style=style)
            return bp.generate(db, count, **kwargs)

        cls.generate_realistic_data = generate_realistic_data
        return cls

    return decorator
