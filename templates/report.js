// report.js
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.test-details').forEach(details => {
        details.classList.add('hidden');
    });
    document.querySelectorAll('.test-header').forEach(header => {
        header.addEventListener('click', () => {
            const details = header.nextElementSibling;
            const chevron = header.querySelector('.fa-chevron-right');
            if (details) {
                details.classList.toggle('hidden');

                // Rotate chevron if it exists
                if (chevron) {
                    chevron.style.transform = details.classList.contains('hidden')
                        ? 'rotate(0deg)'
                        : 'rotate(90deg)';
                }
            }
        });
    });
});
