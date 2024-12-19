class ParticleSpecies :
    def __init__(self, mass, radius,name, color) :
        self.mass = mass
        self.radius = radius
        self.name = name
        self.color = color
    
    def __str__(self) :
        return f"{self.name} with mass {self.mass} and radius"

class Particle2D :
    def __init__(self, x, y, vx, vy, species) :
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

        self.s = species


    def __str__(self) :
        return f"({self.x}, {self.y})"
    
    def update(self, dt) :
        self.x += self.vx * dt
        self.y += self.vy * dt