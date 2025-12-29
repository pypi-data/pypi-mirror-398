let currentCollection = '';
let currentPage = 1;
const pageSize = 10;

async function fetchAllCollections() {
    try {
        // Fetch scraped collections
        const resCol = await fetch('/collections');
        const dataCol = await resCol.json();

        // Fetch user uploads
        const resUp = await fetch('/datasets/list', {
            credentials: 'include'
        });
        const dataUp = await resUp.json();

        const uploadsList = document.getElementById('uploads-list');
        const collectionList = document.getElementById('collection-list');

        uploadsList.innerHTML = '';
        collectionList.innerHTML = '';

        // Render Uploads
        dataUp.forEach(dataset => {
            const li = document.createElement('li');
            li.className = 'collection-item';
            li.textContent = dataset.filename;
            li.dataset.collection = dataset.mongo_collection_name;
            li.onclick = () => selectCollection(dataset.mongo_collection_name, dataset.filename);
            uploadsList.appendChild(li);
        });

        // Render Scraped Collections
        dataCol.collections.forEach(col => {
            const li = document.createElement('li');
            li.className = 'collection-item';
            li.textContent = col;
            li.dataset.collection = col;
            li.onclick = () => selectCollection(col, col);
            collectionList.appendChild(li);
        });

        if (!currentCollection) {
            if (dataUp.length > 0) {
                selectCollection(dataUp[0].mongo_collection_name, dataUp[0].filename);
            } else if (dataCol.collections.length > 0) {
                selectCollection(dataCol.collections[0], dataCol.collections[0]);
            }
        }
    } catch (err) {
        console.error("Failed to fetch collections:", err);
    }
}

async function selectCollection(collectionName, displayName) {
    currentCollection = collectionName;
    currentPage = 1;
    document.querySelectorAll('.collection-item').forEach(el => {
        el.classList.toggle('active', el.dataset.collection === collectionName);
    });
    fetchData();
}

async function fetchData() {
    if (!currentCollection) return;

    const search = document.getElementById('search-input').value;
    const loader = document.getElementById('loader');
    const table = document.getElementById('data-table-container');

    loader.style.display = 'flex';
    table.style.opacity = '0.3';

    try {
        const res = await fetch(`/data/${currentCollection}?page=${currentPage}&page_size=${pageSize}&q=${search}`);
        const data = await res.json();

        renderTable(data.items);
        updatePagination(data);
    } catch (err) {
        console.error("Failed to fetch data:", err);
    } finally {
        loader.style.display = 'none';
        table.style.opacity = '1';
    }
}

function renderTable(items) {
    const head = document.getElementById('table-head');
    const body = document.getElementById('table-body');

    head.innerHTML = '';
    body.innerHTML = '';

    if (!items || items.length === 0) {
        body.innerHTML = '<tr><td colspan="5" class="text-center">No data found in this collection.</td></tr>';
        return;
    }

    const keys = Object.keys(items[0]).filter(k => k !== '_id');
    keys.forEach(key => {
        const th = document.createElement('th');
        th.textContent = key.charAt(0).toUpperCase() + key.slice(1);
        head.appendChild(th);
    });

    items.forEach(item => {
        const tr = document.createElement('tr');
        keys.forEach(key => {
            const td = document.createElement('td');
            let val = item[key];
            if (typeof val === 'object') val = JSON.stringify(val).substring(0, 50) + '...';
            td.textContent = (val === null || val === undefined) ? '' : val;
            tr.appendChild(td);
        });
        body.appendChild(tr);
    });
}

function updatePagination(data) {
    document.getElementById('page-info').textContent = `Page ${data.page} of ${data.total_pages}`;
    document.getElementById('prev-btn').disabled = data.page <= 1;
    document.getElementById('next-btn').disabled = data.page >= data.total_pages;
}

document.getElementById('prev-btn').onclick = () => {
    if (currentPage > 1) {
        currentPage--;
        fetchData();
    }
};

document.getElementById('next-btn').onclick = () => {
    currentPage++;
    fetchData();
};

let searchTimeout;
document.getElementById('search-input').oninput = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        fetchData();
    }, 500);
};

// Initial Load
fetchAllCollections();

// --- Mobile Sidebar Toggle ---
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('dashboard-sidebar');

if (sidebarToggle && sidebar) {
    sidebarToggle.onclick = () => {
        sidebar.classList.toggle('active');
    };

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });

    // Close sidebar when selecting a collection on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && e.target.classList.contains('collection-item')) {
            sidebar.classList.remove('active');
        }
    });
}

// --- File Upload ---
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-upload');

uploadBtn.onclick = () => {
    fileInput.click();
};

fileInput.onchange = async () => {
    if (fileInput.files.length === 0) return;

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const loader = document.getElementById('loader');
    loader.style.display = 'flex';
    document.getElementById('data-table-container').style.opacity = '0.3';

    try {
        const res = await fetch('/datasets/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'  // Include cookies for authentication
        });
        const data = await res.json();

        if (res.ok) {
            alert(`Success: ${data.message}`);
            // Refresh collections
            await fetchAllCollections();
            // Select the new collection (first sheet if multiple)
            if (data.datasets && data.datasets.length > 0) {
                selectCollection(data.datasets[0].collection_name, data.datasets[0].filename);
            } else if (data.collection_name) {
                selectCollection(data.collection_name, data.filename || data.collection_name);
            }
        } else {
            // Check for authentication error
            if (res.status === 401) {
                alert('Your session has expired. Please log in again.');
                window.location.href = '/login';
                return;
            }
            alert(`Error: ${data.detail || "Upload failed"}`);
        }
    } catch (err) {
        console.error("Upload error:", err);
        alert("An unexpected error has occurred. Please check your connection and try again.");
    } finally {
        loader.style.display = 'none';
        document.getElementById('data-table-container').style.opacity = '1';
        fileInput.value = ''; // Reset input
    }
};
