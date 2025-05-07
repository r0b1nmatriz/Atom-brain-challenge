// Create particle animation for the header
function createHeaderParticles() {
    const headerParticles = document.getElementById('header-particles');
    if (!headerParticles) return;
    
    // Clear any existing particles
    headerParticles.innerHTML = '';
    
    // Create new particles
    const numberOfParticles = window.innerWidth < 768 ? 15 : 30;
    
    for (let i = 0; i < numberOfParticles; i++) {
        const particle = document.createElement('span');
        particle.className = 'particle';
        
        // Random positioning
        const posX = Math.random() * 100; // %
        const posY = Math.random() * 100; // %
        
        // Random size
        const size = Math.random() * 3 + 1; // px
        
        // Random animation properties
        const duration = Math.random() * 10 + 5; // s
        const delay = Math.random() * 5; // s
        
        // Apply styles
        particle.style.left = `${posX}%`;
        particle.style.top = `${posY}%`;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${delay}s`;
        
        // Add to container
        headerParticles.appendChild(particle);
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Handle splash screen
    const splashScreen = document.querySelector('.splash-screen');
    if (splashScreen) {
        setTimeout(() => {
            splashScreen.classList.add('fade-out');
        }, 3000);
    }
    
    // Create and animate the header particles
    createHeaderParticles();
    
    // Handle window resize for responsive particles
    window.addEventListener('resize', function() {
        createHeaderParticles();
    });
    // Quiz timer functionality
    const startTime = new Date().getTime();
    let timerInterval;
    
    function startTimer() {
        const timerElement = document.getElementById('quizTimer');
        if (!timerElement) return;
        
        timerInterval = setInterval(function() {
            const currentTime = new Date().getTime();
            const elapsedTime = Math.floor((currentTime - startTime) / 1000);
            
            const minutes = Math.floor(elapsedTime / 60);
            const seconds = elapsedTime % 60;
            
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    // Start timer if we're on the quiz page
    if (document.querySelector('.quiz-container')) {
        startTimer();
    }
    
    // Handle option selection
    const optionItems = document.querySelectorAll('.option-item');
    optionItems.forEach(item => {
        item.addEventListener('click', function() {
            // Find the radio input within this option and select it
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                
                // Add selected styling
                const questionContainer = this.closest('.question-container');
                const allOptions = questionContainer.querySelectorAll('.option-item');
                
                allOptions.forEach(opt => {
                    opt.classList.remove('selected-option');
                });
                
                this.classList.add('selected-option');
            }
        });
    });
    
    // Form validation
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            const allQuestions = document.querySelectorAll('.question-container');
            let allAnswered = true;
            
            allQuestions.forEach(question => {
                const radios = question.querySelectorAll('input[type="radio"]');
                let questionAnswered = false;
                
                radios.forEach(radio => {
                    if (radio.checked) {
                        questionAnswered = true;
                    }
                });
                
                if (!questionAnswered) {
                    allAnswered = false;
                }
            });
            
            if (!allAnswered) {
                e.preventDefault();
                alert('Please answer all questions before submitting.');
                return false;
            }
            
            // Stop timer if it's running
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            
            return true;
        });
    }
    
    // Results page social media share buttons
    const shareButtons = document.querySelectorAll('.share-btn');
    shareButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Track sharing event (could add analytics here)
            console.log('Shared on ' + this.textContent.trim());
        });
    });
    
    // Add class to selected option
    const style = document.createElement('style');
    style.textContent = `
        .selected-option {
            background-color: #fff8f2;
            border-color: #ff6600;
            box-shadow: 0 0 0 1px #ff6600;
        }
    `;
    document.head.appendChild(style);
});

// Confetti effect for high scores on results page
function celebrateHighScore() {
    const scoreElement = document.querySelector('.score-number');
    if (!scoreElement) return;
    
    const scoreText = scoreElement.textContent;
    const scoreParts = scoreText.split('/');
    
    if (scoreParts.length === 2) {
        const score = parseInt(scoreParts[0]);
        const total = parseInt(scoreParts[1]);
        
        // If score is 80% or higher
        if (score / total >= 0.8) {
            // Simple confetti effect with emojis
            const confettiContainer = document.createElement('div');
            confettiContainer.className = 'confetti-container';
            confettiContainer.style.position = 'fixed';
            confettiContainer.style.top = '0';
            confettiContainer.style.left = '0';
            confettiContainer.style.width = '100%';
            confettiContainer.style.height = '100%';
            confettiContainer.style.pointerEvents = 'none';
            confettiContainer.style.zIndex = '9999';
            document.body.appendChild(confettiContainer);
            
            const emojis = ['🎉', '🏆', '🥇', '⭐', '🌟', '💫'];
            
            for (let i = 0; i < 50; i++) {
                const emoji = document.createElement('div');
                emoji.className = 'confetti-emoji';
                emoji.textContent = emojis[Math.floor(Math.random() * emojis.length)];
                emoji.style.position = 'absolute';
                emoji.style.left = Math.random() * 100 + 'vw';
                emoji.style.top = -20 + 'px';
                emoji.style.fontSize = (Math.random() * 20 + 10) + 'px';
                emoji.style.userSelect = 'none';
                emoji.style.animation = 'fall ' + (Math.random() * 3 + 2) + 's linear forwards';
                confettiContainer.appendChild(emoji);
            }
            
            // Create keyframes for falling animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fall {
                    0% {
                        transform: translateY(0) rotate(0deg);
                        opacity: 1;
                    }
                    100% {
                        transform: translateY(100vh) rotate(720deg);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
            
            // Remove confetti after animation completes
            setTimeout(() => {
                confettiContainer.remove();
            }, 5000);
        }
    }
}

// Run celebration if on results page
if (document.querySelector('.result-container')) {
    celebrateHighScore();
}
