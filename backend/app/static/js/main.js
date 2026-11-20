/**
 * Enterprise RAG Assistant - Client JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('pdf-file-input');
    const dropzoneTrigger = document.getElementById('dropzone-trigger');
    const dropzone = document.querySelector('.dropzone');
    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressText = document.getElementById('upload-progress-text');

    const documentList = document.getElementById('document-list');
    const emptyDocsPlaceholder = document.getElementById('empty-docs-placeholder');
    const totalDocCount = document.getElementById('total-doc-count');
    const totalChunkCount = document.getElementById('total-chunk-count');
    const sidebarDocBadge = document.getElementById('sidebar-doc-badge');

    const chatForm = document.getElementById('chat-form');
    const questionInput = document.getElementById('question-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const welcomeBanner = document.getElementById('welcome-banner');
    const thinkingIndicator = document.getElementById('thinking-indicator');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const toastContainer = document.getElementById('toast-container');

    // Helper: Get CSRF Token
    function getCsrfToken() {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) return input.value;
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    // Helper: Toast Notifications
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // Helper: Scroll Chat to Bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // =========================================================================
    // Document Upload Handling
    // =========================================================================
    if (dropzoneTrigger && fileInput) {
        dropzoneTrigger.addEventListener('click', () => fileInput.click());

        // Drag & Drop events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }

    function handleFileUpload(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showToast('Only PDF files are supported.', 'error');
            return;
        }

        if (file.size > 20 * 1024 * 1024) {
            showToast('File size exceeds 20 MB limit.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Show progress UI
        progressContainer.style.display = 'block';
        progressBar.style.width = '35%';
        progressText.textContent = `Uploading ${file.name}...`;

        setTimeout(() => {
            progressBar.style.width = '65%';
            progressText.textContent = 'Chunking text & computing embeddings...';
        }, 600);

        fetch('/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            progressBar.style.width = '100%';
            if (data.success) {
                progressText.textContent = 'Indexing complete!';
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    progressBar.style.width = '0%';
                }, 1000);

                showToast(`"${file.name}" indexed successfully!`, 'success');
                addDocumentToUI(data.document);
            } else {
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
                showToast(data.error || 'Upload failed.', 'error');
            }
        })
        .catch(err => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
            showToast('Error uploading document: ' + err.message, 'error');
        })
        .finally(() => {
            fileInput.value = '';
        });
    }

    function addDocumentToUI(doc) {
        if (emptyDocsPlaceholder) {
            emptyDocsPlaceholder.remove();
        }

        const card = document.createElement('div');
        card.className = 'doc-card';
        card.id = `doc-card-${doc.id}`;
        card.dataset.id = doc.id;
        card.innerHTML = `
            <div class="doc-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
            </div>
            <div class="doc-info">
                <div class="doc-title" title="${escapeHtml(doc.name)}">${escapeHtml(doc.name)}</div>
                <div class="doc-meta">
                    <span>${doc.page_count} pg${doc.page_count === 1 ? '' : 's'}</span>
                    <span class="meta-dot">&bull;</span>
                    <span>${doc.chunk_count} chunks</span>
                    <span class="meta-dot">&bull;</span>
                    <span>${doc.file_size}</span>
                </div>
            </div>
            <button type="button" class="btn-icon delete-doc-btn" data-id="${doc.id}" data-name="${escapeHtml(doc.name)}" title="Delete document">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        `;

        documentList.prepend(card);

        // Update counts
        const currentDocs = parseInt(totalDocCount.textContent || '0') + 1;
        const currentChunks = parseInt(totalChunkCount.textContent || '0') + doc.chunk_count;
        totalDocCount.textContent = currentDocs;
        totalChunkCount.textContent = currentChunks;
        if (sidebarDocBadge) {
            sidebarDocBadge.textContent = `${currentDocs} file${currentDocs === 1 ? '' : 's'}`;
        }
    }

    // =========================================================================
    // Document Deletion Handling
    // =========================================================================
    documentList.addEventListener('click', (e) => {
        const deleteBtn = e.target.closest('.delete-doc-btn');
        if (!deleteBtn) return;

        const docId = deleteBtn.dataset.id;
        const docName = deleteBtn.dataset.name || 'document';

        if (!confirm(`Are you sure you want to delete "${docName}"? This will remove its vectors from the search index.`)) {
            return;
        }

        fetch(`/documents/${docId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const card = document.getElementById(`doc-card-${docId}`);
                if (card) {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    card.style.transition = 'all 0.2s ease';
                    setTimeout(() => {
                        card.remove();
                        const currentDocs = Math.max(0, parseInt(totalDocCount.textContent || '0') - 1);
                        totalDocCount.textContent = currentDocs;
                        if (sidebarDocBadge) {
                            sidebarDocBadge.textContent = `${currentDocs} file${currentDocs === 1 ? '' : 's'}`;
                        }
                        if (currentDocs === 0) {
                            totalChunkCount.textContent = '0';
                            documentList.innerHTML = `
                                <div class="empty-docs" id="empty-docs-placeholder">
                                    <div class="empty-icon">
                                        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                            <line x1="12" y1="8" x2="12" y2="16"></line>
                                            <line x1="8" y1="12" x2="16" y2="12"></line>
                                        </svg>
                                    </div>
                                    <p class="empty-title">No documents yet</p>
                                    <p class="empty-desc">Upload a PDF to start asking grounded questions with AI.</p>
                                </div>
                            `;
                        }
                    }, 200);
                }
                showToast(`"${docName}" deleted.`, 'info');
            } else {
                showToast('Failed to delete document.', 'error');
            }
        })
        .catch(err => {
            showToast('Error deleting document: ' + err.message, 'error');
        });
    });

    // =========================================================================
    // Chat Interaction
    // =========================================================================
    // Auto-grow textarea
    questionInput.addEventListener('input', () => {
        questionInput.style.height = 'auto';
        questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + 'px';
    });

    // Enter to send, Shift+Enter for newline
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    // Suggestion chip clicks
    document.addEventListener('click', (e) => {
        const chip = e.target.closest('.suggestion-chip');
        if (!chip) return;
        const prompt = chip.dataset.prompt;
        if (prompt) {
            questionInput.value = prompt;
            chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question) return;

        // Hide welcome banner if visible
        if (welcomeBanner) {
            welcomeBanner.style.display = 'none';
        }

        // Render User Message
        appendUserMessage(question);
        questionInput.value = '';
        questionInput.style.height = 'auto';

        // Show thinking indicator
        thinkingIndicator.style.display = 'flex';
        scrollToBottom();

        // Submit query
        fetch('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ question })
        })
        .then(res => res.json())
        .then(data => {
            thinkingIndicator.style.display = 'none';
            if (data.success) {
                appendAssistantMessage(data.answer, data.sources, data.created_at);
            } else {
                appendAssistantMessage(`❌ **Error:** ${data.error || 'Failed to generate answer.'}`, [], 'Now');
            }
        })
        .catch(err => {
            thinkingIndicator.style.display = 'none';
            appendAssistantMessage(`❌ **Network error:** ${err.message}`, [], 'Now');
        })
        .finally(() => {
            scrollToBottom();
            questionInput.focus();
        });
    });

    function appendUserMessage(text) {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const msg = document.createElement('div');
        msg.className = 'message user-message';
        msg.innerHTML = `
            <div class="message-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            </div>
            <div class="message-bubble">
                <div class="message-text">${escapeHtml(text)}</div>
                <div class="message-time">${timeStr}</div>
            </div>
        `;
        chatMessages.insertBefore(msg, thinkingIndicator);
        scrollToBottom();
    }

    function appendAssistantMessage(answer, sources = [], timeStr = '') {
        if (!timeStr) {
            timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        const msg = document.createElement('div');
        msg.className = 'message assistant-message';

        let citationsHtml = '';
        if (sources && sources.length > 0) {
            const items = sources.map(src => `
                <div class="citation-item">
                    <div class="citation-header">
                        <span class="citation-tag">Source [${src.source_number}]</span>
                        <span class="citation-doc">${escapeHtml(src.document_name)}</span>
                        <span class="citation-page">Page ${src.page_number}</span>
                        <span class="citation-score">Score: ${src.relevance_score}</span>
                    </div>
                    <div class="citation-snippet">&ldquo;${escapeHtml(src.snippet)}&rdquo;</div>
                </div>
            `).join('');

            citationsHtml = `
                <div class="citations-accordion">
                    <button type="button" class="citations-toggle" onclick="this.parentElement.classList.toggle('open')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        <span>${sources.length} Source Citation${sources.length === 1 ? '' : 's'}</span>
                    </button>
                    <div class="citations-list">
                        ${items}
                    </div>
                </div>
            `;
        }

        // Basic markdown formatting
        const formattedAnswer = formatMarkdown(answer);

        msg.innerHTML = `
            <div class="message-avatar bot-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="10" rx="2"></rect>
                    <circle cx="12" cy="5" r="2"></circle>
                    <path d="M12 7v4"></path>
                    <line x1="8" y1="16" x2="8" y2="16"></line>
                    <line x1="16" y1="16" x2="16" y2="16"></line>
                </svg>
            </div>
            <div class="message-bubble">
                <div class="message-text formatted-content">${formattedAnswer}</div>
                ${citationsHtml}
                <div class="message-time">${timeStr}</div>
            </div>
        `;

        chatMessages.insertBefore(msg, thinkingIndicator);
        scrollToBottom();
    }

    // =========================================================================
    // Clear Chat History
    // =========================================================================
    clearChatBtn.addEventListener('click', () => {
        if (!confirm('Clear all conversation history?')) return;

        fetch('/chat/clear/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Remove all messages except thinking indicator
                const messages = chatMessages.querySelectorAll('.message:not(#thinking-indicator)');
                messages.forEach(m => m.remove());
                if (welcomeBanner) {
                    welcomeBanner.style.display = 'block';
                }
                showToast('Chat history cleared.', 'info');
            }
        })
        .catch(err => {
            showToast('Failed to clear chat: ' + err.message, 'error');
        });
    });

    // Helper: Escaping HTML
    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Helper: Simple Markdown Formatter
    function formatMarkdown(text) {
        if (!text) return '';
        let html = escapeHtml(text);
        
        // Bold: **text**
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Inline code: `text`
        html = html.replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.08);padding:2px 5px;border-radius:4px;font-family:monospace;font-size:0.85em;">$1</code>');
        
        // Citations highlight: [1], [2]
        html = html.replace(/\[(\d+)\]/g, '<span style="background:rgba(79,70,229,0.25);color:#a5b4fc;padding:1px 5px;border-radius:4px;font-weight:600;font-size:0.8em;">[$1]</span>');
        
        // Line breaks to paragraphs
        const paragraphs = html.split(/\n\s*\n/).filter(p => p.trim().length > 0);
        return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br/>')}</p>`).join('');
    }
});
