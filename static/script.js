// ====== FORM VALIDATION FOR LOGIN & SIGNUP ======

function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const username = form.querySelector('input[name="username"]');
    const password = form.querySelector('input[name="password"]');

    form.addEventListener("submit", function (e) {
        if (username.value.trim() === "" || password.value.trim() === "") {
            alert("Username and password are required!");
            e.preventDefault();
        }
    });
}

// ====== STAR RATING FUNCTION ======

function setupStarRating() {
    const stars = document.querySelectorAll(".star");
    const ratingInput = document.getElementById("rating-input");

    if (!stars.length || !ratingInput) return;

    stars.forEach((star, index) => {
        star.addEventListener("click", () => {
            ratingInput.value = index + 1;

            // Highlight stars up to selected
            stars.forEach((s, i) => {
                s.classList.toggle("selected", i <= index);
            });
        });

        star.addEventListener("mouseover", () => {
            stars.forEach((s, i) => {
                s.classList.toggle("hover", i <= index);
            });
        });

        star.addEventListener("mouseout", () => {
            stars.forEach((s) => {
                s.classList.remove("hover");
            });
        });
    });
}

// ====== ON PAGE LOAD SETUP ======

window.addEventListener("DOMContentLoaded", function () {
    // Setup validation
    validateForm("loginForm");
    validateForm("signupForm");

    // Setup star rating (only on review page)
    setupStarRating();
});
