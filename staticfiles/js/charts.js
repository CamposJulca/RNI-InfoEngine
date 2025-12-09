function loadContratosCharts(statsEquipo, statsVinculacion) {

    // 1. Contratos por Equipo
    if (statsEquipo.labels.length > 0) {
        new Chart(document.getElementById("chartEquipo"), {
            type: "bar",
            data: {
                labels: statsEquipo.labels,
                datasets: [{
                    label: "Contratos",
                    data: statsEquipo.values,
                    backgroundColor: "#005BBB",
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.parsed.y} contratos`
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // 2. Contratos por tipo de vinculación
    if (statsVinculacion.labels.length > 0) {
        new Chart(document.getElementById("chartVinculacion"), {
            type: "doughnut",
            data: {
                labels: statsVinculacion.labels,
                datasets: [{
                    data: statsVinculacion.values,
                    backgroundColor: ["#005BBB", "#FFD500", "#00A859"],
                    borderWidth: 2,
                    borderColor: "#fff"
                }]
            },
            options: {
                cutout: "55%",
                responsive: true,
                plugins: {
                    legend: { position: "bottom" },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${ctx.parsed} contratos`
                        }
                    }
                }
            }
        });
    }
}
