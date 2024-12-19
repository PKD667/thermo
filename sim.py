from random import random
import math
import time

import concurrent.futures

from particle import ParticleSpecies, Particle2D

class Wall:

    def __init__(self, surface):
        self.surface = surface
        self.collisions = []
        self.collisions_times = []

        self.temperature_factor = 1

        self.caloric_energy = 0
    
    def add_collision(self,ke):
        
        given_energy = (self.temperature_factor-1) * ke
        #print("Given energy: ", given_energy)
        #print("Wall with energy ", self.caloric_energy)
        if given_energy > self.caloric_energy:
            given_energy = self.caloric_energy
            self.caloric_energy = 0
            self.temperature_factor = 1
        else:
            self.caloric_energy -= given_energy


        #print("Temperature factor: ", self.temperature_factor)       

        self.collisions.append(ke)
        self.collisions_times.append(time.time())

    def heat(self,energy,speed_factor=0.001):
        self.caloric_energy += energy
        self.temperature_factor = 1 + speed_factor

        print("Heating wall with energy ", energy)
        print("Temperature factor: ", self.temperature_factor)


class Box2D:
    def __init__(self,height,width,cell_size=5):
        self.height = height
        self.width = width

        #define the walls
        self.walls = [
            Wall(height),
            Wall(width),
            Wall(height),
            Wall(width)
        ]

        self.particles = []
        self.species = {}

        self.t = 0

        self.cell_size = cell_size

        self.thread_count = 16
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_count)

    
    def add_particle(self,particle):
        self.particles.append(particle)
        if particle.s not in self.species:
            self.add_species(particle.s)
        
        self.species[particle.s.name].append(particle)

    def add_species(self,species):
        self.species[species.name] = []

    def apply_collision_equation(self, p1, p2):
        # Normal vector from p1 to p2
        nx = p2.x - p1.x
        ny = p2.y - p1.y
        # Normalize
        norm = math.sqrt(nx*nx + ny*ny)
        nx /= norm
        ny /= norm

        # Project velocities onto normal
        v1n = p1.vx*nx + p1.vy*ny
        v2n = p2.vx*nx + p2.vy*ny

        # Tangential components
        tx = -ny  # perpendicular to normal
        ty = nx
        v1t = p1.vx*tx + p1.vy*ty
        v2t = p2.vx*tx + p2.vy*ty

        # Apply 1D collision along normal
        m1, m2 = p1.s.mass, p2.s.mass
        v1n_after = (v1n*(m1-m2) + 2*m2*v2n)/(m1+m2)
        v2n_after = (2*m1*v1n + v2n*(m2-m1))/(m1+m2)

        # Reconstruct velocities
        p1.vx = v1n_after*nx + v1t*tx
        p1.vy = v1n_after*ny + v1t*ty
        p2.vx = v2n_after*nx + v2t*tx
        p2.vy = v2n_after*ny + v2t*ty

    def apply_wall_collision(self,particle):

        # compute the energy of the collision
        energy = 0.5*particle.s.mass*(particle.vx**2 + particle.vy**2)

        # right wall
        if particle.x + particle.s.radius > self.width:
            particle.vx = -particle.vx * self.walls[1].temperature_factor
            self.walls[1].add_collision(energy)
            particle.x = self.width - particle.s.radius
        
        # left wall
        if particle.x - particle.s.radius < 0:
            particle.vx = -particle.vx * self.walls[3].temperature_factor
            self.walls[3].add_collision(energy)
            particle.x = particle.s.radius
        
        # top wall
        if particle.y + particle.s.radius > self.height:
            particle.vy = -particle.vy * self.walls[2].temperature_factor
            self.walls[2].add_collision(energy)
            particle.y = self.height - particle.s.radius
        
        # bottom wall
        if particle.y - particle.s.radius < 0:
            particle.vy = -particle.vy * self.walls[0].temperature_factor
            self.walls[0].add_collision(energy)
            particle.y = particle.s.radius
    
    def collide_walls(self):
        # compute wall collisions
        for particle in self.particles:
            if particle.x - particle.s.radius < 0 or particle.x + particle.s.radius > self.width:
                self.apply_wall_collision(particle)
            if particle.y - particle.s.radius < 0 or particle.y + particle.s.radius > self.height:
                self.apply_wall_collision(particle)


    def assign_cells(self):
        # partition the space into cells
        x_cells = math.ceil(self.width/self.cell_size)
        y_cells = math.ceil(self.height/self.cell_size)

        cells = [[[] for _ in range(y_cells)] for _ in range(x_cells)]

        for particle in self.particles:
            x = int(particle.x/self.cell_size)
            y = int(particle.y/self.cell_size)
            cells[x][y].append(particle)

        return cells
    
    def collide_single_cell(self,cell):
        # compute wall collisions


        for i in range(len(cell)):
            for j in range(i+1,len(cell)):
                particle = cell[i]
                particle2 = cell[j]
                # check if the particles are colliding
                if math.sqrt((particle.x-particle2.x)**2 + (particle.y-particle2.y)**2) < particle.s.radius + particle2.s.radius:
                    self.apply_collision_equation(particle,particle2)
    
    def collide_partitioned(self):

        self.collide_walls()

        cells = self.assign_cells()

        # cells is a 2D array of cells 
        # convert it to a 1D array
        cells = [cell for row in cells for cell in row]

        # multiple threads
        # for cell in cells:
        #     self.collide_single_cell(cell)

        self.executor.map(self.collide_single_cell,cells)
        


    def collide_all(self):
        # compute wall collisions
        self.collide_walls()

        # compute particle collisions
        cells = self.assign_cells()

        # already computed collisions
        computed_collisions = set()

        for i in range(len(cells)):
            # for each cell compute collisions with the adjacent cells
            for j in range(len(cells[i])):
                for particle in cells[i][j]:
                    # check for collisions with the adjacent cells
                    for i2 in range(max(0,i-1),min(i+2,len(cells))):
                        for j2 in range(max(0,j-1),min(j+2,len(cells[i2]))):
                            for particle2 in cells[i2][j2]:
                                if particle is not particle2 and (particle,particle2) not in computed_collisions and (particle2,particle) not in computed_collisions:
                                    # check if the particles are colliding
                                    if math.sqrt((particle.x-particle2.x)**2 + (particle.y-particle2.y)**2) < particle.s.radius + particle2.s.radius:
                                        self.apply_collision_equation(particle,particle2)
                                        computed_collisions.add((particle,particle2))
    
    def collide_naive(self):
        self.collide_walls()

        # collide particules without caring about cells or whatevr
        for i in range(len(self.particles)):
            for j in range(i+1,len(self.particles)):
                 if math.sqrt((self.particles[i].x-self.particles[j].x)**2 + (self.particles[i].y-self.particles[j].y)**2) < self.particles[i].s.radius + self.particles[j].s.radius:
                    self.apply_collision_equation(self.particles[i],self.particles[j])
                
    collide = collide_all
    
    def update(self,dt):
        self.collide()

        for particle in self.particles:
            particle.update(dt)

        self.t += dt

    def get_ke(self):
        ke = 0
        for particle in self.particles:
            ke += 0.5*particle.s.mass*(particle.vx**2 + particle.vy**2)
        return ke

    def get_temperature(self):

        # Compute total kinetic energy
        total_ke = self.get_ke()
        
        # Compute temperature
        return total_ke/(len(self.particles))

    def get_pressure(self,window=100):
        surface = self.width*2 + self.height*2
        
        # get the time 100 secons ago
        t = time.time() - window
        # get the collisions in the window
        collisions = [wall.collisions[i] for wall in self.walls for i in range(len(wall.collisions)) if wall.collisions_times[i] > t]
        # compute the pressure
        return sum(collisions)/(surface*window)

    def get_volume(self):
        return self.width*self.height
    

    # Thermodynamic transformations
    
    def transform(self, dx, dy,dt):
        # move right and bottom walls
        print("Transforming x in ", dx//dt)
        for i in range(abs(int(dx//dt))):
            self.width += dx*dt
            self.walls[1].surface = self.width
            self.update(dt)
        
        print("Transforming y in ", dy//dt)
        for i in range(abs(int(dy//dt))):
            self.height += dy*dt
            self.walls[2].surface = self.height
            self.update(dt)
    
    def heat(self,wall_index,energy,speed_factor=0.1):
        self.walls[wall_index].heat(energy,speed_factor)


import pygame
class BoxRenderer:
    def __init__(self,box,scaling=5):
        self.box = box
        self.screen = pygame.display.set_mode((box.width*scaling,box.height*scaling))
        self.scaling = scaling

    def render(self):

        self.screen.fill((255,255,255))

        # Draw grid
        for i in range(0,int(self.box.width),self.box.cell_size):
            pygame.draw.line(self.screen,(200,200,200),(i*self.scaling,0),(i*self.scaling,self.box.height*self.scaling))
        for i in range(0,int(self.box.height),self.box.cell_size):
            pygame.draw.line(self.screen,(200,200,200),(0,i*self.scaling),(self.box.width*self.scaling,i*self.scaling))


        for particle in self.box.particles:
            pygame.draw.circle(self.screen,particle.s.color,(int(particle.x*self.scaling),int(particle.y*self.scaling)),int(particle.s.radius*self.scaling))


        # Draw walls 5 pixels wide
        pygame.draw.rect(self.screen, (0,0,0), (0,0,self.box.width*self.scaling,self.box.height*self.scaling), 2)

        pygame.display.flip()
