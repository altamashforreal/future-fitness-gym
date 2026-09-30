// ─────────────────────────────────────────────
//  GymFlow Frontend — API-Connected App
// ─────────────────────────────────────────────

const API_BASE = '/api';

// ── State ────────────────────────────────────
let allMembers = [];
let allPlans = [];
let memberToDelete = null;

// ── DOM Ready ────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupModal();
    setupDeleteModal();
    setupRenewModal();
    setupSearch();
    checkBackendHealth();
    loadDashboard();
});

// ─────────────────────────────────────────────
//  NAVIGATION
// ─────────────────────────────────────────────
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateTo(page);
        });
    });

    document.getElementById('view-all-members-link')?.addEventListener('click', e => {
        e.preventDefault();
        navigateTo('members');
    });
    document.getElementById('view-all-plans-link')?.addEventListener('click', e => {
        e.preventDefault();
        navigateTo('plans');
    });
}

function navigateTo(page) {
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navEl = document.querySelector(`[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');

    // Show/hide pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const pageEl = document.getElementById(`page-${page}`);
    if (pageEl) pageEl.classList.add('active');

    // Load data for the page
    if (page === 'dashboard') loadDashboard();
    if (page === 'members') loadMembersPage();
    if (page === 'plans') loadPlansPage();
    if (page === 'checkin') loadCheckinPage();
}

// ─────────────────────────────────────────────
//  BACKEND HEALTH CHECK
// ─────────────────────────────────────────────
async function checkBackendHealth() {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    const statEl = document.getElementById('stat-api-status');
    const statSub = document.getElementById('stat-api-sub');
    try {
        const res = await fetch('http://127.0.0.1:8000/health');
        if (res.ok) {
            dot.className = 'status-dot online';
            text.textContent = 'Backend Online';
            if (statEl) { statEl.textContent = 'Online'; statEl.style.color = 'var(--success)'; }
            if (statSub) statSub.textContent = 'http://127.0.0.1:8000';
        } else {
            throw new Error('not ok');
        }
    } catch {
        dot.className = 'status-dot offline';
        text.textContent = 'Backend Offline';
        if (statEl) { statEl.textContent = 'Offline'; statEl.style.color = 'var(--danger)'; }
        if (statSub) statSub.textContent = 'Run: uvicorn app.main:app --reload';
    }
}

// ─────────────────────────────────────────────
//  API HELPERS
// ─────────────────────────────────────────────
async function fetchMembers() {
    const res = await fetch(`${API_BASE}/members/`);
    if (!res.ok) throw new Error('Failed to fetch members');
    return res.json();
}

async function fetchPlans() {
    const res = await fetch(`${API_BASE}/plans/`);
    if (!res.ok) throw new Error('Failed to fetch plans');
    return res.json();
}

async function createMember(data) {
    const res = await fetch(`${API_BASE}/members/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || 'Failed to create member');
    return json;
}

