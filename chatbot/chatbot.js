// Chatbot functionality
const CHAT_API_URL = "http://localhost:5050/api/chat";

function toggleChat() {
  const modal = document.getElementById("chatModal");
  if (modal && modal.classList.contains("show")) {
    closeChat();
  } else {
    openChat();
  }
}

function openChat() {
  const modal = document.getElementById("chatModal");
  const backdrop = document.getElementById("modalBackdrop");
  const button = document.getElementById("chatButton");

  if (backdrop) backdrop.classList.add("show");
  if (modal) modal.classList.add("show");
  if (button) button.classList.add("active");

  // Focus input
  setTimeout(() => {
    const input = document.getElementById("chatInput");
    if (input) input.focus();
  }, 300);

  // Check API connection
  checkApiConnection();
}

function closeChat() {
  const modal = document.getElementById("chatModal");
  const backdrop = document.getElementById("modalBackdrop");
  const button = document.getElementById("chatButton");

  if (backdrop) backdrop.classList.remove("show");
  if (modal) modal.classList.remove("show");
  if (button) button.classList.remove("active");
}

async function checkApiConnection() {
  const statusElement = document.getElementById("chatStatus");
  const statusText = document.getElementById("chatStatusText");

  if (!statusElement || !statusText) return;

  try {
    const response = await fetch(CHAT_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: "test" }),
    });

    if (response.ok || response.status === 400) {
      // API is reachable (400 means it's working but needs valid message)
      statusElement.classList.remove("offline");
      statusText.textContent = "Online";
    } else {
      throw new Error("API not available");
    }
  } catch (error) {
    statusElement.classList.add("offline");
    statusText.textContent = "Offline";
  }
}

