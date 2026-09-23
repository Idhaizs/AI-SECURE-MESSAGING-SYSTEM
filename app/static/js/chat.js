// ============================================
// Chat Interface JavaScript
// ============================================

const socket = io();
let currentReceiverId = null;
let currentReceiverName = null;
let typingTimer = null;
const currentUserId = parseInt(document.getElementById('currentUserId').value);

// Voice Recorder variables
let mediaRecorder = null;
let audioChunks = [];
let recordingInterval = null;
let recordingSeconds = 0;

// ─── Unread Badge & Notification System ─────────────────────────────
const unreadCounts = {};

if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
}

function playNotificationSound() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.3);
    } catch (e) {
        console.log("Audio notification sound error:", e);
    }
}

function updateNavChatsBadge() {
    const totalUnread = Object.values(unreadCounts).reduce((a, b) => a + (parseInt(b) || 0), 0);
    const navBadge = document.getElementById('navChatsBadge');
    if (navBadge) {
        if (totalUnread > 0) {
            navBadge.textContent = totalUnread > 99 ? '99+' : totalUnread;
            navBadge.style.display = 'inline-flex';
        } else {
            navBadge.style.display = 'none';
        }
    }
}

function showNotificationToast(title, bodyText, targetId, isGroup = false, rawId = null) {
    const container = document.getElementById('toastNotificationContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.style.cssText = `
        background: #1e293b;
        color: #ffffff;
        padding: 12px 16px;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        border-left: 4px solid #38bdf8;
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 13px;
        cursor: pointer;
        pointer-events: auto;
        transition: all 0.3s ease;
    `;

    toast.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; color:#38bdf8;">${title}</span>
            <span style="font-size:11px; opacity:0.6;">Just now</span>
        </div>
        <div style="font-size:12px; color:#cbd5e1; word-break:break-word;">${bodyText}</div>
    `;

    toast.onclick = () => {
        const cleanId = parseInt(String(rawId || targetId).replace('g-', ''));
        const contactEl = document.querySelector(`[data-user-id="${targetId}"]`);
        const username = contactEl?.getAttribute('data-username') || (isGroup ? 'Group Chat' : 'User');
        openChat(cleanId, username, isGroup);
        toast.remove();
    };

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

function updateContactPreview(targetId, previewText, timeStr, isUnread = false, senderName = '', isGroup = false, groupName = '', groupId = null) {
    const formattedTargetId = String(targetId).startsWith('g-') ? targetId : (isGroup ? `g-${targetId}` : String(targetId));
    const selector = `[data-user-id="${formattedTargetId}"]`;
    const contactEl = document.querySelector(selector);
    
    const previewEl = document.getElementById(`preview-${formattedTargetId}`);
    const timeEl = document.getElementById(`time-${formattedTargetId}`);
    const badgeEl = document.getElementById(`unread-badge-${formattedTargetId}`);

    const displayPreview = (isGroup && senderName) ? `~ ${senderName}: ${previewText}` : previewText;

    if (previewEl) previewEl.textContent = displayPreview;
    if (timeEl) {
        const formattedTime = timeStr ? (timeStr.includes(' ') ? timeStr.split(' ')[1].slice(0, 5) : timeStr) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        timeEl.textContent = formattedTime;
        if (isUnread) {
            timeEl.style.color = '#22c55e';
            timeEl.style.fontWeight = '700';
        }
    }

    if (contactEl) {
        const contactsList = document.getElementById('contactsList');
        if (contactsList && contactsList.firstChild !== contactEl) {
            contactsList.insertBefore(contactEl, contactsList.firstChild);
        }
    }

    if (isUnread) {
        unreadCounts[formattedTargetId] = (unreadCounts[formattedTargetId] || 0) + 1;
        if (badgeEl) {
            badgeEl.textContent = unreadCounts[formattedTargetId];
            badgeEl.style.display = 'inline-flex';
        }
        updateNavChatsBadge();
        playNotificationSound();

        const toastTitle = isGroup ? `💬 Group: ${groupName || 'Chat'}` : `💬 ${senderName || 'New Message'}`;
        const toastBody = (isGroup && senderName) ? `<b>~ ${escapeHtml(senderName)}</b>: ${escapeHtml(previewText)}` : escapeHtml(previewText);
        showNotificationToast(toastTitle, toastBody, formattedTargetId, isGroup, groupId || targetId);

        if ("Notification" in window && Notification.permission === "granted") {
            try {
                new Notification(toastTitle, {
                    body: isGroup ? `~ ${senderName}: ${previewText}` : previewText
                });
            } catch(e) {}
        }
    }
}

// ─── Socket Events ────────────────────────────────────────────────
socket.on('connect', () => console.log('Connected to server'));

socket.on('new_message', (msg) => {
    if (String(msg.sender_id) === String(currentUserId)) {
        return;
    }
    const isCurrentChat = (!currentIsGroup && (String(msg.sender_id) === String(currentReceiverId) || String(msg.receiver_id) === String(currentReceiverId)));
    if (isCurrentChat) {
        appendMessage(msg);
        scrollToBottom();
    }
    const previewText = msg.message_type === 'file' ? `📎 ${msg.file_name || 'File'}` : (msg.content || 'New message');
    updateContactPreview(msg.sender_id, previewText, msg.sent_at, !isCurrentChat, msg.sender_name, false);
});

socket.on('new_group_message', (msg) => {
    if (String(msg.sender_id) === String(currentUserId)) {
        return;
    }
    const isCurrentChat = (currentIsGroup && String(msg.group_id) === String(currentReceiverId));
    if (isCurrentChat) {
        appendMessage(msg);
        scrollToBottom();
    }
    const previewText = msg.message_type === 'file' ? `📎 ${msg.file_name || 'File'}` : (msg.content || 'New message');
    const groupName = msg.group_name || document.querySelector(`[data-user-id="g-${msg.group_id}"]`)?.getAttribute('data-username') || `Group ${msg.group_id}`;
    updateContactPreview(`g-${msg.group_id}`, previewText, msg.sent_at, !isCurrentChat, msg.sender_name, true, groupName, msg.group_id);
});

socket.on('user_typing', (data) => {
    if (currentReceiverId) {
        document.getElementById('typingIndicator').style.display = 'flex';
    }
});

socket.on('user_stop_typing', () => {
    document.getElementById('typingIndicator').style.display = 'none';
});

// ─── Open Chat & Mobile Navigation ─────────────────────────────────
let currentIsGroup = false;

function toggleMobileView(showChat) {
    const wrapper = document.querySelector('.chat-wrapper');
    if (!wrapper) return;
    if (showChat) {
        wrapper.classList.add('mobile-chat-open');
    } else {
        wrapper.classList.remove('mobile-chat-open');
    }
}

function closeMobileChat() {
    toggleMobileView(false);
}

function openChat(userId, username, isGroup = false) {
    currentReceiverId = userId;
    currentReceiverName = username;
    currentIsGroup = Boolean(isGroup);

    const formattedTargetId = currentIsGroup ? `g-${userId}` : String(userId);
    unreadCounts[formattedTargetId] = 0;

    const badgeId = currentIsGroup ? `unread-badge-g-${userId}` : `unread-badge-${userId}`;
    const badge = document.getElementById(badgeId);
    if (badge) {
        badge.textContent = '0';
        badge.style.display = 'none';
    }
    updateNavChatsBadge();

    const chatMain = document.getElementById('chatMain');
    const panelCalendar = document.getElementById('panel-calendar');
    if (panelCalendar) panelCalendar.style.display = 'none';
    if (chatMain) chatMain.style.display = 'flex';

    if (currentIsGroup) {
        socket.emit('join_group', { group_id: userId });
    }

    const timeEl = document.getElementById(currentIsGroup ? `time-g-${userId}` : `time-${userId}`);
    if (timeEl) {
        timeEl.style.color = '#64748b';
        timeEl.style.fontWeight = 'normal';
    }

    if (!currentIsGroup) {
        fetch(`/chat/mark-read/${userId}`, { method: 'POST' }).then(() => loadUnreadCounts());
    }

    // Update UI
    document.getElementById('chatEmpty').style.display = 'none';
    document.getElementById('chatActive').style.display = 'flex';
    document.getElementById('chatUsername').textContent = username;
    document.getElementById('chatAvatar').innerHTML = currentIsGroup ? '<i class="fas fa-users" style="font-size:16px"></i>' : username[0].toUpperCase();

    // Highlight active contact
    document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('active'));
    const selector = currentIsGroup ? `[data-user-id="g-${userId}"]` : `[data-user-id="${userId}"]`;
    document.querySelector(selector)?.classList.add('active');

    // Update Favourite Status & Dropdown Text
    updateFavUI();

    // Mobile view switch
    toggleMobileView(true);

    // Load messages
    loadMessages(userId, currentIsGroup);
}

// ─── Load Messages ────────────────────────────────────────────────
async function loadMessages(userId, isGroup = false) {
    const area = document.getElementById('messagesArea');
    area.innerHTML = '<div class="loading-messages"><i class="fas fa-spinner fa-spin"></i> Loading messages...</div>';

    try {
        const url = isGroup ? `/chat/messages/${userId}?is_group=true` : `/chat/messages/${userId}`;
        const res = await fetch(url);
        const data = await res.json();

        if (!res.ok || (data && data.error)) {
            area.innerHTML = `<div class="loading-messages" style="color:#ef4444">Failed to load messages (${(data && data.error) || res.status})</div>`;
            return;
        }

        const messages = Array.isArray(data) ? data : [];
        area.innerHTML = '';

        if (messages.length === 0) {
            area.innerHTML = '<div class="loading-messages" style="color:#94a3b8">No messages yet. Start the conversation!</div>';
            return;
        }

        let lastDate = null;
        messages.forEach(msg => {
            const msgDate = (msg.sent_at || '').split(' ')[0] || 'Today';
            if (msgDate !== lastDate) {
                area.appendChild(createDateSeparator(msgDate));
                lastDate = msgDate;
            }
            area.appendChild(createMessageEl(msg));
        });

        scrollToBottom();
    } catch (err) {
        area.innerHTML = `<div class="loading-messages" style="color:#ef4444">Failed to load messages (${err.message})</div>`;
    }
}

function scrollToBottom() {
    const area = document.getElementById('messagesArea');
    if (area) {
        area.scrollTop = area.scrollHeight;
    }
}

function appendMessage(msg) {
    const area = document.getElementById('messagesArea');
    if (!area) return;

    const emptyPlaceholder = area.querySelector('.loading-messages');
    if (emptyPlaceholder) {
        area.innerHTML = '';
    }

    if (area.children.length === 0) {
        const msgDate = (msg.sent_at || '').split(' ')[0] || 'Today';
        area.appendChild(createDateSeparator(msgDate));
    }

    const msgId = msg.message_id || msg.id;
    if (msgId && document.getElementById(`msg-${msgId}`)) {
        return;
    }

    area.appendChild(createMessageEl(msg));
}

let currentReplyTo = null;

// ─── Create Message Element ───────────────────────────────────────
function createMessageEl(msg) {
    const isSent = msg.sender_id === currentUserId;
    const msgId = msg.message_id || msg.id;
    const div = document.createElement('div');
    div.className = `message-bubble ${isSent ? 'sent' : 'received'}`;
    div.id = `msg-${msgId}`;

    let content = '';

    if (msg.is_deleted) {
        content = `<div class="bubble-content" style="font-style:italic;opacity:0.75;"><i class="fas fa-ban"></i> This message was deleted</div>`;
    } else if (msg.message_type === 'file') {
        const fileId = msg.file_id || msg.message_id || 0;
        const icon = getFileIcon(msg.file_name);
        const scanBadge = msg.scan_result === 'clean' ? '✅ Clean' : msg.scan_result === 'suspicious' ? '⚠️ Suspicious' : '📎';
        const isProtected = msg.is_password_protected == 1;
        const lockBadge = isProtected ? '<span style="background:#fef3c7;color:#d97706;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:700;margin-left:4px;">Protected</span>' : '';
        const downloadOnClick = `onclick="downloadFileSecure(event, ${fileId}, '${escapeHtml(msg.file_name || 'File').replace(/'/g, "\\'")}', ${isProtected}, ${isSent})"`;

        content = `
            <div class="bubble-content" style="padding:0;background:none;">
                <a href="/chat/download/${fileId}?download=1" ${downloadOnClick} class="file-message" style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:12px;text-decoration:none;${isSent ? 'background:#1A2B4C;color:#ffffff;' : 'background:#ffffff;color:#1e293b;border:1px solid #e2e8f0;'}">
                    <i class="${icon}" style="font-size:22px;${isSent ? 'color:#60a5fa;' : 'color:#1A2B4C;'}"></i>
                    <div class="file-info" style="display:flex;flex-direction:column;">
                        <span class="file-name" style="font-size:13px;font-weight:600;${isSent ? 'color:#ffffff;' : 'color:#1e293b;'}">${escapeHtml(msg.file_name || 'File')}${lockBadge}</span>
                        <span class="file-scan" style="font-size:11px;${isSent ? 'color:#cbd5e1;' : 'color:#64748b;'}">${scanBadge}</span>
                    </div>
                    <i class="fas ${isProtected ? 'fa-lock' : 'fa-download'}" style="margin-left:16px;font-size:14px;${isSent ? 'color:#ffffff;' : 'color:#64748b;'}"></i>
                </a>
            </div>`;
    } else if (msg.message_type === 'voice') {
        content = `
            <div class="file-message voice-message">
                <i class="fas fa-microphone"></i>
                <div class="file-info">
                    <span class="file-name">Voice Note</span>
                    <audio controls src="/chat/download/${msg.file_id}" style="height:30px;margin-top:4px;"></audio>
                </div>
            </div>`;
    } else {
        const flaggedClass = msg.is_flagged ? 'flagged' : '';
        const threatTag = msg.is_flagged ? `<span class="threat-tag"><i class="fas fa-exclamation-triangle"></i> ${(msg.threat_type || '').replace(/_/g, ' ')}</span>` : '';
        content = `<div class="bubble-content ${flaggedClass}">${escapeHtml(msg.content)}${threatTag ? '<br>' + threatTag : ''}</div>`;
    }

    const time = msg.sent_at ? msg.sent_at.split(' ')[1].slice(0, 5) : '';

    // Action bar for Reply, Edit, Delete
    let actionsHtml = '';
    if (!msg.is_deleted) {
        const replyTextEscaped = escapeHtml(msg.content || msg.file_name || 'File').replace(/'/g, "\\'");
        const senderNameEscaped = escapeHtml(isSent ? 'You' : msg.sender_name).replace(/'/g, "\\'");
        
        let editBtn = '';
        if (isSent && msg.message_type === 'text') {
            editBtn = `<button class="bubble-action-btn" title="Edit" onclick="editMessagePrompt(${msgId}, '${replyTextEscaped}')"><i class="fas fa-pen"></i></button>`;
        }
        
        let deleteBtn = '';
        if (isSent) {
            deleteBtn = `<button class="bubble-action-btn delete-btn" title="Delete" onclick="deleteMessageConfirm(${msgId})"><i class="fas fa-trash-alt"></i></button>`;
        }

        actionsHtml = `
            <div class="bubble-action-bar">
                <button class="bubble-action-btn" title="Reply" onclick="startReply(${msgId}, '${senderNameEscaped}', '${replyTextEscaped}')"><i class="fas fa-reply"></i></button>
                ${editBtn}
                ${deleteBtn}
            </div>`;
    }

    div.innerHTML = `
        ${actionsHtml}
        ${content}
        <div class="bubble-meta">
            <span>${isSent ? 'You' : msg.sender_name}</span>
            <span>${time}</span>
            ${isSent ? '<i class="fas fa-check" style="font-size:10px;color:#93c5fd"></i>' : ''}
        </div>`;

    return div;
}

function createDateSeparator(date) {
    const div = document.createElement('div');
    div.className = 'date-separator';
    div.textContent = formatDate(date);
    return div;
}

// ─── Send Message ─────────────────────────────────────────────────
async function sendMessage() {
    const input = document.getElementById('messageInput');
    let content = input.value.trim();

    if (!content || !currentReceiverId) return;

    if (currentReplyTo) {
        content = `> [${currentReplyTo.senderName}]: ${currentReplyTo.text}\n${content}`;
        cancelReply();
    }

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('receiver_id', currentReceiverId);
        formData.append('content', content);
        if (currentIsGroup) {
            formData.append('is_group', 'true');
        }

        const res = await fetch('/chat/send', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            input.value = '';
            input.style.height = 'auto';

            const msg = {
                message_id: data.message_id,
                sender_id: currentUserId,
                receiver_id: currentReceiverId,
                content: content,
                message_type: 'text',
                is_flagged: data.is_flagged,
                threat_type: data.threat_type,
                sent_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
                sender_name: document.getElementById('currentUsername').value,
                is_group: currentIsGroup,
                group_id: currentReceiverId,
                group_name: currentReceiverName
            };

            appendMessage(msg);
            scrollToBottom();

            if (data.is_flagged && data.warning) {
                showThreatWarning(data.warning);
            }

            if (currentIsGroup) {
                socket.emit('send_group_message', { group_id: currentReceiverId, message: msg });
                updateContactPreview(`g-${currentReceiverId}`, content, msg.sent_at, false, msg.sender_name, true, currentReceiverName, currentReceiverId);
            } else {
                socket.emit('send_message', { receiver_id: currentReceiverId, message: msg });
                updateContactPreview(currentReceiverId, content, msg.sent_at, false, msg.sender_name, false);
            }
        } else {
            if (data.account_blocked || data.redirect) {
                alert(data.error || '🚫 Your account has been suspended by Admin due to a security violation.');
                window.location.href = data.redirect || '/login';
                return;
            }
            alert('❌ ' + (data.error || 'Failed to send message'));
        }
    } catch (err) {
        console.error('Send error:', err);
    } finally {
        sendBtn.disabled = false;
    }
}

// ─── Reply, Edit, Delete Handlers ─────────────────────────────────
function startReply(msgId, senderName, text) {
    currentReplyTo = { msgId, senderName, text };
    document.getElementById('replySenderName').textContent = senderName;
    document.getElementById('replyText').textContent = text.length > 50 ? text.slice(0, 50) + '...' : text;
    document.getElementById('replyPreviewBanner').style.display = 'flex';
    document.getElementById('messageInput').focus();
}

function cancelReply() {
    currentReplyTo = null;
    document.getElementById('replyPreviewBanner').style.display = 'none';
}

async function editMessagePrompt(msgId, oldContent) {
    const newContent = prompt('Edit your message:', oldContent);
    if (!newContent || newContent.trim() === oldContent) return;

    try {
        const res = await fetch(`/chat/message/${msgId}/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent.trim() })
        });
        const data = await res.json();
        if (data.success) {
            if (currentReceiverId) loadMessages(currentReceiverId);
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to edit message');
    }
}

async function deleteMessageConfirm(msgId) {
    if (!msgId || msgId === 'null' || msgId === 'undefined') {
        alert('Message ID missing. Refreshing chat...');
        if (currentReceiverId) loadMessages(currentReceiverId);
        return;
    }
    if (!confirm('Are you sure you want to delete this message?')) return;

    try {
        const res = await fetch(`/chat/message/${msgId}/delete`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            const el = document.getElementById(`msg-${msgId}`);
            if (el) el.remove();
            if (currentReceiverId) loadMessages(currentReceiverId);
        } else {
            alert('❌ ' + (data.error || 'Failed to delete message'));
        }
    } catch (err) {
        alert('Failed to delete message');
    }
}

// ─── Password Protected Upload & Download Handlers ─────────────────
let selectedFileForUpload = null;

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file || !currentReceiverId) return;

    selectedFileForUpload = file;
    document.getElementById('uploadFileNamePreview').textContent = file.name;
    document.getElementById('uploadFileSizePreview').textContent = (file.size / 1024).toFixed(1) + ' KB';

    document.getElementById('filePasswordToggle').checked = false;
    document.getElementById('filePasswordContainer').style.display = 'none';
    document.getElementById('fileUploadPassword').value = '';

    document.getElementById('fileUploadModal').style.display = 'flex';
}

function toggleFilePasswordInput(chk) {
    document.getElementById('filePasswordContainer').style.display = chk.checked ? 'block' : 'none';
    if (!chk.checked) {
        document.getElementById('fileUploadPassword').value = '';
    }
}

function closeFileUploadModal() {
    document.getElementById('fileUploadModal').style.display = 'none';
    selectedFileForUpload = null;
    document.getElementById('fileInput').value = '';
}

async function confirmUploadFile() {
    if (!selectedFileForUpload || !currentReceiverId) return;

    const btn = document.getElementById('uploadFileConfirmBtn');
    const isProtected = document.getElementById('filePasswordToggle').checked;
    const password = document.getElementById('fileUploadPassword').value.trim();

    if (isProtected && !password) {
        return alert('Please enter a password for the protected attachment.');
    }

    const formData = new FormData();
    formData.append('file', selectedFileForUpload);
    formData.append('receiver_id', currentReceiverId);
    if (currentIsGroup) {
        formData.append('is_group', 'true');
    }
    if (isProtected && password) {
        formData.append('file_password', password);
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';

    try {
        closeFileUploadModal();
        showUploadingIndicator();
        const res = await fetch('/chat/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) {
            const msg = {
                message_id: data.message_id,
                sender_id: currentUserId,
                receiver_id: currentReceiverId,
                content: '',
                message_type: 'file',
                file_name: data.file_name,
                file_id: data.file_id,
                scan_result: data.scan_result,
                is_password_protected: data.is_password_protected,
                sent_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
                sender_name: document.getElementById('currentUsername').value,
                is_group: currentIsGroup,
                group_id: currentReceiverId,
                group_name: currentReceiverName
            };

            appendMessage(msg);
            scrollToBottom();
            if (currentIsGroup) {
                socket.emit('send_group_message', { group_id: currentReceiverId, message: msg });
                updateContactPreview(`g-${currentReceiverId}`, `📎 ${data.file_name}`, msg.sent_at, false, msg.sender_name, true, currentReceiverName, currentReceiverId);
            } else {
                socket.emit('send_message', { receiver_id: currentReceiverId, message: msg });
                updateContactPreview(currentReceiverId, `📎 ${data.file_name}`, msg.sent_at, false, msg.sender_name, false);
            }
        } else {
            if (data.account_blocked || data.redirect) {
                alert(data.error || '🚫 Your account has been suspended by Admin due to a security violation.');
                window.location.href = data.redirect || '/login';
                return;
            }
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('File upload failed');
    } finally {
        hideUploadingIndicator();
        document.getElementById('fileInput').value = '';
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Attachment';
    }
}

function downloadFileSecure(e, fileId, fileName, isProtected, isSent) {
    if (isProtected && !isSent) {
        e.preventDefault();
        document.getElementById('unlockFileId').value = fileId;
        document.getElementById('unlockFileNameText').textContent = fileName;
        document.getElementById('unlockFilePasswordInput').value = '';
        document.getElementById('unlockFileError').style.display = 'none';
        document.getElementById('fileUnlockModal').style.display = 'flex';
        document.getElementById('unlockFilePasswordInput').focus();
    }
}

function closeFileUnlockModal() {
    document.getElementById('fileUnlockModal').style.display = 'none';
}

async function submitUnlockFile() {
    const fileId = document.getElementById('unlockFileId').value;
    const password = document.getElementById('unlockFilePasswordInput').value.trim();
    const btn = document.getElementById('unlockFileSubmitBtn');
    const errEl = document.getElementById('unlockFileError');

    if (!password) {
        errEl.textContent = '❌ Please enter the file password';
        errEl.style.display = 'block';
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Unlocking...';
    errEl.style.display = 'none';

    try {
        const downloadUrl = `/chat/download/${fileId}?download=1&password=${encodeURIComponent(password)}`;
        const res = await fetch(downloadUrl);

        if (res.status === 401 || res.status === 403) {
            const data = await res.json();
            errEl.textContent = '❌ ' + (data.error || 'Incorrect password');
            errEl.style.display = 'block';
        } else if (res.ok) {
            closeFileUnlockModal();
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const contentDisposition = res.headers.get('content-disposition');
            let filename = 'downloaded_file';
            if (contentDisposition && contentDisposition.includes('filename=')) {
                filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } else {
            errEl.textContent = '❌ Download failed';
            errEl.style.display = 'block';
        }
    } catch (err) {
        errEl.textContent = '❌ Connection error';
        errEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-key"></i> Unlock & Download';
    }
}

// ─── Emoji Picker ─────────────────────────────────────────────────
function toggleEmojiPicker() {
    const picker = document.getElementById('emojiPicker');
    picker.style.display = picker.style.display === 'none' ? 'flex' : 'none';
}

function addEmoji(emoji) {
    const input = document.getElementById('messageInput');
    input.value += emoji;
    document.getElementById('emojiPicker').style.display = 'none';
    input.focus();
}

// ─── In-Chat Search & Options Menu ────────────────────────────────
function toggleInChatSearch() {
    const bar = document.getElementById('inChatSearchBar');
    const input = document.getElementById('inChatSearchInput');
    const isHidden = bar.style.display === 'none';
    
    bar.style.display = isHidden ? 'flex' : 'none';
    if (isHidden) {
        input.focus();
    } else {
        input.value = '';
        filterInChatMessages();
    }
}

function filterInChatMessages() {
    const q = document.getElementById('inChatSearchInput').value.toLowerCase();
    const bubbles = document.querySelectorAll('#messagesArea .message-bubble');

    bubbles.forEach(b => {
        const text = b.textContent.toLowerCase();
        if (!q || text.includes(q)) {
            b.style.display = 'flex';
        } else {
            b.style.display = 'none';
        }
    });
}

function toggleMoreOptionsMenu() {
    const menu = document.getElementById('moreOptionsMenu');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('moreOptionsMenu');
    const btn = e.target.closest('[title="More options"]');
    if (menu && menu.style.display === 'block' && !menu.contains(e.target) && !btn) {
        menu.style.display = 'none';
    }
});

// ─── Favourites & Filter Pills ────────────────────────────────────
let activeFilter = 'all';

function getFavourites() {
    try {
        const stored = localStorage.getItem(`fav_users_${currentUserId}`);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        return [];
    }
}

function saveFavourites(favs) {
    try {
        localStorage.setItem(`fav_users_${currentUserId}`, JSON.stringify(favs));
    } catch (e) {}
}

function getFavKey() {
    if (!currentReceiverId) return null;
    return currentIsGroup ? `g-${currentReceiverId}` : String(currentReceiverId);
}

function isCurrentFav() {
    const key = getFavKey();
    if (!key) return false;
    const favs = getFavourites().map(String);
    return favs.includes(key) || favs.includes(String(currentReceiverId));
}

function updateFavUI() {
    const isFav = isCurrentFav();
    const item = document.getElementById('favMenuItem');
    if (item) {
        if (isFav) {
            item.innerHTML = '<i class="fas fa-star" style="color:#eab308"></i> Unfavourite Chat';
        } else {
            item.innerHTML = '<i class="far fa-star"></i> Favourite Chat';
        }
    }
    
    const infoItem = document.getElementById('infoMenuItem');
    if (infoItem) {
        if (currentIsGroup) {
            infoItem.innerHTML = '<i class="fas fa-users-cog"></i> Group Settings & Members';
        } else {
            infoItem.innerHTML = '<i class="fas fa-info-circle"></i> Contact Info';
        }
    }
    
    // Update star badges on sidebar contacts (placed neatly on the far right inside .contact-meta)
    const favs = getFavourites().map(String);
    document.querySelectorAll('.contact-item').forEach(el => {
        const uid = String(el.dataset.userId);
        let starBadge = el.querySelector('.fav-star-badge');
        const isUserFav = favs.includes(uid) || (uid.startsWith('g-') && favs.includes(uid.replace('g-', '')));
        
        if (isUserFav) {
            if (!starBadge) {
                starBadge = document.createElement('i');
                starBadge.className = 'fas fa-star fav-star-badge';
                starBadge.style.color = '#eab308';
                starBadge.style.fontSize = '13px';
                starBadge.style.marginTop = '4px';
                starBadge.style.display = 'block';
                starBadge.title = 'Favourite';
                const meta = el.querySelector('.contact-meta') || el;
                meta.appendChild(starBadge);
            }
        } else {
            if (starBadge) starBadge.remove();
        }
    });
}

function toggleFavoriteChat() {
    if (!currentReceiverId) return;
    const key = getFavKey();
    let favs = getFavourites().map(String);
    
    if (favs.includes(key) || favs.includes(String(currentReceiverId))) {
        favs = favs.filter(id => id !== key && id !== String(currentReceiverId));
        saveFavourites(favs);
        alert(`Unfavourited ${currentReceiverName}`);
    } else {
        favs.push(key);
        saveFavourites(favs);
        alert(`⭐ ${currentReceiverName} added to Favourites!`);
    }
    
    document.getElementById('moreOptionsMenu').style.display = 'none';
    updateFavUI();
    filterUsers();
}

function showContactInfo() {
    if (!currentReceiverId) return;
    document.getElementById('moreOptionsMenu').style.display = 'none';
    
    if (currentIsGroup) {
        openGroupInfoModal();
    } else {
        alert(`👤 Contact Info:\nUsername: ${currentReceiverName}\nStatus: Active Encrypted Session`);
    }
}

let currentGroupIdForModal = null;

function closeGroupInfoModal() {
    document.getElementById('groupInfoModal').style.display = 'none';
}

async function openGroupInfoModal() {
    if (!currentReceiverId || !currentIsGroup) return;
    currentGroupIdForModal = currentReceiverId;
    
    const modal = document.getElementById('groupInfoModal');
    const body = document.getElementById('groupInfoModalBody');
    
    modal.style.display = 'flex';
    body.innerHTML = '<div style="text-align:center;padding:24px;color:#94a3b8"><i class="fas fa-spinner fa-spin"></i> Loading group details...</div>';
    
    try {
        const res = await fetch(`/chat/groups/${currentReceiverId}/details`);
        const data = await res.json();
        
        if (!data.success) {
            body.innerHTML = `<div style="color:#ef4444;padding:20px;text-align:center;">❌ ${data.error}</div>`;
            return;
        }
        
        const g = data.group;
        const isAdmin = data.is_admin;
        
        let membersHtml = data.members.map(m => `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:32px;height:32px;border-radius:50%;background:#1A2B4C;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;">${m.username[0].toUpperCase()}</div>
                    <div>
                        <strong style="font-size:14px;color:#1e293b">${escapeHtml(m.username)}</strong>
                        ${m.role === 'admin' ? '<span style="background:#fef3c7;color:#d97706;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;margin-left:6px;">👑 Admin</span>' : ''}
                    </div>
                </div>
                ${(isAdmin && m.user_id !== currentUserId) ? `<button onclick="removeGroupMember(${m.user_id})" class="btn btn-sm" style="color:#ef4444;border-color:#fca5a5;padding:4px 10px;font-size:11px;"><i class="fas fa-user-minus"></i> Remove</button>` : ''}
            </div>
        `).join('');
        
        let availableOptionsHtml = data.available_users.map(u => `<option value="${u.user_id}">${escapeHtml(u.username)}</option>`).join('');
        
        body.innerHTML = `
            <form onsubmit="saveGroupInfo(event)">
                <div class="form-group">
                    <label>Group Name ${isAdmin ? '' : '(Read Only)'}</label>
                    <input type="text" id="editGroupName" value="${escapeHtml(g.name)}" ${isAdmin ? '' : 'disabled'} required>
                </div>
                <div class="form-group">
                    <label>Group Description</label>
                    <textarea id="editGroupDesc" rows="2" style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:14px;outline:none;" placeholder="Add group description..." ${isAdmin ? '' : 'disabled'}>${escapeHtml(g.description || '')}</textarea>
                </div>
                ${isAdmin ? `
                <div style="display:flex;justify-content:flex-end;margin-bottom:20px;">
                    <button type="submit" class="btn btn-primary btn-sm" id="saveGroupBtn"><i class="fas fa-save"></i> Save Changes</button>
                </div>
                ` : ''}
            </form>
            
            <hr style="border:0;border-top:1px solid #e2e8f0;margin:20px 0;">
            
            <div style="margin-bottom:16px;">
                <h4 style="font-size:14px;color:#1e293b;margin-bottom:12px;"><i class="fas fa-users"></i> Group Members (${data.members.length})</h4>
                <div style="max-height:180px;overflow-y:auto;">
                    ${membersHtml}
                </div>
            </div>
            
            ${(isAdmin && data.available_users.length > 0) ? `
            <div style="background:#f1f5f9;padding:14px;border-radius:10px;margin-bottom:16px;">
                <label style="font-size:13px;font-weight:600;color:#334155;display:block;margin-bottom:8px;"><i class="fas fa-user-plus"></i> Add New Member (Admin)</label>
                <div style="display:flex;gap:8px;">
                    <select id="addMemberSelect" style="flex:1;padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px;outline:none;">
                        <option value="">Select registered user to add...</option>
                        ${availableOptionsHtml}
                    </select>
                    <button onclick="addGroupMember()" class="btn btn-primary btn-sm"><i class="fas fa-plus"></i> Add</button>
                </div>
            </div>
            ` : ''}
            
            <div style="display:flex;justify-content:space-between;margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0;">
                <button onclick="leaveGroup()" class="btn btn-sm" style="color:#d97706;border-color:#fde68a;"><i class="fas fa-sign-out-alt"></i> Leave Group</button>
                ${isAdmin ? `<button onclick="deleteGroup()" class="btn btn-sm" style="color:#ef4444;border-color:#fca5a5;"><i class="fas fa-trash-alt"></i> Delete Group</button>` : ''}
            </div>
        `;
    } catch (e) {
        body.innerHTML = `<div style="color:#ef4444;padding:20px;text-align:center;">Failed to load group details.</div>`;
    }
}

async function saveGroupInfo(e) {
    e.preventDefault();
    if (!currentGroupIdForModal) return;
    
    const name = document.getElementById('editGroupName').value.trim();
    const description = document.getElementById('editGroupDesc').value.trim();
    const btn = document.getElementById('saveGroupBtn');
    
    if (!name) return alert('Group name cannot be empty');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    
    try {
        const res = await fetch(`/chat/groups/${currentGroupIdForModal}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('Group details updated successfully!');
            location.reload();
        } else {
            alert('❌ ' + data.error);
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
        }
    } catch (err) {
        alert('Failed to update group');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
    }
}

async function addGroupMember() {
    const select = document.getElementById('addMemberSelect');
    const targetUserId = select.value;
    if (!targetUserId || !currentGroupIdForModal) return alert('Please select a user to add.');
    
    try {
        const res = await fetch(`/chat/groups/${currentGroupIdForModal}/members/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: targetUserId })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('Member added to group successfully!');
            openGroupInfoModal();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to add member');
    }
}

async function removeGroupMember(targetUserId) {
    if (!currentGroupIdForModal) return;
    if (!confirm('Are you sure you want to remove this member from the group?')) return;
    
    try {
        const res = await fetch(`/chat/groups/${currentGroupIdForModal}/members/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: targetUserId })
        });
        const data = await res.json();
        
        if (data.success) {
            alert('Member removed successfully!');
            openGroupInfoModal();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to remove member');
    }
}

