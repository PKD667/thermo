import math
import random
import time


from sim import Box2D, BoxRenderer
import pygame
from particle import Particle2D, ParticleSpecies




# Define the species
species = [
    ParticleSpecies(4, 2, "A", "red"),
    ParticleSpecies(1, 1, "B", "blue")
]

# random particles
n = 100
particles = []
for i in range(n):
    species_index = i % 2
    species_i = species[species_index]
    position = (random.uniform(0,100-species_i.radius), random.uniform(0,100-species_i.radius))
    # check if the particle is inside another particle
    while any([math.sqrt((p.x-position[0])**2 + (p.y-position[1])**2) < p.s.radius + species_i.radius for p in particles]):
        position = (random.uniform(0,100-species_i.radius), random.uniform(0,100-species_i.radius))
    particle = Particle2D(position[0], position[1], random.uniform(-1,1), random.uniform(-1,1), species_i)

    particles.append(particle)

# Create the box
box = Box2D(100,100)

# Add the particles to the box
for particle in particles:
    box.add_particle(particle)

# Create the renderer
renderer = BoxRenderer(box,scaling=5)

# Run the simulation
dt = 0.05
running = True
starttime = time.time()
ticks = 0


temps = []
pressures = []
volumes = []



while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                box.transform(-1, 0, dt)
            if event.key == pygame.K_RIGHT:
                box.transform(1, 0, dt)
            if event.key == pygame.K_UP:
                box.transform(0, -1, dt)
            if event.key == pygame.K_DOWN:
                box.transform(0, 1, dt)
            
            if event.key == pygame.K_h:
                print("Heating")
                box.heat(0,0.1)
                box.heat(1,0.1)
                box.heat(2,0.1)
                box.heat(3,0.1)

    box.update(dt)
    renderer.render()
    
    ticks += 1

    if ticks % 1000 == 0:

        print(f"ticks/s: {ticks/(time.time()-starttime)}")

        if ticks < 100000:
            continue
        P = box.get_pressure()
        V = box.get_volume()
        T = box.get_temperature()
        temps.append(T)
        pressures.append(P)
        volumes.append(V)
        print("Time:", box.t)
        print("Temperature:", T)
        print("Pressure:", P)
        print("Volume:", V)

        print("PV", P*V)

        print("PV / nT:", (P*V) / (n*T))


        

pygame.quit()



import matplotlib.pyplot as plt

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

# plot temperature, pressure, and volume in the same plot with different y axes
fig, ax1 = plt.subplots()

color1 = 'tab:red'
ax1.set_xlabel('time (s)')
ax1.set_ylabel('Temperature (K)', color=color1)
ax1.plot(temps, color=color1)

ax2 = ax1.twinx()
color2 = 'tab:blue'
ax2.set_ylabel('Pressure (Pa)', color=color2)
ax2.plot(pressures, color=color2)

ax3 = ax1.twinx()
ax3.spines['right'].set_position(('axes', 1.2))
make_patch_spines_invisible(ax3)
ax3.spines['right'].set_visible(True)

color3 = 'tab:green'
ax3.set_ylabel('Volume (m³)', color=color3)
ax3.plot(volumes, color=color3)

fig.tight_layout()
plt.show()