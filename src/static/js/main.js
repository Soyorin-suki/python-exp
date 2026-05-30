document.addEventListener('DOMContentLoaded', () => {
    const chartType = document.getElementById('chart_type');
    if (chartType && typeof window.toggleColumns !== 'function') {
        window.toggleColumns = function toggleColumns() {
            const type = chartType.value;
            const single = document.getElementById('single_col_div');
            const two = document.getElementById('two_col_div');
            if (single) {
                single.style.display = type === 'histogram' ? 'block' : 'none';
            }
            if (two) {
                two.style.display = type === 'scatter' ? 'block' : 'none';
            }
        };
        window.toggleColumns();
        chartType.addEventListener('change', window.toggleColumns);
    }

    document.querySelectorAll('.alert').forEach((alert) => {
        alert.setAttribute('role', 'status');
    });
});