async function leaveGroup() {
    if (!currentGroupIdForModal) return;
    if (!confirm('Are you sure you want to leave this group?')) return;
    
    try {
        const res = await fetch(`/chat/groups/${currentGroupIdForModal}/leave`, { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            alert('You left the group.');
            location.reload();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to leave group');
    }
}

async function deleteGroup() {
    if (!currentGroupIdForModal) return;
    if (!confirm('⚠️ Are you sure you want to delete this group permanently? All member connections will be removed.')) return;
    
    try {
        const res = await fetch(`/chat/groups/${currentGroupIdForModal}/delete`, { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            alert('Group deleted successfully.');
            location.reload();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to delete group');
    }
}

function clearChatHistory() {
    if (!currentReceiverId) return;
    if (confirm(`Are you sure you want to clear chat history with ${currentReceiverName}?`)) {
        const area = document.getElementById('messagesArea');
        area.innerHTML = '<div class="loading-messages" style="color:#94a3b8">Chat history cleared</div>';
        document.getElementById('moreOptionsMenu').style.display = 'none';
    }
}

function deleteCurrentConversation() {
    if (!currentReceiverId) return;
    if (confirm(`Delete conversation with ${currentReceiverName}?`)) {
        document.getElementById('chatActive').style.display = 'none';
        document.getElementById('chatEmpty').style.display = 'flex';
        document.getElementById('moreOptionsMenu').style.display = 'none';
        currentReceiverId = null;
    }
}

// ─── Filter Pills ─────────────────────────────────────────────────
// ─── Master Sidebar Navigation & Settings ──────────────────────────
function switchNav(type, sidebarBtn) {
    activeFilter = type;

    // Highlight sidebar icon
    document.querySelectorAll('.sidebar-icon').forEach(btn => btn.classList.remove('active'));
    if (sidebarBtn) {
        sidebarBtn.classList.add('active');
    } else {
        if (type === 'all') document.getElementById('navChatsBtn')?.classList.add('active');
        if (type === 'group') document.getElementById('navGroupsBtn')?.classList.add('active');
        if (type === 'favourite') document.getElementById('navStarredBtn')?.classList.add('active');
        if (type === 'calendar') document.getElementById('navCalendarBtn')?.classList.add('active');
    }

    const chatMain = document.getElementById('chatMain');
    const panelCalendar = document.getElementById('panel-calendar');

    if (type === 'calendar') {
        if (chatMain) chatMain.style.display = 'none';
        if (panelCalendar) {
            panelCalendar.style.display = 'flex';
            loadCalendarMeetings();
            const navCalBadge = document.getElementById('navCalendarBadge');
            if (navCalBadge) navCalBadge.style.display = 'none';
        }
    } else {
        if (panelCalendar) panelCalendar.style.display = 'none';
        if (chatMain) chatMain.style.display = 'flex';

        // Highlight filter pill
        document.querySelectorAll('.filter-pill').forEach(pill => {
            pill.classList.remove('active');
            const pillOnClick = pill.getAttribute('onclick') || '';
            if (pillOnClick.includes(`'${type}'`)) {
                pill.classList.add('active');
            }
        });

        filterUsers();
    }
}

function openUserSettingsModal() {
    document.querySelectorAll('.sidebar-icon').forEach(btn => btn.classList.remove('active'));
    document.getElementById('navSettingsBtn')?.classList.add('active');
    document.getElementById('userSettingsModal').style.display = 'flex';
}

function closeUserSettingsModal() {
    document.getElementById('userSettingsModal').style.display = 'none';
    switchNav(activeFilter || 'all');
}

async function submitUpdateUsername(e) {
    e.preventDefault();
    const newUsername = document.getElementById('editUsernameInput').value.trim();
    const btn = document.getElementById('updateUsernameBtn');

    if (!newUsername) return alert('Username cannot be empty');
    if (newUsername.length < 3) return alert('Username must be at least 3 characters');

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const res = await fetch('/chat/settings/update-username', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: newUsername })
        });
        const data = await res.json();

        if (data.success) {
            alert('👤 Username updated successfully!');
            document.getElementById('currentUsername').value = data.username;
            location.reload();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to update username');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Username';
    }
}

async function submitChangePassword(e) {
    e.preventDefault();
    const oldPassword = document.getElementById('oldPasswordInput').value;
    const newPassword = document.getElementById('newPasswordInput').value;
    const btn = document.getElementById('changePasswordBtn');

    if (!oldPassword || !newPassword) return alert('Please fill in all password fields.');
    if (newPassword.length < 6) return alert('New password must be at least 6 characters.');

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';

    try {
        const res = await fetch('/chat/settings/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
        });
        const data = await res.json();

        if (data.success) {
            alert('🔒 Password changed successfully!');
            document.getElementById('oldPasswordInput').value = '';
            document.getElementById('newPasswordInput').value = '';
            closeUserSettingsModal();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to change password');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-lock"></i> Update Password';
    }
}

async function submitUpdateSecurityQuestion(e) {
    e.preventDefault();
    const question = document.getElementById('secQuestionSelect').value;
    const answer = document.getElementById('secAnswerInput').value.trim();
    const btn = document.getElementById('updateSecQuestionBtn');

    if (!question || !answer) return alert('Please enter both secret question and answer.');

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const res = await fetch('/chat/settings/update-security-question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, answer })
        });
        const data = await res.json();

        if (data.success) {
            alert('🔒 Secret Recovery Question updated successfully!');
            document.getElementById('secAnswerInput').value = '';
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to update security question');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Question';
    }
}

