// --- 1. SYSTEM INITIALIZATION & LOGIN ---
function saveLogin() {
    const nameInput = document.getElementById('opName');
    const name = nameInput.value.trim();
    if (!name) return alert("Security clearance required.");

    localStorage.setItem('opName', name);
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('main-app').classList.remove('system-offline');
    document.getElementById('topBanner').classList.add('banner-online');
    
    const display = document.getElementById('operatorDisplay');
    const sideDisplay = document.getElementById('sideUserName');
    
    if (display) display.innerHTML = `<i class="fas fa-user-shield text-green-300 mr-2"></i> OPERATOR: ${name.toUpperCase()}`;
    if (sideDisplay) sideDisplay.innerText = `Operator: ${name.toUpperCase()}`;
}

function logout() {
    if(confirm("Confirm system shutdown?")) {
        localStorage.removeItem('opName');
        location.reload();
    }
}

window.onload = () => {
    const savedName = localStorage.getItem('opName');
    if (savedName) {
        document.getElementById('opName').value = savedName;
        saveLogin();
    }
};

// --- 2. HISTORY MODAL LOGIC ---
function showHistory() {
    const modal = document.getElementById('historyModal');
    const log = document.getElementById('historyLog');
    const history = JSON.parse(localStorage.getItem('triageHistory') || '[]');

    if (history.length > 0) {
        log.innerHTML = history.map(item => `
            <div class="p-4 bg-white rounded-2xl border-2 border-[#C7AF94] flex justify-between items-center animate-in fade-in duration-300">
                <div>
                    <p class="text-[10px] font-black text-[#95714F] uppercase">${item.time} | ${item.district}</p>
                    <p class="text-sm font-bold text-slate-800">${item.location}</p>
                </div>
                <span class="text-lg font-black ${parseFloat(item.severity) >= 8 ? 'text-red-500' : 'text-[#8C916C]'}">${item.severity}</span>
            </div>
        `).reverse().join('');
    }
    modal.classList.remove('hidden');
}

function closeHistory() { document.getElementById('historyModal').classList.add('hidden'); }

function clearHistory() {
    if(confirm("Wipe all historical mission data?")) {
        localStorage.removeItem('triageHistory');
        showHistory();
    }
}

// --- 3. DISASTER MAPPING ---
const DISASTER_MAP = {
    'Flood': { text: "Heavy river flooding. Water levels rising.", check: ["River flooding", "Urban flooding", "Dam overflow"] },
    'Landslide': { text: "Landslide detected. Roads blocked.", check: ["Slope collapse", "Road blockage", "House burial"] },
    'Forest Fire': { text: "Forest fire spreading. Smoke inhalation risk.", check: ["Wildlife risk", "Smoke spread"] },
    'Cyclone': { text: "Strong winds and storm surge.", check: ["Coastal flooding", "Power outage"] },
    'Drought': { text: "Water scarcity and crop failure.", check: ["Water scarcity", "Heat stress"] },
    'Building Collapse': { text: "Structure failure. People trapped.", check: ["People trapped", "Gas leak"] },
    'Bridge Collapse': { text: "Bridge washout. Traffic cut off.", check: ["Structural failure", "Submerged vehicles"] },
    'Road Damage': { text: "Highway cut off. Sinkhole detected.", check: ["Highway blocked", "Sinkhole"] },
    'Dam Risk': { text: "Structural risk at dam. Leakage visible.", check: ["Structural crack", "Leakage"] },
    'Power Grid': { text: "Power failure. Hospitals on backup.", check: ["Blackout", "Hospital risk"] },
    'Medical': { text: "Mass casualty incident. Multiple injuries.", check: ["Trauma", "Oxygen needed"] },
    'Industrial Leak': { text: "Chemical gas leak. Breathing difficulties.", check: ["Gas risk", "Contamination"] },
    'Explosion': { text: "Gas explosion in market area.", check: ["Secondary fire", "Blast injury"] },
    'Urban Fire': { text: "High-rise fire. Exits blocked.", check: ["Smoke inhalation", "Short circuit"] },
    'Accident': { text: "Major highway accident. Victims trapped.", check: ["Fuel leak", "Entrapment"] }
};