async function deleteMember(id) {
    const res = await fetch(`${API_BASE}/members/${id}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error('Failed to delete member');
}

// ─────────────────────────────────────────────
//  DASHBOARD
// ─────────────────────────────────────────────
async function loadDashboard() {
    try {
        [allMembers, allPlans] = await Promise.all([fetchMembers(), fetchPlans()]);
        renderDashboardStats();
        renderDashboardMembersTable(allMembers.slice(0, 5));
        renderDashboardPlans(allPlans);
    } catch (err) {
        console.error('Dashboard load error:', err);
        document.getElementById('dashboard-members-tbody').innerHTML =
            `<tr><td colspan="5" class="error-row"><ion-icon name="alert-circle-outline"></ion-icon> ${err.message} — Is the backend running?</td></tr>`;
    }
}

function renderDashboardStats() {
    const total = allMembers.length;
    const active = allMembers.filter(m => m.membership_status === 'active').length;
    const expiring = allMembers.filter(m => m.membership_status === 'expiring').length;
    const expired = allMembers.filter(m => m.membership_status === 'expired').length;

    document.getElementById('stat-total-members').textContent = total;
    document.getElementById('stat-active-members').textContent = active;
    
    const expiringEl = document.getElementById('stat-expiring-members');
    if (expiringEl) expiringEl.textContent = expiring;
    
    const expiredEl = document.getElementById('stat-expired-members');
    if (expiredEl) expiredEl.textContent = expired;
    
    document.getElementById('stat-total-plans').textContent = allPlans.length;
}

function renderDashboardMembersTable(members) {
    const tbody = document.getElementById('dashboard-members-tbody');
    if (!members.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-row">No members yet. Add your first member!</td></tr>`;
        return;
    }
    tbody.innerHTML = members.map(m => {
        const ms = m.membership_status;
        const statusBadge = membershipStatusBadge(ms, m.days_remaining);
        const needsRenew = ms === 'expired' || ms === 'expiring' || ms === 'none';
        return `
        <tr>
            <td><strong>${m.member_id}</strong></td>
            <td>
                <div class="member-cell">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(m.first_name + '+' + m.last_name)}&background=random" alt="${m.first_name}">
                    <span>${m.first_name} ${m.last_name}</span>
                </div>
            </td>
            <td>${m.phone}</td>
            <td>${m.membership_plan ? `<span class="plan-tag">${m.membership_plan}</span>` : '<span class="text-muted">—</span>'}</td>
            <td>${statusBadge}</td>
            <td>${m.membership_end_date || '<span class="text-muted">—</span>'}</td>
            <td>
                <button class="btn-icon" onclick="openEditModal(${m.id})" title="Edit Member">
                    <ion-icon name="create-outline"></ion-icon>
                </button>
                ${needsRenew ? `<button class="btn-icon renew-btn" onclick="openRenewModal(${m.id}, '${m.first_name} ${m.last_name}')" title="Renew Membership"><ion-icon name="card-outline"></ion-icon></button>` : ''}
                <button class="btn-icon" onclick="openDeleteModal(${m.id}, '${m.first_name} ${m.last_name}')" title="Delete Member">
                    <ion-icon name="trash-outline"></ion-icon>
                </button>
            </td>
        </tr>`;
    }).join('');
    renderAlertTable();
}

function renderDashboardPlans(plans) {
    const container = document.getElementById('plans-grid-dashboard');
    if (!plans.length) {
        container.innerHTML = `<p class="empty-row">No plans found.</p>`;
        return;
    }
    container.innerHTML = plans.slice(0, 4).map(p => planCardHTML(p)).join('');
}

// ─────────────────────────────────────────────
//  MEMBERS PAGE
// ─────────────────────────────────────────────
async function loadMembersPage() {
    const tbody = document.getElementById('members-tbody');
    tbody.innerHTML = `<tr><td colspan="7" class="loading-row"><span class="spinner"></span> Loading members...</td></tr>`;
    try {
        allMembers = await fetchMembers();
        renderMembersTable(allMembers);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="error-row"><ion-icon name="alert-circle-outline"></ion-icon> ${err.message}</td></tr>`;
    }
}

function renderMembersTable(members) {
    const tbody = document.getElementById('members-tbody');
    const badge = document.getElementById('members-count-badge');
    if (badge) badge.textContent = `${members.length} member${members.length !== 1 ? 's' : ''}`;

    if (!members.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty-row">No members found. Add your first one!</td></tr>`;
        return;
    }

    tbody.innerHTML = members.map(m => {
        const ms = m.membership_status;
        const statusBadge = membershipStatusBadge(ms, m.days_remaining);
        const needsRenew = ms === 'expired' || ms === 'expiring' || ms === 'none';
        return `
        <tr>
            <td><span class="member-id-badge">${m.member_id}</span></td>
            <td>
                <div class="member-cell">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(m.first_name + '+' + m.last_name)}&background=random" alt="${m.first_name}">
                    <span>${m.first_name} ${m.last_name}</span>
                </div>
            </td>
            <td>${m.phone}</td>
            <td>${m.email || '<span class="text-muted">—</span>'}</td>
            <td class="capitalize">${m.gender || '<span class="text-muted">—</span>'}</td>
            <td>${m.membership_plan ? `<span class="plan-tag">${m.membership_plan}</span>` : '<span class="text-muted">No plan</span>'}</td>
            <td>${statusBadge}</td>
            <td>
                <button class="btn-icon" onclick="openEditModal(${m.id})" title="Edit Member">
                    <ion-icon name="create-outline"></ion-icon>
                </button>
                ${needsRenew ? `<button class="btn-icon renew-btn" onclick="openRenewModal(${m.id}, '${m.first_name} ${m.last_name}')" title="Renew Membership"><ion-icon name="card-outline"></ion-icon></button>` : ''}
                <button class="btn-icon" onclick="openDeleteModal(${m.id}, '${m.first_name} ${m.last_name}')" title="Delete Member">
                    <ion-icon name="trash-outline"></ion-icon>
                </button>
            </td>
        </tr>`;
    }).join('');
}

