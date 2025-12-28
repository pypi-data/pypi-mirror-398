class Seeder:
    """Base class for database seeders"""

    def run(self, db):
        """Override this method to define seeding logic"""
        raise NotImplementedError("Seeder must implement run() method")


class SeederRegistry:
    """Registry for managing seeders"""

    _seeders = []

    @classmethod
    def register(cls, seeder_class):
        """Register a seeder"""
        cls._seeders.append(seeder_class)
        return seeder_class

    @classmethod
    def run_all(cls, db):
        """Run all registered seeders"""
        for seeder_class in cls._seeders:
            seeder = seeder_class()
            print(f"Running seeder: {seeder_class.__name__}")
            seeder.run(db)


def seeder(cls):
    """Decorator to register a seeder"""
    SeederRegistry.register(cls)
    return cls
