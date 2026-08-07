const measured = [
    {
        name: "Microsoft",
        score: 87,
        detail: "Mejor estabilidad global y mejor puntuación en la prueba actual. Tiempo aproximado: 60 min."
    },
    {
        name: "AudiTo · Equilibrada",
        score: 83,
        detail: "Resultado completo de la prueba original. Antes del loop final, la comprensión estimada fue cercana al 86%."
    }
];

const pending = [
    ["OpenAI nativo", "Benchmark pendiente"],
    ["AudiTo · Base", "Benchmark pendiente"],
    ["AudiTo · Rápida", "Benchmark pendiente"],
    ["AudiTo · Máxima", "Benchmark pendiente"],
    ["AudiTo · Equilibrada v0.5", "Repetir benchmark"]
];

const measuredContainer = document.querySelector("#measured-results");
const pendingContainer = document.querySelector("#pending-results");

measured.forEach(item => {
    const card = document.createElement("article");
    card.className = "benchmark-card";
    card.innerHTML = `
        <div class="benchmark-head">
            <h3>${item.name}</h3>
            <strong class="score">${item.score}%</strong>
        </div>
        <div class="bar"><span data-score="${item.score}"></span></div>
        <p>${item.detail}</p>
    `;
    measuredContainer.appendChild(card);
});

pending.forEach(([name, status]) => {
    const card = document.createElement("article");
    card.className = "model-card";
    card.innerHTML = `<h3>${name}</h3><p>Sin porcentaje publicado hasta medirlo sobre el mismo audio de referencia.</p><span class="status">${status}</span>`;
    pendingContainer.appendChild(card);
});

requestAnimationFrame(() => {
    document.querySelectorAll(".bar span").forEach(bar => {
        bar.style.width = `${bar.dataset.score}%`;
    });
});