function membershipStatusBadge(status, daysRemaining) {
    if (status === 'active')   return `<span class="status-badge success">Active (${daysRemaining}d left)</span>`;
    if (status === 'expiring') return `<span class="status-badge warning">Expiring in ${daysRemaining}d</span>`;
    if (status === 'expired')  return `<span class="status-badge danger">Expired ${Math.abs(daysRemaining)}d ago</span>`;
    return `<span class="status-badge" style="background:rgba(255,255,255,0.05);color:var(--text-muted)">No Plan</span>`;
}

function renderAlertTable() {
    const alertMembers = allMembers.filter(m => m.membership_status === 'expired' || m.membership_status === 'expiring');
    const tbody = document.getElementById('alert-members-tbody');
    const badge = document.getElementById('alert-count-badge');
    
    if (badge) badge.textContent = `${alertMembers.length} member${alertMembers.length !== 1 ? 's' : ''}`;
    
    if (!alertMembers.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty-row" style="color:var(--success)"><ion-icon name="checkmark-circle-outline"></ion-icon> All members have valid memberships!</td></tr>`;
        return;
    }
    
    // Sort: expired first, then expiring by days remaining
    alertMembers.sort((a, b) => (a.days_remaining ?? 0) - (b.days_remaining ?? 0));
    
    tbody.innerHTML = alertMembers.map(m => {
        const isExpired = m.membership_status === 'expired';
        const daysLabel = isExpired
            ? `<span style="color:#ef4444;font-weight:600;">-${Math.abs(m.days_remaining)} days</span>`
            : `<span style="color:#f59e0b;font-weight:600;">${m.days_remaining} days</span>`;
        return `
        <tr class="${isExpired ? 'row-expired' : 'row-expiring'}">
            <td><span class="member-id-badge">${m.member_id}</span></td>
            <td>
                <div class="member-cell">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(m.first_name + '+' + m.last_name)}&background=random" alt="${m.first_name}">
                    <div>
                        <div>${m.first_name} ${m.last_name}</div>
                        <small class="text-muted">${m.phone}</small>
                    </div>
                </div>
            </td>
            <td>${m.phone}</td>
            <td>${m.membership_plan ? `<span class="plan-tag">${m.membership_plan}</span>` : '—'}</td>
            <td>${m.membership_end_date || '—'}</td>
            <td>${daysLabel}</td>
            <td>${membershipStatusBadge(m.membership_status, m.days_remaining)}</td>
            <td>
                <button class="btn btn-primary" style="padding:6px 14px;font-size:0.82rem;" onclick="openRenewModal(${m.id}, '${m.first_name} ${m.last_name}')">
                    <ion-icon name="card-outline"></ion-icon> Renew
                </button>
            </td>
        </tr>`;
    }).join('');
}

// ─────────────────────────────────────────────
//  PLANS PAGE
// ─────────────────────────────────────────────
async function loadPlansPage() {
    const container = document.getElementById('plans-grid-full');
    container.innerHTML = `<div class="loading-row"><span class="spinner"></span> Loading plans...</div>`;
    try {
        allPlans = await fetchPlans();
        container.innerHTML = allPlans.map(p => planCardHTML(p)).join('');
    } catch (err) {
        container.innerHTML = `<p class="error-row"><ion-icon name="alert-circle-outline"></ion-icon> ${err.message}</p>`;
    }
}

