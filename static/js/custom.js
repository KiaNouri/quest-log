/**
 * Questlog — small progressive-enhancement script.
 * No framework, no build step. Two jobs:
 *   1. Animate .xp-bar-fill elements from 0 to their data-value width.
 *   2. Count stat numbers up from 0 on page load.
 * Both are purely cosmetic and safe to fail silently.
 */
document.addEventListener('DOMContentLoaded', function () {
    animateXpBars();
    animateStatCounters();
    initThemeToggle();
});

function initThemeToggle() {
    var toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', function () {
        var root = document.documentElement;
        var current = root.getAttribute('data-bs-theme') || 'light';
        var next = current === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-bs-theme', next);
        localStorage.setItem('ql-theme', next);
    });
}

function animateXpBars() {
    var bars = document.querySelectorAll('.xp-bar-fill');
    bars.forEach(function (bar) {
        var target = parseFloat(bar.getAttribute('data-value')) || 0;
        target = Math.max(0, Math.min(100, target));
        // Let the browser paint the 0% state first, then transition.
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                bar.style.width = target + '%';
            });
        });
    });
}

function animateStatCounters() {
    var counters = document.querySelectorAll('[data-counter]');
    counters.forEach(function (el) {
        var target = parseInt(el.getAttribute('data-counter'), 10);
        if (isNaN(target)) return;

        var duration = 800;
        var start = null;

        function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            el.textContent = Math.floor(progress * target).toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                el.textContent = target.toLocaleString();
            }
        }
        window.requestAnimationFrame(step);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".review-text-wrapper").forEach(function (wrapper) {
        var text = wrapper.querySelector(".review-text");
        var toggle = wrapper.querySelector(".review-expand-toggle");

        if (!text || !toggle) return;

        // Show toggle button if text overflows
        if (text.scrollHeight > text.clientHeight + 4) {
            toggle.classList.remove("d-none");
        }

        // Toggle expand state on click
        toggle.addEventListener("click", function () {
            var expanded = text.classList.toggle("expanded");
            toggle.textContent = expanded ? "Show less" : "Show more";
        });
    });
});