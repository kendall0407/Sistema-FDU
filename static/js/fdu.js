document.querySelectorAll('[data-filter]').forEach(input => {
    input.addEventListener('input', () => {
        const value = input.value.toLocaleLowerCase().trim();
        const tbody = document.querySelector(`#${input.dataset.filter} tbody`);
        if (!tbody) return;
        tbody.querySelectorAll('tr').forEach(row => {
            row.hidden = !row.textContent.toLocaleLowerCase().includes(value);
        });
    });
});