function planCardHTML(plan) {
    const icons = { Monthly: 'calendar-outline', Quarterly: 'layers-outline', 'Half-Yearly': 'trending-up-outline', Annual: 'ribbon-outline', 'Personal Training': 'body-outline', Locker: 'lock-closed-outline' };
    const icon = icons[plan.name] || 'pricetag-outline';
    return `
        <div class="plan-card ${plan.is_addon ? 'addon' : ''}">
            <div class="plan-icon"><ion-icon name="${icon}"></ion-icon></div>
            <div class="plan-name">${plan.name}</div>
            <div class="plan-price">₹${plan.price.toLocaleString('en-IN')}</div>
            <div class="plan-duration">${plan.duration_days} days</div>
            ${plan.is_addon ? '<span class="plan-badge">Addon</span>' : '<span class="plan-badge base">Base Plan</span>'}
        </div>
    `;
}

// ─────────────────────────────────────────────
//  SEARCH
// ─────────────────────────────────────────────
function setupSearch() {
    // Global top bar search
    document.getElementById('global-search')?.addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        const filtered = allMembers.filter(m =>
            `${m.first_name} ${m.last_name}`.toLowerCase().includes(q) ||
            m.phone.includes(q) || (m.member_id && m.member_id.toLowerCase().includes(q))
        );
        // Navigate to members page and filter
        navigateTo('members');
        renderMembersTable(filtered);
    });

    // In-page members search
    document.getElementById('member-search-input')?.addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        const filtered = allMembers.filter(m =>
            `${m.first_name} ${m.last_name}`.toLowerCase().includes(q) ||
            m.phone.includes(q) || (m.member_id && m.member_id.toLowerCase().includes(q))
        );
        renderMembersTable(filtered);
    });
}

