
function renderClinicChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Clinic 1',
                    data: data.clinic1,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.5)',
                    tension: 0.2,
                    pointRadius: 4
                },
                {
                    label: 'Clinic 2',
                    data: data.clinic2,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    tension: 0.2,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Proportion of Deaths' }
                },
                x: {
                    title: { display: true, text: 'Year' }
                }
            }
        }
    });
}

function renderMonthlyChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Combine into a single timeline padded with nulls to separate the datasets cleanly
    const labels = data.labelsBefore.concat(data.labelsAfter);
    const beforeData = data.before.concat(Array(data.after.length).fill(null));
    const afterData = Array(data.before.length).fill(null).concat(data.after);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Before Handwashing',
                    data: beforeData,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.5)',
                    tension: 0.2,
                    pointRadius: 3
                },
                {
                    label: 'After Handwashing',
                    data: afterData,
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.5)',
                    tension: 0.2,
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Proportion of Deaths' }
                },
                x: {
                    title: { display: true, text: 'Date' }
                }
            }
        }
    });
}

function renderBootstrapHistogram(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Color code the Confidence Interval (Blue for inside, Red for tails)
    const backgroundColors = data.labels.map(label => {
        if (label < data.ci_lower || label > data.ci_upper) {
            return 'rgba(239, 68, 68, 0.8)'; 
        }
        return 'rgba(59, 130, 246, 0.8)';
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels.map(l => l.toFixed(4)),
            datasets: [{
                label: 'Frequency',
                data: data.counts,
                backgroundColor: backgroundColors,
                barPercentage: 1.0,
                categoryPercentage: 1.0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Frequency' }
                },
                x: {
                    title: { display: true, text: 'Mean Difference' },
                    ticks: { maxTicksLimit: 8 }
                }
            }
        }
    });
}