function setFilter(type, btn) {
    switchNav(type);
}

// ─── Group Modal (Registered Users Only) ──────────────────────────
function openGroupModal() {
    document.getElementById('groupModal').style.display = 'flex';
}

function closeGroupModal() {
    document.getElementById('groupModal').style.display = 'none';
}

async function submitCreateGroup() {
    const groupName = document.getElementById('groupNameInput').value.strip ? document.getElementById('groupNameInput').value.strip() : document.getElementById('groupNameInput').value.trim();
    const checked = Array.from(document.querySelectorAll('.group-member-checkbox:checked')).map(cb => cb.value);

    if (!groupName || checked.length === 0) {
        return alert('Please enter a group name and select at least 1 registered member.');
    }

    try {
        const res = await fetch('/chat/groups/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_name: groupName, member_ids: checked })
        });
        const data = await res.json();

        if (data.success) {
            alert(`Group "${data.group_name}" created successfully!`);
            closeGroupModal();
            location.reload();
        } else {
            alert('❌ ' + data.error);
        }
    } catch (err) {
        alert('Failed to create group');
    }
}

// ─── Helpers ──────────────────────────────────────────────────────
function appendMessage(msg) {
    const area = document.getElementById('messagesArea');
    const loadingEl = area.querySelector('.loading-messages');
    if (loadingEl) loadingEl.remove();
    area.appendChild(createMessageEl(msg));
}

