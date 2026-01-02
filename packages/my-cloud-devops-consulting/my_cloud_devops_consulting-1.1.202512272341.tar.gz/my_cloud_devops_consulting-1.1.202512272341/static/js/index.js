
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
  backToTopButton.className = "scroll-to-top";
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

  // Hero section animation
  const heroSection = document.querySelector(".hero");
  if (heroSection) {
    heroSection.style.transition = "opacity 1s ease, transform 1s ease";
    heroSection.style.opacity = 0;
    heroSection.style.transform = "translateY(20px)";
    setTimeout(() => {
      heroSection.style.opacity = 1;
      heroSection.style.transform = "translateY(0)";
    }, 100);
  }

  // Card hover effect with subtle movement
  const cards = document.querySelectorAll(".card");
  cards.forEach(card => {
    card.addEventListener("mouseover", () => {
      card.style.transform = "scale(1.05)";
      card.style.transition = "transform 0.3s ease";
    });
    card.addEventListener("mouseout", () => {
      card.style.transform = "scale(1)";
    });
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
    .scroll-to-top {
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
      transition: background 0.3s ease;
    }
    .scroll-to-top:hover {
      background: #e07a35;
    }
  `;
  document.head.appendChild(styleSheet);
});


// Function to scroll to the top of the page
function scrollToTop() {
window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Show the button when the user scrolls down
window.addEventListener('scroll', () => {
const scrollToTopButton = document.querySelector('.scroll-to-top');
if (window.pageYOffset > 300) {
  scrollToTopButton.style.display = 'block';
} else {
  scrollToTopButton.style.display = 'none';
}
});