// --- 4. UI INTERACTION ---
function selectDisaster(type) {
    const drawer = document.getElementById('inlineChecklist');
    const container = document.getElementById('dynamicChecklist');
    const input = document.getElementById('rawInput');
    const data = DISASTER_MAP[type];

    input.value = data.text;
    document.getElementById('checklistTitle').innerText = `${type.toUpperCase()} FIELD VERIFICATION`;
    
    container.innerHTML = `
        <div class="flex flex-col lg:flex-row gap-6 items-stretch w-full">
            <div class="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                ${data.check.map(item => `
                    <label class="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100 cursor-pointer hover:bg-white transition-all group">
                        <input type="checkbox" class="w-5 h-5 accent-[#8C916C]">
                        <span class="text-[10px] font-bold text-slate-600 uppercase group-hover:text-[#95714F]">${item}</span>
                    </label>
                `).join('')}
            </div>
            <div class="flex items-center justify-center border-l border-slate-200 pl-6">
                <button onclick="processData()" class="h-full bg-[#8C916C] hover:bg-[#95714F] text-white px-8 rounded-2xl font-black uppercase text-xs shadow-lg flex flex-col items-center justify-center gap-2 min-w-[140px] active:scale-95 transition-all">
                    <i class="fas fa-paper-plane text-xl"></i>
                    <span>Dispatch</span>
                </button>
            </div>
        </div>
    `;

    drawer.classList.remove('hidden');
    drawer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.querySelectorAll('.glass-card').forEach(b => b.classList.remove('active-btn'));
    const btnId = `btn-${type.replace(/\s+/g, '')}`;
    if(document.getElementById(btnId)) document.getElementById(btnId).classList.add('active-btn');
}

// --- 5. API & FEED LOGIC ---
async function processData() {
    const input = document.getElementById('rawInput').value;
    const locInput = document.getElementById('manualLocation').value;
    const btn = document.getElementById('btnText');
    
    if (!input.trim()) return alert("Enter triage details.");

    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Analyzing...';
    btn.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:8000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: input, manual_location: locInput })
        });

        if (!response.ok) throw new Error("Server Error");
        const data = await response.json();
        
        // Manual Location Priority
        const finalLoc = locInput.trim() || data.location || "Unknown Site";
        const finalSev = data.final_severity || data.severity || "5.0";

        // Save to History
        const history = JSON.parse(localStorage.getItem('triageHistory') || '[]');
        history.push({
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            location: finalLoc,
            district: data.district || "Karnataka HQ",
            severity: finalSev
        });
        localStorage.setItem('triageHistory', JSON.stringify(history));

        addCardToFeed(data, finalLoc, finalSev);
        document.getElementById('manualLocation').value = '';
        document.getElementById('rawInput').value = '';

    } catch (error) {
        alert("Connection Error: Is FastAPI running?");
    } finally {
        btn.innerHTML = 'Finalize & Dispatch';
        btn.disabled = false;
    }
}

function addCardToFeed(data, loc, sev) {
    const feed = document.getElementById('feedContainer');
    const isCritical = parseFloat(sev) >= 8;

    const card = `
        <div class="flex bg-white rounded-3xl overflow-hidden shadow-xl border-2 transition-all hover:scale-[1.01] animate-in slide-in-from-right duration-500 ${isCritical ? 'border-red-500' : 'border-[#C7AF94]'}">
            <div class="w-24 flex items-center justify-center ${isCritical ? 'bg-red-50 text-red-500' : 'bg-slate-50 text-[#8C916C]'}">
                <i class="fas ${isCritical ? 'fa-triangle-exclamation' : 'fa-circle-check'} text-3xl"></i>
            </div>
            <div class="flex-1 p-6 text-left">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="text-xl font-black uppercase tracking-tighter">${loc}</h4>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">${data.district || 'Karnataka'} HQ</span>
                    </div>
                    <div class="text-right">
                        <span class="text-[10px] font-black text-slate-400 uppercase block opacity-40">Severity</span>
                        <span class="text-4xl font-black ${isCritical ? 'text-red-500' : 'text-[#95714F]'}">${sev}</span>
                    </div>
                </div>
                <p class="text-slate-600 mt-3 font-medium italic leading-tight">"${data.summary}"</p>
                <div class="mt-4 pt-4 border-t border-slate-100 flex justify-between">
                    <span class="text-[10px] font-black text-green-700 bg-green-50 px-3 py-1 rounded-full uppercase">
                        <i class="fas fa-shield-halved mr-1"></i> Unit: ${data.recommended_unit}
                    </span>
                </div>
            </div>
        </div>`;
    feed.insertAdjacentHTML('afterbegin', card);
}

setInterval(() => {
    const clock = document.getElementById('clock');
    if (clock) clock.innerText = new Date().toLocaleTimeString([], { hour12: false });
}, 1000);