function scrollToBottom() {
    const area = document.getElementById('messagesArea');
    area.scrollTop = area.scrollHeight;
}

function handleEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleTyping() {
    if (!currentReceiverId) return;
    socket.emit('typing', { receiver_id: currentReceiverId });
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => socket.emit('stop_typing', { receiver_id: currentReceiverId }), 1500);
}

function filterUsers() {
    const q = document.getElementById('searchUser').value.toLowerCase();
    const favs = getFavourites().map(String);

    document.querySelectorAll('.contact-item').forEach(el => {
        const username = (el.dataset.username || '').toLowerCase();
        const userId = String(el.dataset.userId);
        const isFav = favs.includes(userId) || (userId.startsWith('g-') && favs.includes(userId.replace('g-', ''))) || favs.includes('g-' + userId);
        const isGroup = el.dataset.isGroup === 'true' || el.classList.contains('group-item');

        const matchesQuery = !q || username.includes(q);
        let matchesFilter = true;

        if (activeFilter === 'favourite') {
            matchesFilter = isFav;
        } else if (activeFilter === 'group') {
            matchesFilter = isGroup;
        }

        if (matchesQuery && matchesFilter) {
            el.style.display = 'flex';
        } else {
            el.style.display = 'none';
        }
    });
}

function showPanel(panel) {
    document.querySelectorAll('.sidebar-icon').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
}

