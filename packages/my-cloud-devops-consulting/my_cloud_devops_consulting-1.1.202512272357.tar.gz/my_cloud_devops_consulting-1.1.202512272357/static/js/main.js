document.addEventListener("DOMContentLoaded", () => {
    // Smooth scrolling for all internal links
    const smoothScrollLinks = document.querySelectorAll("a[href^='#']");
    smoothScrollLinks.forEach(link => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            const targetId = link.getAttribute("href").substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: "smooth" });
            }
        });
    });

    // Back to top button functionality
    const backToTopButton = document.createElement("button");
    backToTopButton.innerText = "↑ Top";
    backToTopButton.className = "scroll-to-top";
    document.body.appendChild(backToTopButton);

    backToTopButton.style.display = "none";
    backToTopButton.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    window.addEventListener("scroll", () => {
        backToTopButton.style.display = window.pageYOffset > 300 ? "block" : "none";
    });

    // Modular function to reveal elements on scroll
    const revealOnScroll = () => {
        const sections = document.querySelectorAll("section");
        const viewportHeight = window.innerHeight;
        sections.forEach(section => {
            const sectionTop = section.getBoundingClientRect().top;
            if (sectionTop < viewportHeight - 100) {
                section.classList.add("visible");
            }
        });
    };
    window.addEventListener("scroll", revealOnScroll);
    revealOnScroll(); // ✅ Reveal sections immediately on page load

    // Inject dynamic styles for section reveal effect
    const styleSheet = document.createElement("style");
    styleSheet.innerText = `
        section {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        }
        section.visible {
            opacity: 1;
            transform: translateY(0);
        }
        .scroll-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 15px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            display: none;
            cursor: pointer;
        }
        .scroll-to-top:hover {
            background: #0056b3;
        }
    `;
    document.head.appendChild(styleSheet);

    // Testimonials auto-rotation
    const testimonials = document.querySelectorAll(".testimonial");
    let index = 0;

    function rotateTestimonials() {
        testimonials[index].classList.remove("active");
        index = (index + 1) % testimonials.length;
        testimonials[index].classList.add("active");
    }

    if (testimonials.length > 1) {
        setInterval(rotateTestimonials, 2000);
    }
});
