document.addEventListener('DOMContentLoaded', () => {
    const wineList = document.getElementById('wine-list');
    const searchInput = document.getElementById('search-input');
    const refreshBtn = document.getElementById('refresh-btn');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const storeTabs = document.querySelectorAll('.store-tab');
    const pairingFilterBtns = document.querySelectorAll('.pairing-filter-btn');

    // Sort Modal Elements
    const sortTriggerBtn = document.getElementById('sort-trigger-btn');
    const sortModal = document.getElementById('sortModal');
    const closeSort = document.querySelector('.close-sort');
    const sortOptions = document.querySelectorAll('.sort-option');
    const currentSortLabel = document.getElementById('current-sort-label');

    // Configuration
    // For production, change this to your GitHub Pages URL
    // e.g., 'https://yourusername.github.io/winevino-data/wines.json'
    const DATA_URL = '/static/wines.json';
    const CACHE_KEY = 'winevinoCachedDataV3'; // Changed to force cache refresh
    const CACHE_TIMESTAMP_KEY = 'winevinoCacheTimestampV3'; // Changed to force cache refresh
    const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

    let allWines = [];
    let currentFilter = 'all';
    let currentStore = 'all';
    let currentPairing = null;
    let currentSort = 'score'; // Default sort

    // Fetch wines on load
    fetchWines();

    // Filter button logic
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update filter
            currentFilter = btn.dataset.filter;
            applyFilters();
        });
    });

    // Pairing filter logic
    pairingFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Toggle active state
            if (btn.classList.contains('active')) {
                btn.classList.remove('active');
                currentPairing = null;
            } else {
                pairingFilterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentPairing = btn.dataset.pairing;
            }
            applyFilters();
        });
    });

    // Sort Modal Logic
    if (sortTriggerBtn) {
        sortTriggerBtn.addEventListener('click', () => {
            sortModal.style.display = 'flex';
        });

        closeSort.addEventListener('click', () => {
            sortModal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === sortModal) {
                sortModal.style.display = 'none';
            }
        });

        sortOptions.forEach(option => {
            option.addEventListener('click', () => {
                // Update active state
                sortOptions.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');

                // Update sort value
                currentSort = option.dataset.value;
                currentSortLabel.textContent = option.textContent.trim();

                // Close modal
                sortModal.style.display = 'none';

                // Re-fetch/Sort wines
                fetchWines();
            });
        });
    }

    // Settings Modal Logic
    const settingsModal = document.getElementById('settingsModal');
    const settingsBtn = document.getElementById('settings-btn');
    const closeSettings = document.querySelector('.close-settings');
    const resetRatingsBtn = document.getElementById('reset-ratings-btn');
    const resetNotesBtn = document.getElementById('reset-notes-btn');
    const factoryResetBtn = document.getElementById('factory-reset-btn');
    const settingsMessage = document.getElementById('settings-message');

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.style.display = 'flex';
        });

        closeSettings.addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                settingsModal.style.display = 'none';
            }
        });

        function showSettingsMessage(msg, type = 'success') {
            settingsMessage.textContent = msg;
            settingsMessage.className = `settings-message ${type}`;
            setTimeout(() => {
                settingsMessage.classList.add('hidden');
            }, 3000);
        }

        resetRatingsBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete all your personal ratings? This cannot be undone.')) {
                localStorage.removeItem('personalScores');
                showSettingsMessage('All ratings have been reset.');
                // Refresh view to update stars
                applyFilters();
            }
        });

        resetNotesBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete all your notes and pairings? This cannot be undone.')) {
                localStorage.removeItem('winePairings');
                showSettingsMessage('All notes and pairings have been reset.');
                // Refresh view to update pairings
                applyFilters();
            }
        });

        factoryResetBtn.addEventListener('click', () => {
            if (confirm('WARNING: This will delete ALL your data (ratings, notes, pairings). Are you sure?')) {
                localStorage.clear();
                showSettingsMessage('Factory reset complete.');
                setTimeout(() => {
                    location.reload();
                }, 1500);
            }
        });
    }

    // Store tab logic
    storeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active state
            storeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update store filter
            currentStore = tab.dataset.store;

            // Fetch wines for this store (simulated filtering for now)
            fetchWines();
        });
    });

    refreshBtn.addEventListener('click', () => {
        refreshBtn.classList.add('fa-spin');

        // Clear cache to force fresh fetch
        localStorage.removeItem(CACHE_KEY);
        localStorage.removeItem(CACHE_TIMESTAMP_KEY);

        // Re-fetch data
        fetchWines().then(() => {
            setTimeout(() => {
                refreshBtn.classList.remove('fa-spin');
            }, 500);
        });
    });

    searchInput.addEventListener('input', (e) => {
        applyFilters();
    });

    function applyFilters() {
        let filteredWines = [...allWines];

        // Search filter
        const searchTerm = searchInput.value.toLowerCase();
        if (searchTerm) {
            filteredWines = filteredWines.filter(wine =>
                wine.name.toLowerCase().includes(searchTerm) ||
                wine.type.toLowerCase().includes(searchTerm) ||
                wine.store.toLowerCase().includes(searchTerm)
            );
        }

        // Type filter
        if (currentFilter !== 'all') {
            filteredWines = filteredWines.filter(wine => wine.type.toLowerCase() === currentFilter.toLowerCase());
        }

        // Pairing filter
        if (currentPairing) {
            filteredWines = filteredWines.filter(wine =>
                wine.pairings && wine.pairings.includes(currentPairing)
            );
        }

        renderWines(filteredWines);
    }

    async function fetchWines() {
        try {
            let data = [];

            // Check cache first
            const cachedData = localStorage.getItem(CACHE_KEY);
            const cacheTimestamp = localStorage.getItem(CACHE_TIMESTAMP_KEY);
            const now = Date.now();

            if (cachedData && cacheTimestamp && (now - parseInt(cacheTimestamp)) < CACHE_DURATION) {
                console.log('Using cached data');
                data = JSON.parse(cachedData);
            } else {
                console.log('Fetching fresh data from server');
                // Add timestamp to prevent browser caching of the JSON file itself
                const response = await fetch(`${DATA_URL}?t=${now}`);
                if (!response.ok) throw new Error('Network response was not ok');
                data = await response.json();

                // Cache the data
                localStorage.setItem(CACHE_KEY, JSON.stringify(data));
                localStorage.setItem(CACHE_TIMESTAMP_KEY, now.toString());
            }

            allWines = data;

            // Enrich wines with local storage data (pairings)
            const localPairings = JSON.parse(localStorage.getItem('winePairings') || '{}');
            const personalScores = JSON.parse(localStorage.getItem('personalScores') || '{}');

            allWines = allWines.map(wine => {
                if (localPairings[wine.name]) {
                    wine.pairings = localPairings[wine.name].pairings || [];
                    wine.description = localPairings[wine.name].description || '';
                }
                wine.personalScore = personalScores[wine.name] || 0;
                return wine;
            });

            // Client-side filtering by store
            if (currentStore !== 'all') {
                allWines = allWines.filter(w => w.store && w.store.toLowerCase() === currentStore.toLowerCase());
            }

            // Client-side sorting
            if (currentSort === 'personal-score') {
                allWines.sort((a, b) => (b.personalScore || 0) - (a.personalScore || 0));
            } else if (currentSort === 'price-low') {
                allWines.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
            } else if (currentSort === 'price-high') {
                allWines.sort((a, b) => parseFloat(b.price) - parseFloat(a.price));
            } else if (currentSort === 'score') {
                allWines.sort((a, b) => parseFloat(b.vivino_score || 0) - parseFloat(a.vivino_score || 0));
            }

            applyFilters();

            // Loading spinner is removed by renderWines clearing the container
        } catch (error) {
            console.error('Error fetching wines:', error);
            wineList.innerHTML = `<p class="error">Failed to load wines: ${error.message}. Please check your connection.</p>`;
        }
    }

    function renderWines(wines) {
        wineList.innerHTML = '';

        if (wines.length === 0) {
            wineList.innerHTML = '<div class="no-results"><p>No wines found matching your criteria.</p></div>';
            return;
        }

        // Get personal scores
        const personalScores = JSON.parse(localStorage.getItem('personalScores') || '{}');

        wines.forEach(wine => {
            const card = document.createElement('div');
            card.className = 'wine-card';

            // Personal score
            const myScore = personalScores[wine.name] || 0;
            const myScoreHtml = myScore > 0
                ? `<div class="personal-score-badge"><i class="fas fa-star"></i> ${myScore}/5</div>`
                : '';

            // Pairing tags
            let pairingsHtml = '';
            if (wine.pairings && wine.pairings.length > 0) {
                const emojis = {
                    'Red meat': '🥩',
                    'White meat': '🍗',
                    'Seafood': '🦞',
                    'Fish': '🐟',
                    'Dessert': '🍰'
                };

                pairingsHtml = `<div class="pairing-tags">
                    ${wine.pairings.map(p => `<span class="pairing-tag" title="${p}">${emojis[p] || ''}</span>`).join('')}
                </div>`;
            }

            card.innerHTML = `
                <div class="wine-image">
                    <img src="${wine.image_url}" alt="${wine.name}" loading="lazy">
                </div>
                <div class="wine-info">
                    <div class="wine-header">
                        <div class="wine-meta">
                            <span class="wine-type-badge type-${wine.type.toLowerCase()}">${wine.type}</span>
                            ${myScore > 0 ? `<span class="personal-score-badge"><i class="fas fa-star"></i> ${myScore}/5</span>` : ''}
                        </div>
                        <a href="${wine.url}" target="_blank" class="external-link-btn" onclick="event.stopPropagation();" title="View on ${wine.store}">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                    <div class="wine-meta">
                        <span class="vivino-score"><i class="fas fa-star"></i> ${wine.vivino_score}</span>
                        ${pairingsHtml}
                    </div>
                    <h3>${wine.name}</h3>
                    <div class="wine-footer">
                        <span class="wine-price">€${wine.price}</span>
                    </div>
                </div>
            `;

            // Make entire card clickable
            card.addEventListener('click', (e) => {
                window.location.href = `/wine/${encodeURIComponent(wine.name)}`;
            });

            wineList.appendChild(card);
        });
    }
});