function showThreatWarning(text) {
    document.getElementById('threatWarningText').textContent = text;
    document.getElementById('threatWarning').style.display = 'flex';
}

function dismissWarning() {
    document.getElementById('threatWarning').style.display = 'none';
}

function showUploadingIndicator() {
    const btn = document.querySelector('.attach-btn');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
}

function hideUploadingIndicator() {
    const btn = document.querySelector('.attach-btn');
    if (btn) {
        btn.innerHTML = '<i class="fas fa-plus"></i><input type="file" id="fileInput" style="display:none;" onchange="handleFileSelect(event)">';
    }
}

function updateContactPreview(userId, text, time, showUnread = false) {
    const preview = document.getElementById(`preview-${userId}`);
    const timeEl = document.getElementById(`time-${userId}`);
    if (preview) preview.textContent = text.length > 30 ? text.slice(0, 30) + '...' : text;
    if (timeEl) timeEl.textContent = time ? time.split(' ')[1]?.slice(0, 5) : '';

    if (showUnread) {
        loadUnreadCounts();
    }
}

// ─── Calendar & Meetings JS Module ─────────────────────────────────
let activeCalendarView = 'month';
let allMeetingsList = [];

let currentCalYear = new Date().getFullYear();
let currentCalMonth = new Date().getMonth(); // 0-indexed (0=Jan, 7=Aug)
let calendarDisplayMode = 'grid'; // 'grid' or 'list'

