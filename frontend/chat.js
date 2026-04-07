(function () {
  const API_BASE = "/api";
  const TOKEN_KEY = "token";
  const WS_BASE = (window.location.protocol === "https:" ? "wss:" : "ws:") + "//" + window.location.host + "/ws";
  const USERS_REFRESH_MS = 5000;

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function redirectIfNotAuthenticated() {
    if (!getToken()) {
      window.location.href = "index.html";
      return true;
    }
    return false;
  }

  if (redirectIfNotAuthenticated()) {
    throw new Error("Not authenticated");
  }

  const token = getToken();
  let currentUser = null;
  let selectedUserId = null;
  let selectedUsername = "";
  let ws = null;

  function authHeaders() {
    return {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    };
  }

  async function api(path, options = {}) {
    const res = await fetch(API_BASE + path, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
    });
    if (res.status === 401) {
      clearToken();
      window.location.href = "index.html";
      throw new Error("Unauthorized");
    }
    return res;
  }

  async function loadMe() {
    const res = await api("/users/me");
    if (!res.ok) throw new Error("Failed to load user");
    currentUser = await res.json();
    document.getElementById("current-username").textContent = currentUser.username;
  }

  async function loadUsers() {
    const res = await api("/users");
    if (!res.ok) return [];
    return res.json();
  }

  async function loadMessages(withUserId) {
    const path = withUserId ? "/messages?with_user=" + withUserId : "/messages";
    const res = await api(path);
    if (!res.ok) return [];
    return res.json();
  }

  function renderUsers(users) {
    const ul = document.getElementById("users-list");
    ul.innerHTML = "";
    users.forEach(function (u) {
      const li = document.createElement("li");
      li.classList.add("user-item");
      li.dataset.userId = u.id;
      li.innerHTML = "<span class=\"name\">" + escapeHtml(u.username) + "</span>";
      if (selectedUserId === u.id) li.classList.add("selected");
      li.addEventListener("click", function () {
        selectUser(u.id, u.username);
      });
      ul.appendChild(li);
    });

    if (selectedUserId && !users.some(function (u) { return u.id === selectedUserId; })) {
      selectedUserId = null;
      selectedUsername = "";
      document.getElementById("chat-with-name").textContent = "Выберите пользователя";
      document.getElementById("messages-list").innerHTML = "";
    }

    if (!selectedUserId && users.length > 0) {
      selectUser(users[0].id, users[0].username);
    }
  }

  function selectUser(userId, username) {
    selectedUserId = userId;
    selectedUsername = username;
    document.getElementById("chat-with-name").textContent = "Чат с " + username;
    document.querySelectorAll("#users-list li").forEach(function (li) {
      li.classList.toggle("selected", li.dataset.userId === userId);
    });
    loadAndRenderMessages();
  }

  function renderMessages(messages) {
    const ul = document.getElementById("messages-list");
    ul.innerHTML = "";
    messages.forEach(function (m) {
      const li = document.createElement("li");
      li.classList.add(m.sender_id === currentUser.id ? "sent" : "received");
      const who = m.sender_id === currentUser.id ? "Вы" : (selectedUsername || "Собеседник");
      const sig = m.signature_valid ? "" : " (подпись не проверена)";
      li.innerHTML = "<span class=\"who\">" + who + sig + "</span><span class=\"text\">" + escapeHtml(m.payload) + "</span>";
      ul.appendChild(li);
    });
    ul.scrollTop = ul.scrollHeight;
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  async function loadAndRenderMessages() {
    if (!selectedUserId) return;
    const messages = await loadMessages(selectedUserId);
    renderMessages(messages);
  }

  async function refreshUsers() {
    try {
      const users = await loadUsers();
      renderUsers(users);
    } catch (_) {}
  }

  async function sendMessage() {
    const input = document.getElementById("message-input");
    const text = input.value.trim();
    if (!text || !selectedUserId) return;
    try {
      const res = await api("/messages", {
        method: "POST",
        body: JSON.stringify({ receiver_id: selectedUserId, payload: text }),
      });
      if (!res.ok) {
        const err = await res.json();
        alert(err.detail || "Ошибка отправки");
        return;
      }
      input.value = "";
      loadAndRenderMessages();
    } catch (e) {
      alert("Ошибка отправки");
    }
  }

  function connectWs() {
    const url = WS_BASE + "?token=" + encodeURIComponent(token);
    ws = new WebSocket(url);
    ws.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "new_message" && data.sender_id && data.message_id) {
          if (data.sender_id === selectedUserId) {
            loadAndRenderMessages();
          }
          refreshUsers();
        }
      } catch (_) {}
    };
    ws.onclose = function () {
      setTimeout(connectWs, 3000);
    };
  }

  document.getElementById("send-btn").addEventListener("click", sendMessage);
  document.getElementById("message-input").addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendMessage();
  });

  document.querySelector(".logout").addEventListener("click", function (e) {
    e.preventDefault();
    clearToken();
    window.location.href = "index.html";
  });

  (async function init() {
    await loadMe();
    await refreshUsers();
    connectWs();
    setInterval(refreshUsers, USERS_REFRESH_MS);
  })();
})();
