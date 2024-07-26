function createPieChart(values) {
    const ctx = document.getElementById('pie-chart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Value 1', 'Value 2', 'Value 3', 'Value 4'],
            datasets: [{
                data: [values.value1, values.value2, values.value3, values.value4],
                backgroundColor: ['red', 'blue', 'yellow', 'green'],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}