// ─────────────────────────────────────────────
//  ADD / EDIT MEMBER MODAL
// ─────────────────────────────────────────────
function setupModal() {
    const modal = document.getElementById('member-modal');
    const form = document.getElementById('member-form');

    const openModal = () => {
        document.getElementById('member-modal-title').textContent = 'Add New Member';
        document.getElementById('member-modal-desc').textContent = 'Fill in the details to register a new gym member.';
        document.getElementById('submit-member-text').textContent = 'Add Member';
        document.getElementById('edit_member_id').value = '';
        
        modal.classList.add('open');
        form.reset();
        hideFormMessages();
    };
    
    const closeModal = () => modal.classList.remove('open');

    document.getElementById('open-add-member-btn')?.addEventListener('click', openModal);
    document.getElementById('open-add-member-btn-2')?.addEventListener('click', openModal);
    document.getElementById('close-modal-btn')?.addEventListener('click', closeModal);
    document.getElementById('cancel-modal-btn')?.addEventListener('click', closeModal);

    // Close on backdrop click
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    // Form submit
    form.addEventListener('submit', async e => {
        e.preventDefault();
        hideFormMessages();

        const submitBtn = document.getElementById('submit-member-btn');
        const btnSpan = submitBtn.querySelector('span');
        submitBtn.disabled = true;
        
        const isEditing = !!document.getElementById('edit_member_id').value;
        btnSpan.textContent = isEditing ? 'Saving...' : 'Adding...';

        const data = buildFormData(form);
        const editId = document.getElementById('edit_member_id').value;
        delete data.edit_member_id;

        try {
            if (isEditing) {
                const res = await fetch(`${API_BASE}/members/${editId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const json = await res.json();
                if (!res.ok) throw new Error(json.detail || 'Failed to update member');
                
                showFormSuccess(`✅ Member <strong>${json.first_name} ${json.last_name}</strong> updated successfully!`);
                
                // Update in local state
                const index = allMembers.findIndex(m => m.id == editId);
                if (index !== -1) allMembers[index] = json;
                
            } else {
                const newMember = await createMember(data);
                showFormSuccess(`✅ Member <strong>${newMember.first_name} ${newMember.last_name}</strong> added successfully! ID: <strong>${newMember.member_id}</strong>`);
                allMembers.unshift(newMember);
            }
            
            renderDashboardStats();
            renderDashboardMembersTable(allMembers.slice(0, 5));
            if (document.getElementById('page-members').classList.contains('active')) {
                renderMembersTable(allMembers);
            }
            
            setTimeout(() => closeModal(), 2000);
        } catch (err) {
            showFormError(`❌ ${err.message}`);
        } finally {
            submitBtn.disabled = false;
            btnSpan.textContent = isEditing ? 'Save Member' : 'Add Member';
        }
    });
}

window.openEditModal = function(id) {
    const member = allMembers.find(m => m.id === id);
    if (!member) return;

    const modal = document.getElementById('member-modal');
    const form = document.getElementById('member-form');
    hideFormMessages();

    document.getElementById('member-modal-title').textContent = 'Edit Member';
    document.getElementById('member-modal-desc').textContent = `Update details for ${member.first_name} ${member.last_name}.`;
    document.getElementById('submit-member-text').textContent = 'Save Changes';
    
    // Populate form
    document.getElementById('edit_member_id').value = member.id;
    document.getElementById('first_name').value = member.first_name || '';
    document.getElementById('last_name').value = member.last_name || '';
    document.getElementById('phone').value = member.phone || '';
    document.getElementById('email').value = member.email || '';
    document.getElementById('date_of_birth').value = member.date_of_birth || '';
    document.getElementById('gender').value = member.gender || '';
    document.getElementById('address').value = member.address || '';
    document.getElementById('emergency_contact').value = member.emergency_contact || '';

    modal.classList.add('open');
};

function buildFormData(form) {
    const raw = Object.fromEntries(new FormData(form).entries());
    // Remove empty optional fields
    const cleaned = {};
    for (const [k, v] of Object.entries(raw)) {
        if (v !== '') cleaned[k] = v;
    }
    return cleaned;
}

function showFormError(msg) {
    const el = document.getElementById('form-error');
    el.innerHTML = msg;
    el.style.display = 'block';
}

function showFormSuccess(msg) {
    const el = document.getElementById('form-success');
    el.innerHTML = msg;
    el.style.display = 'block';
}

function hideFormMessages() {
    document.getElementById('form-error').style.display = 'none';
    document.getElementById('form-success').style.display = 'none';
}

// ─────────────────────────────────────────────
//  DELETE MEMBER MODAL
// ─────────────────────────────────────────────
function setupDeleteModal() {
    const modal = document.getElementById('delete-modal');
    const closeModal = () => { modal.classList.remove('open'); memberToDelete = null; };

    document.getElementById('close-delete-modal')?.addEventListener('click', closeModal);
    document.getElementById('cancel-delete-btn')?.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    document.getElementById('confirm-delete-btn')?.addEventListener('click', async () => {
        if (!memberToDelete) return;
        const btn = document.getElementById('confirm-delete-btn');
        btn.disabled = true;
        btn.innerHTML = '<ion-icon name="hourglass-outline"></ion-icon> Deleting...';

        try {
            await deleteMember(memberToDelete.id);
            allMembers = allMembers.filter(m => m.id !== memberToDelete.id);
            renderMembersTable(allMembers);
            renderDashboardStats();
            renderDashboardMembersTable(allMembers.slice(0, 5));
            closeModal();
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<ion-icon name="trash-outline"></ion-icon> Delete';
        }
    });
}

function openDeleteModal(id, name) {
    memberToDelete = { id, name };
    document.getElementById('delete-member-name').textContent = name;
    document.getElementById('delete-modal').classList.add('open');
}

// ─────────────────────────────────────────────
//  RENEW MEMBERSHIP MODAL
// ─────────────────────────────────────────────
let currentRenewMember = null;

function setupRenewModal() {
    const modal = document.getElementById('renew-modal');
    const form = document.getElementById('renew-form');

    const closeModal = () => modal.classList.remove('open');

    document.getElementById('close-renew-modal')?.addEventListener('click', closeModal);
    document.getElementById('cancel-renew-btn')?.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    // WhatsApp Link Generation — sends directly via Twilio (no WhatsApp Web)
    document.getElementById('send-wa-link-btn')?.addEventListener('click', async () => {
        const planId = document.getElementById('renew_plan_id').value;
        if (!planId) {
            showRenewError("Please select a plan first to send a payment link.");
            return;
        }
        if (!currentRenewMember) return;

        const btn = document.getElementById('send-wa-link-btn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '⏳ Sending...';

        const host = window.location.origin;
        const payUrl = `${host}/frontend/pay.html?member_id=${currentRenewMember.id}&plan_id=${planId}`;

        try {
            const res = await fetch(`${API_BASE}/members/${currentRenewMember.id}/send-payment-link`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plan_id: parseInt(planId), pay_url: payUrl })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to send');
            }

            showRenewSuccess("✅ Payment link sent to " + currentRenewMember.first_name + "'s WhatsApp!");
        } catch (err) {
            showRenewError("❌ Could not send WhatsApp: " + err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });

    form.addEventListener('submit', async e => {
        e.preventDefault();
        
        document.getElementById('renew-form-error').style.display = 'none';
        document.getElementById('renew-form-success').style.display = 'none';

        const submitBtn = document.getElementById('submit-renew-btn');
        const btnSpan = submitBtn.querySelector('span');
        submitBtn.disabled = true;
        btnSpan.textContent = 'Processing...';

        const memberId = document.getElementById('renew-member-id').value;
        const data = buildFormData(form);
        
        const payload = {
            member_id: parseInt(memberId),
            plan_id: parseInt(data.plan_id),
            start_date: data.start_date || null,
            payment_method: data.payment_method,
            transaction_id: data.transaction_id || null,
            is_renewal: true,
            addon_ids: []
        };

        try {
            const res = await fetch(`${API_BASE}/memberships/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const json = await res.json();
            if (!res.ok) throw new Error(json.detail || 'Failed to renew membership');
            
            showRenewSuccess(`✅ Membership renewed successfully! Valid until ${json.end_date}`);
            
            setTimeout(() => {
                closeModal();
                loadMembersPage(); // Refresh table
                if (document.getElementById('page-dashboard').classList.contains('active')) {
                    loadDashboard();
                }
            }, 2000);
        } catch (err) {
            showRenewError(`❌ ${err.message}`);
        } finally {
            submitBtn.disabled = false;
            btnSpan.textContent = 'Cash / Direct Renew';
        }
    });
}

function showRenewError(msg) {
    const errEl = document.getElementById('renew-form-error');
    errEl.innerHTML = msg;
    errEl.style.display = 'block';
}

function showRenewSuccess(msg) {
    const successEl = document.getElementById('renew-form-success');
    successEl.innerHTML = msg;
    successEl.style.display = 'block';
}

function openRenewModal(id, name) {
    document.getElementById('renew-member-id').value = id;
    document.getElementById('renew-member-name').textContent = name;
    currentRenewMember = allMembers.find(m => m.id === id);
    
    // Set today as default start date
    document.getElementById('renew_start_date').value = new Date().toISOString().split('T')[0];
    
    document.getElementById('renew-form-error').style.display = 'none';
    document.getElementById('renew-form-success').style.display = 'none';
    
    // Populate plans
    const select = document.getElementById('renew_plan_id');
    select.innerHTML = '<option value="">— Select Plan —</option>' + 
        allPlans.filter(p => !p.is_addon).map(p => 
            `<option value="${p.id}">${p.name} (₹${p.price})</option>`
        ).join('');
        
    document.getElementById('renew-modal').classList.add('open');
}


// ─────────────────────────────────────────────
//  Row highlight animation CSS (dynamic)
// ─────────────────────────────────────────────
const style = document.createElement('style');
style.textContent = `
    @keyframes highlight {
        0% { background-color: rgba(59, 130, 246, 0.15); }
        100% { background-color: transparent; }
    }
`;
document.head.appendChild(style);

// ─────────────────────────────────────────────
//  CHECK-IN LOGIC
// ─────────────────────────────────────────────
async function loadCheckinPage() {
    await fetchTodayCheckins();
    setupCheckinForm();
}

async function fetchTodayCheckins() {
    try {
        const res = await fetch(`${API_BASE}/checkins/today`);
        if (!res.ok) throw new Error('Failed to fetch check-in log');
        const logs = await res.json();
        renderCheckinLog(logs);
    } catch (err) {
        document.getElementById('checkin-log-tbody').innerHTML = 
            `<tr><td colspan="4" class="error-row"><ion-icon name="alert-circle-outline"></ion-icon> ${err.message}</td></tr>`;
    }
}

function renderCheckinLog(logs) {
    const tbody = document.getElementById('checkin-log-tbody');
    document.getElementById('checkin-today-count').textContent = `${logs.length} check-ins today`;
    
    if (!logs.length) {
        tbody.innerHTML = `<tr><td colspan="4" class="empty-row">No check-ins today yet.</td></tr>`;
        return;
    }
    
    tbody.innerHTML = logs.map(ci => {
        const time = new Date(ci.checked_in_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        return `
            <tr>
                <td><strong>${ci.member_name}</strong> <br><small class="text-muted">${ci.member_id}</small></td>
                <td><span class="capitalize">${ci.method}</span></td>
                <td>${time}</td>
                <td><span class="status-badge ${ci.status === 'allowed' ? 'success' : ci.status === 'expiring' ? 'warning' : 'danger'}">${ci.status}</span></td>
            </tr>
        `;
    }).join('');
}

function setupCheckinForm() {
    const manualBtn = document.getElementById('checkin-submit-btn');
    const bioBtn = document.getElementById('biometric-submit-btn');
    const refreshBtn = document.getElementById('refresh-log-btn');
    
    if (manualBtn.dataset.bound) return; // prevent double binding
    manualBtn.dataset.bound = "true";
    
    manualBtn.addEventListener('click', async () => {
        const query = document.getElementById('checkin-query').value.trim();
        const method = document.querySelector('input[name="checkin_method"]:checked').value;
        if (!query) return;
        
        await submitCheckin(`${API_BASE}/checkins/`, { query, method });
        document.getElementById('checkin-query').value = '';
    });
    
    bioBtn.addEventListener('click', async () => {
        const memberId = document.getElementById('biometric-query').value.trim();
        if (!memberId) return;
        
        // Simulating the payload a biometric device sends
        const payload = {
            biometric_user_id: memberId,
            device_id: "SIMULATOR_1",
            device_secret: "biometric-secret-change-me"
        };
        await submitCheckin(`${API_BASE}/checkins/biometric/verify`, payload);
        document.getElementById('biometric-query').value = '';
    });
    
    refreshBtn.addEventListener('click', fetchTodayCheckins);
}

async function submitCheckin(url, payload) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (!res.ok) {
            showCheckinResult({ status: 'error', message: data.detail || 'Check-in failed' });
            return;
        }
        
        showCheckinResult(data);
        fetchTodayCheckins(); // Refresh the log
    } catch (err) {
        showCheckinResult({ status: 'error', message: err.message });
    }
}

function showCheckinResult(result) {
    const card = document.getElementById('checkin-result-card');
    const icon = document.getElementById('result-icon');
    const nameEl = document.getElementById('result-name');
    const idEl = document.getElementById('result-member-id');
    const planEl = document.getElementById('result-plan');
    const msgEl = document.getElementById('result-message');
    
    card.className = 'checkin-result-card visible';
    
    // Clear previous
    nameEl.textContent = '';
    idEl.textContent = '';
    planEl.textContent = '';
    
    if (result.status === 'allowed') {
        card.classList.add('success');
        icon.innerHTML = '<ion-icon name="checkmark-circle"></ion-icon>';
        nameEl.textContent = result.full_name;
        idEl.textContent = `ID: ${result.member_id}`;
        planEl.textContent = `Plan: ${result.plan_name} (Expires: ${result.expires_on})`;
        msgEl.innerHTML = `<strong>ACCESS GRANTED</strong><br>${result.message}`;
    } 
    else if (result.status === 'expiring') {
        card.classList.add('warning');
        icon.innerHTML = '<ion-icon name="alert-circle"></ion-icon>';
        nameEl.textContent = result.full_name;
        idEl.textContent = `ID: ${result.member_id}`;
        planEl.textContent = `Plan: ${result.plan_name} (Expires: ${result.expires_on})`;
        msgEl.innerHTML = `<strong>ACCESS GRANTED (EXPIRING SOON)</strong><br>${result.message}`;
    }
    else if (result.status === 'denied') {
        card.classList.add('danger');
        icon.innerHTML = '<ion-icon name="close-circle"></ion-icon>';
        nameEl.textContent = result.full_name || 'Unknown';
        if (result.member_id !== '—') idEl.textContent = `ID: ${result.member_id}`;
        if (result.plan_name) planEl.textContent = `Last Plan: ${result.plan_name} (Expired: ${result.expires_on})`;
        msgEl.innerHTML = `<strong>ACCESS DENIED</strong><br>${result.message}`;
    }
    else {
        // Error
        card.classList.add('danger');
        icon.innerHTML = '<ion-icon name="warning"></ion-icon>';
        msgEl.textContent = result.message;
    }
}