const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
];

function switchCalendarDisplayMode(mode) {
    calendarDisplayMode = mode;
    const gridContainer = document.getElementById('calendarVisualGridContainer');
    const listContainer = document.getElementById('calendarListViewContainer');
    const gridBtn = document.getElementById('calModeGridBtn');
    const listBtn = document.getElementById('calModeListBtn');

    if (mode === 'grid') {
        if (gridContainer) gridContainer.style.display = 'block';
        if (listContainer) listContainer.style.display = 'none';
        if (gridBtn) {
            gridBtn.classList.add('active');
            gridBtn.style.background = '#1a2b4c';
            gridBtn.style.color = 'white';
        }
        if (listBtn) {
            listBtn.classList.remove('active');
            listBtn.style.background = 'transparent';
            listBtn.style.color = '#64748b';
        }
        renderVisualCalendarGrid();
    } else {
        if (gridContainer) gridContainer.style.display = 'none';
        if (listContainer) listContainer.style.display = 'flex';
        if (listBtn) {
            listBtn.classList.add('active');
            listBtn.style.background = '#1a2b4c';
            listBtn.style.color = 'white';
        }
        if (gridBtn) {
            gridBtn.classList.remove('active');
            gridBtn.style.background = 'transparent';
            gridBtn.style.color = '#64748b';
        }
        renderCalendarMeetings();
    }
}

function prevMonth() {
    currentCalMonth--;
    if (currentCalMonth < 0) {
        currentCalMonth = 11;
        currentCalYear--;
    }
    renderVisualCalendarGrid();
}

function nextMonth() {
    currentCalMonth++;
    if (currentCalMonth > 11) {
        currentCalMonth = 0;
        currentCalYear++;
    }
    renderVisualCalendarGrid();
}

function goToToday() {
    const now = new Date();
    currentCalYear = now.getFullYear();
    currentCalMonth = now.getMonth();
    renderVisualCalendarGrid();
}

function renderVisualCalendarGrid() {
    const matrixEl = document.getElementById('calendarGridMatrix');
    const labelEl = document.getElementById('currentMonthYearLabel');
    if (!matrixEl) return;

    if (labelEl) {
        labelEl.textContent = `${monthNames[currentCalMonth]} ${currentCalYear}`;
    }

    const todayStr = new Date().toISOString().split('T')[0];

    const firstDayIndex = new Date(currentCalYear, currentCalMonth, 1).getDay(); // 0=Sun, 6=Sat
    const daysInMonth = new Date(currentCalYear, currentCalMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(currentCalYear, currentCalMonth, 0).getDate();

    let gridHtml = '';

    // 1. Previous month trailing days
    for (let i = firstDayIndex - 1; i >= 0; i--) {
        const pDay = daysInPrevMonth - i;
        const pMonth = currentCalMonth === 0 ? 11 : currentCalMonth - 1;
        const pYear = currentCalMonth === 0 ? currentCalYear - 1 : currentCalYear;
        const dateStr = `${pYear}-${String(pMonth + 1).padStart(2, '0')}-${String(pDay).padStart(2, '0')}`;

        gridHtml += `
            <div class="cal-cell other-month" onclick="openCreateMeetingModal('${dateStr}')">
                <span class="cal-cell-number">${pDay}</span>
            </div>`;
    }

    // 2. Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${currentCalYear}-${String(currentCalMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = dateStr === todayStr;

        // Find meetings on this date
        const dayMeetings = allMeetingsList.filter(m => m.start_time && m.start_time.startsWith(dateStr));

        let eventsHtml = '';
        dayMeetings.forEach(m => {
            const timeStr = m.start_time ? m.start_time.split(' ')[1] : '';
            eventsHtml += `
                <div class="cal-event-pill ${m.meeting_type}" onclick="event.stopPropagation(); viewMeetingDetails(${m.meeting_id})" title="${escapeHtml(m.title)} (${m.start_time})">
                    ${timeStr} ${escapeHtml(m.title)}
                </div>`;
        });

        gridHtml += `
            <div class="cal-cell ${isToday ? 'today' : ''}" onclick="openCreateMeetingModal('${dateStr}')" title="Click to schedule meeting on ${dateStr}">
                <span class="cal-cell-number">${day}</span>
                ${eventsHtml}
            </div>`;
    }

    // 3. Next month leading days (fill up 42 total grid cells)
    const totalRendered = firstDayIndex + daysInMonth;
    const remainingCells = (totalRendered > 35 ? 42 : 35) - totalRendered;
    for (let nDay = 1; nDay <= remainingCells; nDay++) {
        const nMonth = currentCalMonth === 11 ? 0 : currentCalMonth + 1;
        const nYear = currentCalMonth === 11 ? currentCalYear + 1 : currentCalYear;
        const dateStr = `${nYear}-${String(nMonth + 1).padStart(2, '0')}-${String(nDay).padStart(2, '0')}`;

        gridHtml += `
            <div class="cal-cell other-month" onclick="openCreateMeetingModal('${dateStr}')">
                <span class="cal-cell-number">${nDay}</span>
            </div>`;
    }

    matrixEl.innerHTML = gridHtml;
}

