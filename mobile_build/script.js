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

    // Scroll to Top Button
    const scrollToTopBtn = document.getElementById('scroll-to-top');

    // Configuration
    // Fetch wine data from GitHub Pages (allows remote updates without app rebuild)
    // Fallback to local file if offline
    const DATA_URL = 'https://macdudu2014.github.io/winevino/mobile_build/wines.json';
    const CACHE_KEY = 'winevinoCachedDataV3'; // Changed to force cache refresh
    const CACHE_TIMESTAMP_KEY = 'winevinoCacheTimestampV3'; // Changed to force cache refresh
    const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

    let allWines = [];
    let currentFilter = 'all';
    let currentStore = 'all';
    let currentPairing = null;
    let currentSort = 'score'; // Default sort

    // Pagination for performance
    let currentPage = 1;
    const WINES_PER_PAGE = 50; // Load 50 wines at a time
    let isLoading = false;


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

    function renderWines(wines, append = false) {
        if (!append) {
            wineList.innerHTML = '';
            currentPage = 1;
        }

        if (wines.length === 0 && !append) {
            wineList.innerHTML = '<div class="no-results"><p>No wines found matching your criteria.</p></div>';
            return;
        }

        // Calculate which wines to show
        const startIndex = (currentPage - 1) * WINES_PER_PAGE;
        const endIndex = startIndex + WINES_PER_PAGE;
        const winesToShow = wines.slice(startIndex, endIndex);

        // Get personal scores
        const personalScores = JSON.parse(localStorage.getItem('personalScores') || '{}');

        winesToShow.forEach(wine => {
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
                            <span class="store-badge store-${wine.store.toLowerCase().replace(/\s+/g, '-')}">${wine.store}</span>
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
                // Use query parameter for standalone detail page
                window.location.href = `detail.html?name=${encodeURIComponent(wine.name)}`;
            });

            wineList.appendChild(card);
        });

        // Show "Load More" button if there are more wines
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (endIndex < wines.length) {
            if (!loadMoreBtn) {
                const btn = document.createElement('button');
                btn.id = 'load-more-btn';
                btn.className = 'load-more-btn';
                btn.textContent = 'Load More Wines';
                btn.addEventListener('click', () => {
                    currentPage++;
                    renderWines(wines, true);
                });
                wineList.appendChild(btn);
            }
        } else if (loadMoreBtn) {
            loadMoreBtn.remove();
        }
    }

    // Scroll to Top Button Logic
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.classList.add('visible');
        } else {
            scrollToTopBtn.classList.remove('visible');
        }
    });

    scrollToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});
