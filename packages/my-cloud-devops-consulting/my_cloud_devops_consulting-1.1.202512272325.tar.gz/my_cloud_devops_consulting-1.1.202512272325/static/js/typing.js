document.addEventListener("DOMContentLoaded", () => {
    const text = [
      "Empowering Your Cloud Journey ",
      "Automate. Scale. Secure. ",
      "From Dev to Ops — Faster ",
    ];
    let i = 0;
    let j = 0;
    let isDeleting = false;
    const element = document.getElementById("dynamic-headline");
  
    function typeEffect() {
      const currentPhrase = text[i];
      const fullLength = currentPhrase.length;
  
      if (!isDeleting) {
        j++;
      } else {
        j--;
      }
  
      element.innerText = currentPhrase.substring(0, j);
  
      let delay = isDeleting ? 80 : 160; // base typing/deleting speed
  
      if (!isDeleting && j === fullLength) {
        isDeleting = true;
        delay = 2000; // pause after typing
      } else if (isDeleting && j === 0) {
        isDeleting = false;
        i = (i + 1) % text.length;
        delay = 600; // pause before next phrase
      }
  
      setTimeout(typeEffect, delay);
    }
  
    typeEffect();
  });
  