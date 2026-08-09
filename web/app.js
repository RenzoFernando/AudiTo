const repository = "RenzoFernando/AudiTo";
const repositoryUrl = `https://github.com/${repository}`;
const releaseUrl = `${repositoryUrl}/releases/latest`;
const installerName = "AudiTo-Setup.exe";
const portableName = "AudiTo-Portable.exe";
const installerFallback = `${releaseUrl}/download/${installerName}`;
const portableFallback = `${releaseUrl}/download/${portableName}`;

const releaseStatus = document.querySelector("#release-status");
const releaseVersion = document.querySelector("#release-version");
const downloadStatus = document.querySelector("#download-status");
const downloadLinks = {
    installer: [
        document.querySelector("#hero-installer-link"),
        document.querySelector("#installer-download-link")
    ],
    portable: [
        document.querySelector("#hero-portable-link"),
        document.querySelector("#portable-download-link")
    ]
};

function setLinks(elements, url) {
    elements.filter(Boolean).forEach(element => {
        element.href = url;
        element.classList.remove("pending");
        element.removeAttribute("aria-disabled");
    });
}

function setPending(elements) {
    elements.filter(Boolean).forEach(element => {
        element.classList.add("pending");
        element.setAttribute("aria-disabled", "true");
        element.addEventListener("click", event => event.preventDefault(), { once: true });
    });
}

function normalizeVersion(value) {
    return String(value || "").trim().replace(/^v/i, "");
}

setLinks(downloadLinks.installer, installerFallback);
setLinks(downloadLinks.portable, portableFallback);

fetch(`https://api.github.com/repos/${repository}/releases/latest`, {
    headers: { Accept: "application/vnd.github+json" }
})
    .then(response => {
        if (response.status === 404) {
            setPending(downloadLinks.installer);
            setPending(downloadLinks.portable);
            releaseStatus.textContent = "Primera release pendiente";
            downloadStatus.textContent = "Las descargas se activarán automáticamente cuando publiques la primera GitHub Release.";
            return null;
        }
        if (!response.ok) {
            throw new Error(`GitHub API ${response.status}`);
        }
        return response.json();
    })
    .then(release => {
        if (!release) {
            return;
        }
        const version = normalizeVersion(release.tag_name || release.name);
        if (version) {
            releaseVersion.textContent = `v${version}`;
        }
        releaseStatus.textContent = "Última release";
        const assets = Array.isArray(release.assets) ? release.assets : [];
        const installerAsset = assets.find(asset => asset.name === installerName);
        const portableAsset = assets.find(asset => asset.name === portableName);
        setLinks(downloadLinks.installer, installerAsset?.browser_download_url || installerFallback);
        setLinks(downloadLinks.portable, portableAsset?.browser_download_url || portableFallback);
        downloadStatus.textContent = "Descargas enlazadas automáticamente con la última GitHub Release publicada.";
    })
    .catch(() => {
        releaseStatus.textContent = "GitHub Releases";
        downloadStatus.textContent = "Descarga desde GitHub usando los nombres estables de los artefactos oficiales.";
    });
