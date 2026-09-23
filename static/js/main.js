document.addEventListener('DOMContentLoaded', () => {
    let templates = [];
    let assignments = { pc: {}, hp: {} };
    const days = [
        {id: 'mon', name: 'Senin'},
        {id: 'tue', name: 'Selasa'},
        {id: 'wed', name: 'Rabu'},
        {id: 'thu', name: 'Kamis'},
        {id: 'fri', name: 'Jumat'},
        {id: 'sat', name: 'Sabtu'},
        {id: 'sun', name: 'Minggu'}
    ];

    // Navigation
    const navDashboard = document.getElementById('nav-dashboard');
    const navSchedule = document.getElementById('nav-schedule');
    const navTemplates = document.getElementById('nav-templates');
    
    const viewDashboard = document.getElementById('view-dashboard');
    const viewSchedule = document.getElementById('view-schedule');
    const viewTemplates = document.getElementById('view-templates');

    // Hamburger Menu Logic
    const hamburger = document.getElementById('hamburger');
    const navLinksContainer = document.getElementById('nav-links');
    
    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navLinksContainer.classList.toggle('active');
        });
    }

    function switchView(view) {
        viewDashboard.style.display = view === 'dashboard' ? 'block' : 'none';
        viewSchedule.style.display = view === 'schedule' ? 'block' : 'none';
        viewTemplates.style.display = view === 'templates' ? 'block' : 'none';
        
        navDashboard.style.color = view === 'dashboard' ? 'var(--text-primary)' : 'var(--text-secondary)';
        navSchedule.style.color = view === 'schedule' ? 'var(--text-primary)' : 'var(--text-secondary)';
        navTemplates.style.color = view === 'templates' ? 'var(--text-primary)' : 'var(--text-secondary)';
        
        // Update URL hash without jumping
        history.replaceState(null, null, '#' + view);

        // Hide mobile menu after click
        if (window.innerWidth <= 768) {
            navLinksContainer.classList.remove('active');
        }
    }

    // Read initial hash on load
    const initialHash = window.location.hash.replace('#', '') || 'dashboard';
    switchView(initialHash);
    if(initialHash === 'templates') renderTemplatesList();

    navDashboard.addEventListener('click', (e) => { e.preventDefault(); switchView('dashboard'); });
    navSchedule.addEventListener('click', (e) => { e.preventDefault(); switchView('schedule'); });
    navTemplates.addEventListener('click', (e) => { e.preventDefault(); switchView('templates'); renderTemplatesList(); });

    // Fetch Initial Data
    async function fetchData() {
        try {
            const [tplRes, assRes, statRes, devRes] = await Promise.all([
                fetch('/api/templates'),
                fetch('/api/assignments'),
                fetch('/api/status'),
                fetch('/api/devices')
            ]);
            
            templates = await tplRes.json();
            const rawAssignments = await assRes.json();
            const devices = await devRes.json();
            
            if (rawAssignments.mon) {
                assignments = { pc: rawAssignments, hp: rawAssignments };
            } else {
                assignments = rawAssignments;
            }

            const status = await statRes.json();
            
            document.getElementById('toggle-pc').checked = status.pc_hafizh;
            document.getElementById('toggle-hp').checked = status.hp_hafizh;
            
            renderAssignments();
            renderDevices(devices);
        } catch (err) {
            console.error('Error fetching data:', err);
        }
    }

    function renderDevices(devices) {
        const list = document.getElementById('devices-list');
        list.innerHTML = '';
        if(devices.length === 0) {
            list.innerHTML = '<p style="color:var(--text-secondary)">No devices connected</p>';
            return;
        }
        
        devices.forEach(dev => {
            const div = document.createElement('div');
            div.className = 'status-item';
            div.style.alignItems = 'flex-start';
            div.innerHTML = `
                <div class="status-info" style="flex: 1; padding-right: 10px;">
                    <h3 style="color: var(--success); margin-bottom: 4px;">${dev.name}</h3>
                    <p style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4;">
                        MAC: ${dev.mac}<br>
                        IP: ${dev.ip}
                    </p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem;">
                    <label class="switch">
                        <input type="checkbox" onchange="toggleDeviceBlock('${dev.mac}', this.checked)" ${!dev.blocked ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                    <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;" onclick="renameDevice('${dev.mac}', '${dev.name}')">Rename</button>
                </div>
            `;
            list.appendChild(div);
        });
    }

    window.toggleDeviceBlock = async function(mac, isAllowed) {
        await fetch('/api/devices', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mac: mac, blocked: !isAllowed})
        });
        // We don't necessarily need to reload, but we can to be safe
    }
    
    window.renameDevice = async function(mac, currentName) {
        const { value: newName } = await Swal.fire({
            title: 'Rename Device',
            input: 'text',
            inputLabel: `Enter new name for MAC: ${mac}`,
            inputValue: currentName,
            showCancelButton: true,
            background: '#1e293b',
            color: '#f8fafc',
            confirmButtonColor: '#3b82f6',
            cancelButtonColor: '#64748b',
            inputValidator: (value) => {
                if (!value) {
                    return 'Name cannot be empty!'
                }
            }
        });
        
        if (newName && newName !== currentName) {
            await fetch('/api/devices', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mac: mac, name: newName})
            });
            fetchData(); // reload
        }
    }

    // Render Weekly Assignments
    function renderAssignments() {
        renderAssignmentTable('pc', 'assignments-body-pc');
        renderAssignmentTable('hp', 'assignments-body-hp');
    }

    function renderAssignmentTable(type, tbodyId) {
        const tbody = document.getElementById(tbodyId);
        tbody.innerHTML = '';
        
        days.forEach(day => {
            const tr = document.createElement('tr');
            
            const tdDay = document.createElement('td');
            tdDay.textContent = day.name;
            tdDay.style.fontWeight = '600';
            
            const tdSelect = document.createElement('td');
            const select = document.createElement('select');
            select.style.padding = '0.5rem';
            select.style.background = 'rgba(15, 23, 42, 0.6)';
            select.style.color = 'white';
            select.style.border = '1px solid var(--glass-border)';
            select.style.borderRadius = '8px';
            
            // Add a "No Template" option
            const optNone = document.createElement('option');
            optNone.value = "";
            optNone.textContent = "-- Pilih Template --";
            select.appendChild(optNone);

            templates.forEach(tpl => {
                const opt = document.createElement('option');
                opt.value = tpl.id;
                opt.textContent = tpl.name;
                if (assignments[type] && assignments[type][day.id] === tpl.id) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });
            
            select.addEventListener('change', (e) => {
                if (!assignments[type]) assignments[type] = {};
                assignments[type][day.id] = e.target.value;
                saveAssignments();
            });
            
            tdSelect.appendChild(select);
            
            tr.appendChild(tdDay);
            tr.appendChild(tdSelect);
            tbody.appendChild(tr);
        });
    }

    async function saveAssignments() {
        await fetch('/api/assignments', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(assignments)
        });
    }

    // Apply Schedule Button
    document.getElementById('btn-apply-schedule').addEventListener('click', async () => {
        const btn = document.getElementById('btn-apply-schedule');
        const origText = btn.innerHTML;
        btn.innerHTML = 'Applying...';
        btn.disabled = true;
        
        try {
            const res = await fetch('/api/apply', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Applied!',
                    text: data.message,
                    background: '#1e293b',
                    color: '#f8fafc',
                    confirmButtonColor: '#3b82f6'
                });
            }
        } catch (err) {
            Swal.fire({
                icon: 'error',
                title: 'Oops...',
                text: 'Failed to apply schedule.',
                background: '#1e293b',
                color: '#f8fafc',
                confirmButtonColor: '#ef4444'
            });
        } finally {
            btn.innerHTML = origText;
            btn.disabled = false;
        }
    });

    // Kill Switch Status
    const togglePc = document.getElementById('toggle-pc');
    const toggleHp = document.getElementById('toggle-hp');

    async function updateStatus() {
        await fetch('/api/status', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                pc_hafizh: togglePc.checked,
                hp_hafizh: toggleHp.checked
            })
        });
    }
    
    togglePc.addEventListener('change', updateStatus);
    toggleHp.addEventListener('change', updateStatus);

    // Template Manager
    let editingTemplateId = null;
    const modal = document.getElementById('template-modal');
    const sessionsContainer = document.getElementById('tpl-sessions');

    function renderTemplatesList() {
        const container = document.getElementById('templates-list');
        container.innerHTML = '';
        
        templates.forEach(tpl => {
            const div = document.createElement('div');
            div.className = 'status-item';
            
            const info = document.createElement('div');
            info.className = 'status-info';
            info.innerHTML = `<h3>${tpl.name}</h3><p>${tpl.sessions.length} Sesi Waktu</p>`;
            
            const btnEdit = document.createElement('button');
            btnEdit.className = 'btn-secondary';
            btnEdit.textContent = 'Edit';
            btnEdit.addEventListener('click', () => openTemplateModal(tpl.id));
            
            div.appendChild(info);
            div.appendChild(btnEdit);
            container.appendChild(div);
        });
    }

    function openTemplateModal(id = null) {
        editingTemplateId = id;
        sessionsContainer.innerHTML = '';
        
        if (id) {
            const tpl = templates.find(t => t.id === id);
            document.getElementById('modal-title').textContent = 'Edit Template';
            document.getElementById('tpl-name').value = tpl.name;
            tpl.sessions.forEach(s => addSessionRow(s.start, s.end));
        } else {
            document.getElementById('modal-title').textContent = 'Buat Template Baru';
            document.getElementById('tpl-name').value = '';
            addSessionRow('08:00', '12:00');
        }
        
        modal.classList.add('active');
    }

    function addSessionRow(start = '', end = '') {
        const div = document.createElement('div');
        div.className = 'session-row';
        div.innerHTML = `
            <input type="time" class="session-start" value="${start}" required>
            <span style="color:var(--text-secondary)">to</span>
            <input type="time" class="session-end" value="${end}" required>
            <button class="btn-remove" title="Remove Session">&times;</button>
        `;
        div.querySelector('.btn-remove').addEventListener('click', () => {
            div.remove();
        });
        sessionsContainer.appendChild(div);
    }

    document.getElementById('btn-add-session').addEventListener('click', () => addSessionRow());
    document.getElementById('btn-modal-cancel').addEventListener('click', () => modal.classList.remove('active'));
    document.getElementById('btn-new-template').addEventListener('click', () => openTemplateModal());

    document.getElementById('btn-modal-save').addEventListener('click', async () => {
        const name = document.getElementById('tpl-name').value;
        if (!name) return alert('Nama Template wajib diisi');
        
        const sessionElements = sessionsContainer.querySelectorAll('.session-row');
        const newSessions = [];
        sessionElements.forEach(el => {
            const start = el.querySelector('.session-start').value;
            const end = el.querySelector('.session-end').value;
            if (start && end) {
                newSessions.push({start, end});
            }
        });
        
        if (editingTemplateId) {
            const tpl = templates.find(t => t.id === editingTemplateId);
            tpl.name = name;
            tpl.sessions = newSessions;
        } else {
            const newId = 't' + Date.now();
            templates.push({id: newId, name, sessions: newSessions});
        }
        
        await fetch('/api/templates', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(templates)
        });
        
        modal.classList.remove('active');
        renderTemplatesList();
        renderAssignments(); // Re-render to update dropdowns
    });

    // Initialize
    fetchData();
});
