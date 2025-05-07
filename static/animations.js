// Animations and particle effects for quiz app

// Create particle background effect
function createParticleBackground() {
  const particlesContainer = document.createElement('div');
  particlesContainer.className = 'particles-background';
  document.body.appendChild(particlesContainer);
  
  // Create particles
  for (let i = 0; i < 50; i++) {
    createParticle(particlesContainer);
  }
}

function createParticle(container) {
  const particle = document.createElement('div');
  particle.className = 'particle';
  
  // Random size between 5 and 30px
  const size = Math.floor(Math.random() * 25) + 5;
  particle.style.width = `${size}px`;
  particle.style.height = `${size}px`;
  
  // Random position
  const posX = Math.floor(Math.random() * window.innerWidth);
  const posY = Math.floor(Math.random() * window.innerHeight);
  particle.style.left = `${posX}px`;
  particle.style.top = `${posY}px`;
  
  // Random animation duration between 15 and 45 seconds
  const duration = Math.floor(Math.random() * 30) + 15;
  particle.style.animationDuration = `${duration}s`;
  
  // Random delay
  const delay = Math.floor(Math.random() * 10);
  particle.style.animationDelay = `${delay}s`;
  
  // Random opacity
  const opacity = (Math.random() * 0.5) + 0.1;
  particle.style.opacity = opacity;
  
  // Add to container
  container.appendChild(particle);
  
  // Remove and recreate particles after animation completes
  setTimeout(() => {
    particle.remove();
    createParticle(container);
  }, duration * 1000 + delay * 1000);
}

// Page transition effect
function setupPageTransitions() {
  const links = document.querySelectorAll('a:not([target="_blank"])');
  
  links.forEach(link => {
    link.addEventListener('click', function(e) {
      // Don't apply to external links or links with specific classes
      if (this.getAttribute('href').startsWith('#') || 
          this.getAttribute('href').startsWith('javascript:') ||
          this.classList.contains('no-transition')) {
        return;
      }
      
      e.preventDefault();
      const href = this.getAttribute('href');
      
      // Fade out current page
      document.body.style.opacity = '0';
      
      // Navigate after animation completes
      setTimeout(() => {
        window.location.href = href;
      }, 300);
    });
  });
}

// Score counter animation
function animateScoreCounter() {
  const scoreElement = document.querySelector('.score-number');
  if (!scoreElement) return;
  
  const finalScore = parseInt(scoreElement.getAttribute('data-score'));
  
  if (!finalScore && finalScore !== 0) return;
  
  scoreElement.textContent = '0';
  
  let currentScore = 0;
  const duration = 1500; // 1.5 seconds
  const interval = 50; // Update every 50ms
  const steps = duration / interval;
  const increment = finalScore / steps;
  
  const counter = setInterval(() => {
    currentScore += increment;
    
    // Don't exceed the final score
    if (currentScore >= finalScore) {
      scoreElement.textContent = finalScore;
      clearInterval(counter);
      return;
    }
    
    scoreElement.textContent = Math.floor(currentScore);
  }, interval);
}

// Add glow effect to buttons
function addGlowEffects() {
  const buttons = document.querySelectorAll('button, .btn');
  buttons.forEach(button => {
    button.classList.add('glow-button');
  });
}

// Quiz options hover effects
function setupQuizOptionEffects() {
  const options = document.querySelectorAll('.quiz-option');
  options.forEach(option => {
    option.addEventListener('mouseenter', function() {
      this.style.transform = 'translateX(10px) scale(1.03)';
    });
    
    option.addEventListener('mouseleave', function() {
      this.style.transform = 'translateX(0) scale(1)';
    });
    
    option.addEventListener('click', function() {
      // Highlight selected option
      options.forEach(opt => opt.classList.remove('selected'));
      this.classList.add('selected');
      
      // Apply pulse animation
      this.style.animation = 'none';
      setTimeout(() => {
        this.style.animation = 'pulse 0.5s';
      }, 10);
    });
  });
}

// Handle flash messages fadeout
function setupFlashMessages() {
  const flashMessages = document.querySelectorAll('.alert');
  flashMessages.forEach(message => {
    setTimeout(() => {
      message.style.opacity = '0';
      setTimeout(() => {
        message.style.display = 'none';
      }, 500);
    }, 5000);
  });
}

// Initialize all animations
function initAnimations() {
  // Wait for DOM to be loaded
  document.addEventListener('DOMContentLoaded', function() {
    createParticleBackground();
    setupPageTransitions();
    animateScoreCounter();
    addGlowEffects();
    setupQuizOptionEffects();
    setupFlashMessages();
    
    // Fade in body
    document.body.style.opacity = '1';
  });
}

// Start animations
initAnimations();