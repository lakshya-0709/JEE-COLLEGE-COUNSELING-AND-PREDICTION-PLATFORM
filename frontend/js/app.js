/* ═══════════════════════════════════════════════════
   JEE Counselor — App Shell with Page Router
   ═══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const navbar = document.getElementById('navbar');
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    const navLogo = document.getElementById('navLogo');
    const links = document.querySelectorAll('.nav-link');
    const statNumbers = document.querySelectorAll('.stat-number');
    const ctaButton = document.getElementById('ctaButton');
    const appPages = document.querySelectorAll('.app-page');

    // Valid page names
    const validPages = ['home', 'predict', 'trends', 'compare', 'preference'];

    // Initialize
    initRouter();
    initNavbar();
    initStatCounters();
    initScrollReveal();
    initParticleBackground();
    checkBackendHealth();

    /* ───────────────────────────────────────────────
       Hash-Based Page Router
       ─────────────────────────────────────────────── */
    function initRouter() {
        // Navigate on hash change
        window.addEventListener('hashchange', () => {
            navigateTo(getPageFromHash());
        });

        // Initial page load
        navigateTo(getPageFromHash());

        // Feature card links on home page
        document.querySelectorAll('.home-feature-card').forEach(card => {
            card.addEventListener('click', (e) => {
                e.preventDefault();
                const href = card.getAttribute('href');
                if (href) {
                    window.location.hash = href;
                }
            });
        });

        // Back-to-home links
        document.querySelectorAll('.back-to-home').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.hash = '#home';
            });
        });

        // Footer feature links
        document.querySelectorAll('.footer-links a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.hash = link.getAttribute('href');
            });
        });
    }

    function getPageFromHash() {
        const hash = window.location.hash.replace('#', '');
        return validPages.includes(hash) ? hash : 'home';
    }

    function navigateTo(pageName) {
        // Hide all pages
        appPages.forEach(page => page.classList.remove('active'));

        // Show the target page
        const targetPage = document.querySelector(`.app-page[data-page="${pageName}"]`);
        if (targetPage) {
            targetPage.classList.add('active');
        }

        // Update active nav link
        links.forEach(link => {
            link.classList.remove('active');
            const linkPage = link.getAttribute('data-section');
            if (linkPage === pageName) {
                link.classList.add('active');
            }
        });

        // Scroll to top on page change
        window.scrollTo({ top: 0, behavior: 'instant' });

        // Close mobile menu if open
        if (navToggle) {
            navToggle.classList.remove('active');
            navLinks.classList.remove('active');
        }

        // Re-trigger scroll reveal for newly visible page
        initScrollReveal();
    }

    /* ───────────────────────────────────────────────
       Navbar
       ─────────────────────────────────────────────── */
    function initNavbar() {
        // Sticky Navbar shadow on scroll
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });

        // Mobile Nav Toggle
        if (navToggle) {
            navToggle.addEventListener('click', () => {
                navToggle.classList.toggle('active');
                navLinks.classList.toggle('active');
            });
        }

        // Nav links → trigger hash navigation
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const href = link.getAttribute('href');
                window.location.hash = href;
            });
        });

        // Logo → go home
        if (navLogo) {
            navLogo.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.hash = '#home';
            });
        }

        // CTA button → go to predict
        if (ctaButton) {
            ctaButton.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.hash = '#predict';
            });
        }
    }

    /* ───────────────────────────────────────────────
       Animate Stat Numbers
       ─────────────────────────────────────────────── */
    function initStatCounters() {
        if (statNumbers.length === 0) return;

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const targetEl = entry.target;
                    const targetVal = parseInt(targetEl.getAttribute('data-target'), 10);
                    animateCounter(targetEl, targetVal, 2000);
                    obs.unobserve(targetEl);
                }
            });
        }, { root: null, threshold: 0.1 });

        statNumbers.forEach(num => observer.observe(num));
    }

    /* ───────────────────────────────────────────────
       Scroll Reveal
       ─────────────────────────────────────────────── */
    function initScrollReveal() {
        const revealElements = document.querySelectorAll('.reveal:not(.visible)');
        if (revealElements.length === 0) return;

        const revealObserver = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

        revealElements.forEach(el => revealObserver.observe(el));
    }

    /* ───────────────────────────────────────────────
       Particle Background
       ─────────────────────────────────────────────── */
    function initParticleBackground() {
        const canvas = document.getElementById('particle-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let particles = [];
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        const particleCount = Math.min(60, Math.floor((width * height) / 20000));
        const colors = ['#00d4ff', '#ff6b35', '#7000ff', '#ffffff'];

        window.addEventListener('resize', () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        class Particle {
            constructor() {
                this.reset();
            }

            reset() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.size = Math.random() * 2 + 1;
                this.speedX = (Math.random() - 0.5) * 0.4;
                this.speedY = (Math.random() - 0.5) * 0.4;
                this.color = colors[Math.floor(Math.random() * colors.length)];
                this.alpha = Math.random() * 0.5 + 0.2;
                this.pulseSpeed = Math.random() * 0.01 + 0.005;
                this.pulseDir = Math.random() > 0.5 ? 1 : -1;
            }

            update() {
                this.x += this.speedX;
                this.y += this.speedY;

                if (this.x < 0 || this.x > width) this.speedX *= -1;
                if (this.y < 0 || this.y > height) this.speedY *= -1;

                this.alpha += this.pulseSpeed * this.pulseDir;
                if (this.alpha > 0.8 || this.alpha < 0.15) {
                    this.pulseDir *= -1;
                }
            }

            draw() {
                ctx.save();
                ctx.globalAlpha = this.alpha;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = this.color;

                if (this.size > 2) {
                    ctx.shadowBlur = 10;
                    ctx.shadowColor = this.color;
                }

                ctx.fill();
                ctx.restore();
            }
        }

        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);

            ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
            ctx.lineWidth = 0.5;
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < 150) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }

            particles.forEach(p => {
                p.update();
                p.draw();
            });

            requestAnimationFrame(animate);
        }

        animate();
    }

    /* ───────────────────────────────────────────────
       Backend Health Check
       ─────────────────────────────────────────────── */
    async function checkBackendHealth() {
        const isHealthy = await api.healthCheck();
        if (isHealthy) {
            console.log("JEE Counselor API connection successful.");
            showToast("Server connected successfully!", "success");
        } else {
            console.warn("Could not connect to JEE Counselor API server.");
            showToast("Backend server offline. Please start the server.", "error");
        }
    }
});