async function loadCalendarMeetings() {
    const listEl = document.getElementById('calendarMeetingsList');
    if (listEl) {
        listEl.innerHTML = '<div style="text-align:center; color:#94a3b8; padding:40px;"><i class="fas fa-spinner fa-spin"></i> Loading meetings...</div>';
    }

    try {
        const res = await fetch('/chat/meetings');
        const data = await res.json();

        if (data.success) {
            allMeetingsList = data.meetings || [];
            renderVisualCalendarGrid();
            renderCalendarMeetings();
        } else {
            if (listEl) listEl.innerHTML = `<div style="text-align:center; color:#ef4444; padding:40px;">Failed to load meetings: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (err) {
        if (listEl) listEl.innerHTML = '<div style="text-align:center; color:#ef4444; padding:40px;">Connection error loading meetings.</div>';
    }
}

function filterCalendarView(mode) {
    activeCalendarView = mode;
    document.querySelectorAll('.cal-view-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.background = 'transparent';
        btn.style.color = '#64748b';
    });
    const activeBtn = document.getElementById(`calView${mode.charAt(0).toUpperCase() + mode.slice(1)}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.background = '#1a2b4c';
        activeBtn.style.color = 'white';
    }
    renderCalendarMeetings();
}

function renderCalendarMeetings() {
    const listEl = document.getElementById('calendarMeetingsList');
    if (!listEl) return;

    const viewLabel = activeCalendarView === 'day' ? "Today's Schedule (Day View)"
        : activeCalendarView === 'week' ? "This Week's Schedule (Week View)"
        : "All Scheduled Meetings (Month View)";

    if (allMeetingsList.length === 0) {
        listEl.innerHTML = `
            <div style="background:white; border-radius:16px; border:1px solid #e2e8f0; padding:40px 24px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="width:64px; height:64px; border-radius:50%; background:#f1f5f9; color:#1a2b4c; display:inline-flex; align-items:center; justify-content:center; font-size:24px; margin-bottom:14px;">
                    <i class="fas fa-calendar-plus"></i>
                </div>
                <h4 style="margin:0 0 6px 0; font-size:17px; font-weight:700; color:#1a2b4c;">${viewLabel}</h4>
                <p style="margin:0 0 18px 0; font-size:13px; color:#64748b;">No meetings scheduled for this timeframe yet.</p>
                <button onclick="openCreateMeetingModal()" style="background:#1a2b4c; color:white; border:none; padding:10px 20px; border-radius:10px; font-weight:600; font-size:13px; cursor:pointer; display:inline-flex; align-items:center; gap:8px;">
                    <i class="fas fa-plus"></i> Schedule New Meeting
                </button>
            </div>`;
        return;
    }

    const now = new Date();
    const filtered = allMeetingsList.filter(m => {
        if (!m.start_time) return true;
        const mDate = new Date(m.start_time.replace(' ', 'T'));
        if (activeCalendarView === 'day') {
            return mDate.toDateString() === now.toDateString();
        } else if (activeCalendarView === 'week') {
            const diffDays = Math.abs((mDate - now) / (1000 * 60 * 60 * 24));
            return diffDays <= 7;
        }
        return true;
    });

    if (filtered.length === 0) {
        listEl.innerHTML = `
            <div style="text-align:center; padding:40px 20px; background:white; border-radius:16px; border:1px solid #e2e8f0;">
                <i class="fas fa-calendar-minus" style="font-size:36px; color:#cbd5e1; margin-bottom:10px;"></i>
                <h4 style="margin:0 0 4px 0; font-size:15px; color:#334155;">No meetings for this ${activeCalendarView} view</h4>
                <p style="margin:0; font-size:12px; color:#94a3b8;">Try switching to Month view to see all events.</p>
            </div>`;
        return;
    }

    let html = '';
    filtered.forEach(m => {
        const typeBadge = m.meeting_type === 'google_meet' ? '<span style="background:#ea4335; color:white; font-size:11px; padding:3px 8px; border-radius:12px; font-weight:600;"><i class="fas fa-video"></i> Google Meet</span>'
            : m.meeting_type === 'teams' ? '<span style="background:#464eb8; color:white; font-size:11px; padding:3px 8px; border-radius:12px; font-weight:600;"><i class="fas fa-users-rectangle"></i> MS Teams</span>'
            : '<span style="background:#059669; color:white; font-size:11px; padding:3px 8px; border-radius:12px; font-weight:600;"><i class="fas fa-map-marker-alt"></i> Physical</span>';

        const isLink = m.location_or_link && m.location_or_link.startsWith('http');
        const locationLinkHtml = isLink 
            ? `<a href="${m.location_or_link}" target="_blank" style="color:#2563eb; text-decoration:none; font-weight:600; display:inline-flex; align-items:center; gap:4px;"><i class="fas fa-external-link-alt"></i> Join Meeting (${m.location_or_link})</a>`
            : `<span style="color:#475569;"><i class="fas fa-location-arrow"></i> ${escapeHtml(m.location_or_link || 'Location')}</span>`;

        const infoBtnHtml = `<button onclick="viewMeetingDetails(${m.meeting_id})" style="background:#eff6ff; border:1px solid #bfdbfe; color:#2563eb; cursor:pointer; font-size:12px; padding:6px 12px; border-radius:8px; display:inline-flex; align-items:center; gap:5px; font-weight:600; transition:all 0.15s;" title="View Details"><i class="fas fa-info-circle"></i> Info</button>`;
        const editBtnHtml = m.is_organizer ? `<button onclick="openEditMeetingModal(${m.meeting_id})" style="background:#fffbeb; border:1px solid #fef3c7; color:#d97706; cursor:pointer; font-size:12px; padding:6px 12px; border-radius:8px; display:inline-flex; align-items:center; gap:5px; font-weight:600; transition:all 0.15s;" title="Edit Meeting"><i class="fas fa-edit"></i> Edit</button>` : '';
        const deleteBtnHtml = m.is_organizer ? `<button onclick="confirmDeleteMeeting(${m.meeting_id}, '${escapeHtml(m.title).replace(/'/g, "\\'")}')" style="background:#fef2f2; border:1px solid #fecaca; color:#ef4444; cursor:pointer; font-size:12px; padding:6px 12px; border-radius:8px; display:inline-flex; align-items:center; gap:5px; font-weight:600; transition:all 0.15s;" title="Cancel Meeting"><i class="fas fa-trash-alt"></i> Delete</button>` : '';

        html += `
            <div style="background:white; border-radius:14px; border:1px solid #e2e8f0; padding:18px 22px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                <div style="display:flex; align-items:flex-start; gap:16px;">
                    <div style="background:#f1f5f9; border-radius:12px; padding:12px 16px; text-align:center; min-width:65px;">
                        <span style="display:block; font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase;">${m.start_time ? m.start_time.split(' ')[0] : ''}</span>
                        <span style="display:block; font-size:15px; font-weight:800; color:#1a2b4c; margin-top:2px;">${m.start_time ? m.start_time.split(' ')[1] : ''}</span>
                    </div>
                    <div>
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                            <h4 style="margin:0; font-size:16px; font-weight:700; color:#1a2b4c;">${escapeHtml(m.title)}</h4>
                            ${typeBadge}
                        </div>
                        <p style="margin:0 0 6px 0; font-size:13px; color:#64748b;">
                            <i class="fas fa-clock" style="margin-right:4px;"></i> ${m.start_time} - ${m.end_time} | 
                            <i class="fas fa-user-tie" style="margin-left:6px; margin-right:4px;"></i> Organizer: <strong>${escapeHtml(m.organizer_name)}</strong>
                        </p>
                        <div style="font-size:13px;">${locationLinkHtml}</div>
                        ${m.description ? `<p style="margin:6px 0 0 0; font-size:12px; color:#475569; background:#f8fafc; padding:6px 10px; border-radius:6px;">${escapeHtml(m.description)}</p>` : ''}
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    ${infoBtnHtml}
                    ${editBtnHtml}
                    ${deleteBtnHtml}
                </div>
            </div>`;
    });

    listEl.innerHTML = html;
}

function openCreateMeetingModal() {
    const modal = document.getElementById('createMeetingModal');
    if (!modal) return;

    const now = new Date();
    const startIso = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    const endIso = new Date(now.getTime() + 3600000 - (now.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);

    document.getElementById('meetingTitleInput').value = '';
    document.getElementById('meetingPlatformSelect').value = 'google_meet';
    togglePlatformLocation('google_meet');
    document.getElementById('meetingStartTimeInput').value = startIso;
    document.getElementById('meetingEndTimeInput').value = endIso;
    document.getElementById('meetingDescriptionInput').value = '';
    
    document.querySelectorAll('.meeting-participant-checkbox').forEach(cb => cb.checked = true);

    modal.style.display = 'flex';
}

function closeCreateMeetingModal() {
    const modal = document.getElementById('createMeetingModal');
    if (modal) modal.style.display = 'none';
}

function togglePlatformLocation(type) {
    const container = document.getElementById('customLocationContainer');
    const label = document.getElementById('customLocationLabel');
    const input = document.getElementById('meetingLocationInput');
    const extBtn = document.getElementById('openExternalPlatformBtn');

    if (container) container.style.display = 'block';

    if (type === 'google_meet') {
        if (label) label.textContent = 'Google Meet Link / URL';
        if (input) input.placeholder = 'Paste your Google Meet link here (e.g., https://meet.google.com/abc-defg-hij)';
        if (extBtn) {
            extBtn.style.display = 'inline-flex';
            extBtn.href = 'https://meet.google.com/new';
            extBtn.innerHTML = '<i class="fas fa-external-link-alt"></i> Create Link on Google Meet';
        }
    } else if (type === 'teams') {
        if (label) label.textContent = 'Microsoft Teams Link / URL';
        if (input) input.placeholder = 'Paste your MS Teams link here (e.g., https://teams.microsoft.com/l/meetup-join/...)';
        if (extBtn) {
            extBtn.style.display = 'inline-flex';
            extBtn.href = 'https://teams.microsoft.com';
            extBtn.innerHTML = '<i class="fas fa-external-link-alt"></i> Open MS Teams';
        }
    } else {
        if (label) label.textContent = 'Physical Location / Address';
        if (input) input.placeholder = 'e.g., Meeting Room A, Level 3';
        if (extBtn) extBtn.style.display = 'none';
    }
}

async function submitCreateMeeting() {
    const title = document.getElementById('meetingTitleInput').value.trim();
    const meeting_type = document.getElementById('meetingPlatformSelect').value;
    let start_time = document.getElementById('meetingStartTimeInput').value.replace('T', ' ');
    if (start_time && start_time.length === 16) start_time += ':00';

    let end_time = document.getElementById('meetingEndTimeInput').value.replace('T', ' ');
    if (end_time && end_time.length === 16) end_time += ':00';

    const location = document.getElementById('meetingLocationInput').value.trim();
    const description = document.getElementById('meetingDescriptionInput').value.trim();
    const participant_ids = Array.from(document.querySelectorAll('.meeting-participant-checkbox:checked')).map(cb => cb.value);
    const send_chat_invite = document.getElementById('sendChatInviteCheckbox').checked;
    const btn = document.getElementById('submitMeetingBtn');

    if (!title || !start_time || !end_time) {
        return alert('Please enter Meeting Title, Start Time, and End Time.');
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scheduling...';

    try {
        const res = await fetch('/chat/meetings/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                meeting_type,
                start_time,
                end_time,
                location,
                description,
                participant_ids,
                send_chat_invite,
                target_chat_id: currentReceiverId
            })
        });

        if (res.status === 401) {
            alert('🔒 Session expired. Please log in again.');
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        if (res.ok && data.success) {
            alert('🎉 Meeting scheduled successfully!');
            closeCreateMeetingModal();
            loadCalendarMeetings();

            if (data.message_id && currentReceiverId) {
                loadMessages(currentReceiverId);
            }
        } else {
            alert('❌ ' + (data.error || 'Failed to schedule meeting'));
            if (data.redirect) window.location.href = data.redirect;
        }
    } catch (err) {
        alert('Failed to connect to server: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-calendar-check"></i> Create Meeting';
    }
}

async function confirmDeleteMeeting(meetingId, title) {
    if (confirm(`Are you sure you want to cancel the meeting "${title}"?`)) {
        try {
            const res = await fetch(`/chat/meetings/${meetingId}/delete`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                loadCalendarMeetings();
            } else {
                alert('❌ ' + data.error);
            }
        } catch (err) {
            alert('Failed to cancel meeting.');
        }
    }
}

function viewMeetingDetails(meetingId) {
    const meeting = allMeetingsList.find(m => m.meeting_id === meetingId);
    if (!meeting) return;

    const modal = document.getElementById('viewMeetingDetailsModal');
    const body = document.getElementById('viewMeetingDetailsBody');
    if (!modal || !body) return;

    const typeBadge = meeting.meeting_type === 'google_meet' ? '<span style="background:#ea4335; color:white; font-size:12px; padding:4px 10px; border-radius:12px; font-weight:600;"><i class="fas fa-video"></i> Google Meet</span>'
        : meeting.meeting_type === 'teams' ? '<span style="background:#464eb8; color:white; font-size:12px; padding:4px 10px; border-radius:12px; font-weight:600;"><i class="fas fa-users-rectangle"></i> MS Teams</span>'
        : '<span style="background:#059669; color:white; font-size:12px; padding:4px 10px; border-radius:12px; font-weight:600;"><i class="fas fa-map-marker-alt"></i> Physical Location</span>';

    const isLink = meeting.location_or_link && meeting.location_or_link.startsWith('http');
    const locationHtml = isLink 
        ? `<a href="${meeting.location_or_link}" target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none; word-break:break-all;"><i class="fas fa-external-link-alt"></i> ${meeting.location_or_link}</a>`
        : `<span>${escapeHtml(meeting.location_or_link || 'Physical Location')}</span>`;

    let participantsHtml = '<div style="display:flex; flex-wrap:wrap; gap:6px;">';
    if (meeting.participants && meeting.participants.length > 0) {
        meeting.participants.forEach(p => {
            participantsHtml += `<span style="background:#f1f5f9; color:#334155; padding:4px 10px; border-radius:16px; font-size:12px; font-weight:500; border:1px solid #e2e8f0;"><i class="fas fa-user-circle" style="color:#64748b;"></i> ${escapeHtml(p.username)}</span>`;
        });
    } else {
        participantsHtml += '<span style="color:#94a3b8; font-size:13px;">No participants specified</span>';
    }
    participantsHtml += '</div>';

    body.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <h3 style="margin:0; font-size:20px; font-weight:700; color:#1a2b4c;">${escapeHtml(meeting.title)}</h3>
            ${typeBadge}
        </div>
        
        <div style="background:#f8fafc; border-radius:12px; padding:14px; border:1px solid #e2e8f0; display:flex; flex-direction:column; gap:8px;">
            <div style="font-size:13px; color:#475569;"><i class="fas fa-calendar-day" style="width:20px; color:#2563eb;"></i> <strong>Start Time:</strong> ${meeting.start_time}</div>
            <div style="font-size:13px; color:#475569;"><i class="fas fa-clock" style="width:20px; color:#2563eb;"></i> <strong>End Time:</strong> ${meeting.end_time}</div>
            <div style="font-size:13px; color:#475569;"><i class="fas fa-user-tie" style="width:20px; color:#2563eb;"></i> <strong>Organizer:</strong> ${escapeHtml(meeting.organizer_name)}</div>
            <div style="font-size:13px; color:#475569;"><i class="fas fa-map-marker-alt" style="width:20px; color:#2563eb;"></i> <strong>Link / Location:</strong> ${locationHtml}</div>
        </div>

        <div>
            <label style="font-size:12px; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Invited Participants (${meeting.participants ? meeting.participants.length : 0})</label>
            ${participantsHtml}
        </div>

        ${meeting.description ? `
        <div>
            <label style="font-size:12px; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Meeting Agenda / Description</label>
            <div style="background:#f1f5f9; padding:10px 14px; border-radius:8px; font-size:13px; color:#334155;">${escapeHtml(meeting.description)}</div>
        </div>` : ''}`;

    modal.style.display = 'flex';
}

function closeMeetingDetailsModal() {
    const modal = document.getElementById('viewMeetingDetailsModal');
    if (modal) modal.style.display = 'none';
}

function openEditMeetingModal(meetingId) {
    const meeting = allMeetingsList.find(m => m.meeting_id === meetingId);
    if (!meeting) return;

    const modal = document.getElementById('editMeetingModal');
    if (!modal) return;

    document.getElementById('editMeetingIdInput').value = meeting.meeting_id;
    document.getElementById('editMeetingTitleInput').value = meeting.title;
    document.getElementById('editMeetingPlatformSelect').value = meeting.meeting_type;
    document.getElementById('editMeetingLocationInput').value = meeting.location_or_link || '';
    
    if (meeting.start_time) {
        document.getElementById('editMeetingStartTimeInput').value = meeting.start_time.replace(' ', 'T').slice(0, 16);
    }
    if (meeting.end_time) {
        document.getElementById('editMeetingEndTimeInput').value = meeting.end_time.replace(' ', 'T').slice(0, 16);
    }
    document.getElementById('editMeetingDescriptionInput').value = meeting.description || '';

    modal.style.display = 'flex';
}

function closeEditMeetingModal() {
    const modal = document.getElementById('editMeetingModal');
    if (modal) modal.style.display = 'none';
}

async function submitUpdateMeeting() {
    const meetingId = document.getElementById('editMeetingIdInput').value;
    const title = document.getElementById('editMeetingTitleInput').value.trim();
    const meeting_type = document.getElementById('editMeetingPlatformSelect').value;
    let start_time = document.getElementById('editMeetingStartTimeInput').value.replace('T', ' ');
    if (start_time && start_time.length === 16) start_time += ':00';

    let end_time = document.getElementById('editMeetingEndTimeInput').value.replace('T', ' ');
    if (end_time && end_time.length === 16) end_time += ':00';

    const location = document.getElementById('editMeetingLocationInput').value.trim();
    const description = document.getElementById('editMeetingDescriptionInput').value.trim();
    const btn = document.getElementById('submitEditMeetingBtn');

    if (!title || !start_time || !end_time) {
        return alert('Please enter Meeting Title, Start Time, and End Time.');
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const res = await fetch(`/chat/meetings/${meetingId}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                meeting_type,
                start_time,
                end_time,
                location,
                description
            })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            alert('✅ Meeting updated successfully!');
            closeEditMeetingModal();
            loadCalendarMeetings();
        } else {
            alert('❌ ' + (data.error || 'Failed to update meeting'));
        }
    } catch (err) {
        alert('Failed to connect to server.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
    }
}