async function sendMessage() {
  const input = document.getElementById("chatInput");
  const sendButton = document.getElementById("sendButton");
  if (!input || !sendButton) return;

  const message = input.value.trim();

  if (!message) return;

  // Disable input and button
  input.disabled = true;
  sendButton.disabled = true;

  // Add user message
  addMessage(message, "user");
  input.value = "";

  // Hide suggested questions after sending a message
  hideSuggestedQuestions();

  // Show loading
  showLoading();

  try {
    const response = await fetch(CHAT_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Hide loading
    hideLoading();

    // Add AI response
    if (data.response) {
      addMessage(data.response, "ai");
      // Show suggested questions again after receiving a response
      showSuggestedQuestions();
    } else if (data.error) {
      addErrorMessage(data.error);
    } else {
      addErrorMessage("Unexpected response from server");
    }

    // Update status
    const statusElement = document.getElementById("chatStatus");
    const statusText = document.getElementById("chatStatusText");
    if (statusElement && statusText) {
      statusElement.classList.remove("offline");
      statusText.textContent = "Online";
    }
  } catch (error) {
    hideLoading();
    addErrorMessage(
      "Failed to connect to the chatbot API. Make sure the Flask server is running on " +
        CHAT_API_URL
    );

    // Update status
    const statusElement = document.getElementById("chatStatus");
    const statusText = document.getElementById("chatStatusText");
    if (statusElement && statusText) {
      statusElement.classList.add("offline");
      statusText.textContent = "Offline";
    }
  } finally {
    // Re-enable input and button
    if (input) {
      input.disabled = false;
      input.focus();
    }
    if (sendButton) sendButton.disabled = false;
  }
}

function addMessage(text, type) {
  const messagesDiv = document.getElementById("chatMessages");
  if (!messagesDiv) return;

  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${type}`;

  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  messageDiv.innerHTML = `
        <div class="message-bubble">${escapeHtml(text)}</div>
        <div class="message-time">${timeStr}</div>
    `;

  messagesDiv.appendChild(messageDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addErrorMessage(text) {
  const messagesDiv = document.getElementById("chatMessages");
  if (!messagesDiv) return;

  const errorDiv = document.createElement("div");
  errorDiv.className = "error-message";
  errorDiv.textContent = text;
  messagesDiv.appendChild(errorDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showLoading() {
  const messagesDiv = document.getElementById("chatMessages");
  if (!messagesDiv) return;

  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message loading";
  loadingDiv.id = "loadingMessage";
  loadingDiv.innerHTML = `
        <div class="loading-indicator">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
  messagesDiv.appendChild(loadingDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideLoading() {
  const loading = document.getElementById("loadingMessage");
  if (loading) {
    loading.remove();
  }
}

function resetChat() {
  if (confirm("Reset conversation history?")) {
    const messagesDiv = document.getElementById("chatMessages");
    if (messagesDiv) {
      messagesDiv.innerHTML = `
                <div class="message ai">
                    <div class="message-bubble">
                        Conversation reset. How can I help you?
                    </div>
                    <div class="message-time">Just now</div>
                </div>
            `;
    }
    // Show suggested questions again after reset
    showSuggestedQuestions();
  }
}

function handleChatKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function useSuggestedQuestion(question) {
  const input = document.getElementById("chatInput");
  if (input) {
    // Set the input value
    input.value = question;
    // Trigger input event to ensure the value is properly set
    input.dispatchEvent(new Event("input", { bubbles: true }));
    // Focus the input
    input.focus();
    // Hide suggested questions after selecting one
    hideSuggestedQuestions();
    // Small delay to ensure the value is set, then auto-send
    setTimeout(() => {
      if (input.value.trim() === question.trim()) {
        sendMessage();
      }
    }, 100);
  }
}

function showSuggestedQuestions() {
  const suggestedQuestions = document.getElementById("suggestedQuestions");
  if (suggestedQuestions) {
    suggestedQuestions.classList.remove("hidden");
  }
}

function hideSuggestedQuestions() {
  const suggestedQuestions = document.getElementById("suggestedQuestions");
  if (suggestedQuestions) {
    suggestedQuestions.classList.add("hidden");
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Initialize chatbot when DOM is ready
function initChatbot() {
  // Inject chatbot HTML into the container
  const chatbotContainer = document.getElementById("chatbot-container");
  if (!chatbotContainer) {
    console.error(
      'Chatbot container not found. Make sure there is an element with id="chatbot-container"'
    );
    return;
  }

  chatbotContainer.innerHTML = `
        <!-- Chat Button (Floating) -->
        <button class="chat-button" id="chatButton" onclick="toggleChat()" aria-label="Open chatbot">
            💬
        </button>

        <!-- Modal Backdrop -->
        <div class="modal-backdrop" id="modalBackdrop" onclick="closeChat()"></div>

        <!-- Chat Modal -->
        <div class="chat-modal" id="chatModal" role="dialog" aria-labelledby="chatModalTitle" aria-modal="true">
            <!-- Modal Header -->
            <div class="chat-modal-header">
                <div>
                    <h3 id="chatModalTitle">Research Chatbot</h3>
                    <div style="display: flex; align-items: center; margin-top: 5px;">
                        <span class="chat-status" id="chatStatus"></span>
                        <span style="font-size: 11px; color: #aaa;" id="chatStatusText">Online</span>
                    </div>
                </div>
                <div class="chat-modal-actions">
                    <button class="chat-reset-btn" onclick="resetChat()" aria-label="Reset conversation">Reset</button>
                    <button class="chat-close-btn" onclick="closeChat()" aria-label="Close chatbot">×</button>
                </div>
            </div>

            <!-- Chat Messages Area -->
            <div class="chat-messages" id="chatMessages" role="log" aria-live="polite" aria-atomic="false">
                <div class="message ai">
                    <div class="message-bubble">
                        Hello! I'm your research assistant. Ask me anything about Physical Sciences research data, including fields, subfields, topics, and funders.
                    </div>
                    <div class="message-time">Just now</div>
                </div>
            </div>

            <!-- Suggested Questions -->
            <div class="suggested-questions" id="suggestedQuestions">
                <div class="suggested-question-row">
                    <button class="suggested-question-btn" onclick="useSuggestedQuestion('What fields are in Physical Sciences?')">What fields are in Physical Sciences?</button>
                    <button class="suggested-question-btn" onclick="useSuggestedQuestion('What are the top subfields in Physical Sciences?')">What are the top subfields?</button>
                </div>
                <div class="suggested-question-row">
                    <button class="suggested-question-btn" onclick="useSuggestedQuestion('What are the top topics in Physical Sciences?')">What are the top topics?</button>
                    <button class="suggested-question-btn" onclick="useSuggestedQuestion('Summarize the Physical Sciences research data')">Summarize the research data</button>
                </div>
            </div>

            <!-- Chat Input Area -->
            <div class="chat-input-area">
                <textarea
                    class="chat-input"
                    id="chatInput"
                    placeholder="Ask about research data..."
                    rows="1"
                    aria-label="Type your message"
                    onkeydown="handleChatKeyPress(event)"
                ></textarea>
                <button class="chat-send-btn" id="sendButton" onclick="sendMessage()" aria-label="Send message">Send</button>
            </div>
        </div>
    `;

  // Close on ESC key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const modal = document.getElementById("chatModal");
      if (modal && modal.classList.contains("show")) {
        closeChat();
      }
    }
  });
}

// Initialize when DOM is loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initChatbot);
} else {
  initChatbot();
}
