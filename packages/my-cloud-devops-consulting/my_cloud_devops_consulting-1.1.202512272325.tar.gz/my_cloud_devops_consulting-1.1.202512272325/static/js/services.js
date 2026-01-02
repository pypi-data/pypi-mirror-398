document.addEventListener("DOMContentLoaded", () => {
    // Smooth scrolling for internal links
    const links = document.querySelectorAll("a[href^='#']");
    links.forEach(link => {
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
    backToTopButton.className = "back-to-top";
    document.body.appendChild(backToTopButton);
  
    backToTopButton.style.display = "none";
    backToTopButton.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  
    window.addEventListener("scroll", () => {
      if (window.pageYOffset > 300) {
        backToTopButton.style.display = "block";
      } else {
        backToTopButton.style.display = "none";
      }
    });
  
    // Section reveal on scroll
    const sections = document.querySelectorAll("section");
    const revealSection = () => {
      const viewportHeight = window.innerHeight;
      sections.forEach(section => {
        const sectionTop = section.getBoundingClientRect().top;
        if (sectionTop < viewportHeight - 100) {
          section.classList.add("visible");
        }
      });
    };
    window.addEventListener("scroll", revealSection);
  
    // Styling enhancements for the reveal effect
    const styleSheet = document.createElement("style");
    styleSheet.type = "text/css";
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
      .back-to-top {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 15px;
        background: #ff8c42;
        color: white;
        border: none;
        border-radius: 5px;
        display: none;
        cursor: pointer;
      }
      .back-to-top:hover {
        background: #e07a35;
      }
    `;
    document.head.appendChild(styleSheet);
  });
  