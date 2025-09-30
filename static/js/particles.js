/**
 * Static Particle System v3
 * Statické particle, které se pohybují v rámci obrazovky
 */

class ParticleSystem {
    constructor() {
        this.container = null;
        this.particles = [];
        this.maxParticles = 180; // Více particle pro hustší pozadí
        this.animationTypes = [
            'float-up', 'float-down', 'float-left', 'float-right',
            'diagonal-1', 'diagonal-2', 'diagonal-3', 'diagonal-4',
            'circle', 'wave'
        ];
        this.init();
    }

    init() {
        // Vytvoř container pro particle
        this.container = document.createElement('div');
        this.container.className = 'particles-container';
        document.body.appendChild(this.container);

        // Generuj particle
        this.generateParticles();
    }

    generateParticles() {
        // Vyčisti existující particle
        this.container.innerHTML = '';

        // Generuj nové particle
        for (let i = 0; i < this.maxParticles; i++) {
            this.createParticle(i);
        }
    }

    createParticle(index) {
        const particle = document.createElement('div');
        
        // Náhodné vlastnosti - menší particle
        const size = Math.random() * 5 + 2; // 1-10px
        const animationType = this.animationTypes[Math.floor(Math.random() * this.animationTypes.length)];
        const delay = Math.random() * 5; // 0-5s delay (kratší)
        const duration = Math.random() * 8 + 6; // 6-14s duration (kratší)
        
        // Nastav třídy
        particle.className = `particle ${animationType}`;
        
        // Aplikuj styly
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.animationDelay = delay + 's';
        particle.style.animationDuration = duration + 's';
        
        // Náhodná průhlednost - jemnější pro menší particle
        const opacity = Math.random() * 0.08 + 0.02; // 0.02-0.10
        particle.style.background = `rgba(255, 255, 255, ${opacity})`;
        
        // Statická pozice v rámci obrazovky
        this.setStaticPosition(particle);
        
        this.container.appendChild(particle);
    }

    setStaticPosition(particle) {
        // Náhodná pozice v rámci obrazovky (statická)
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
    }

    // Metoda pro restart particle (volitelné)
    restart() {
        this.generateParticles();
    }

    // Metoda pro změnu počtu particle
    setParticleCount(count) {
        this.maxParticles = Math.max(10, Math.min(150, count));
        this.generateParticles();
    }
}

// Inicializuj particle systém když je DOM ready
document.addEventListener('DOMContentLoaded', function() {
    window.particleSystem = new ParticleSystem();
});

// Export pro moduly
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParticleSystem;
}