function getFileIcon(filename) {
    if (!filename) return 'fas fa-file';
    const ext = filename.split('.').pop().toLowerCase();
    const icons = { pdf: 'fas fa-file-pdf', jpg: 'fas fa-file-image', jpeg: 'fas fa-file-image', png: 'fas fa-file-image', gif: 'fas fa-file-image', mp4: 'fas fa-file-video', doc: 'fas fa-file-word', docx: 'fas fa-file-word', txt: 'fas fa-file-alt', zip: 'fas fa-file-archive' };
    return icons[ext] || 'fas fa-file';
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (dateStr === today.toISOString().split('T')[0]) return 'Today';
    if (dateStr === yesterday.toISOString().split('T')[0]) return 'Yesterday';
    return date.toLocaleDateString('en-MY', { day: 'numeric', month: 'short', year: 'numeric' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

async function loadUnreadCounts() {
    try {
        const res = await fetch('/chat/unread-counts');
        const data = await res.json();

        if (data.success && data.unread_counts) {
            document.querySelectorAll('.unread-pill-badge').forEach(badge => badge.style.display = 'none');

            for (const [senderId, count] of Object.entries(data.unread_counts)) {
                if (count > 0 && String(senderId) !== String(currentReceiverId)) {
                    unreadCounts[senderId] = count;
                    const badge = document.getElementById(`unread-badge-${senderId}`);
                    if (badge) {
                        badge.textContent = count;
                        badge.style.display = 'inline-flex';
                    }
                    const timeEl = document.getElementById(`time-${senderId}`);
                    if (timeEl) timeEl.style.color = '#22c55e';
                }
            }

            for (const [key, count] of Object.entries(unreadCounts)) {
                if (String(key).startsWith('g-') && count > 0) {
                    const badge = document.getElementById(`unread-badge-${key}`);
                    if (badge) {
                        badge.textContent = count;
                        badge.style.display = 'inline-flex';
                    }
                }
            }

            updateNavChatsBadge();
        }
    } catch (err) {}
}

async function loadCalendarUnreadBadge() {
    try {
        const res = await fetch('/chat/meetings/unread-count');
        const data = await res.json();
        const badge = document.getElementById('navCalendarBadge');
        if (badge) {
            if (data.success && data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (err) {}
}

document.addEventListener('DOMContentLoaded', () => {
    updateFavUI();
    loadUnreadCounts();
    loadCalendarUnreadBadge();
});
