(function () {
  const API_BASE = "/api";
  const TOKEN_KEY = "token";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function redirectIfAuthenticated() {
    if (getToken()) {
      window.location.href = "chat.html";
    }
  }

  redirectIfAuthenticated();

  function showError(formId, message) {
    const el = document.getElementById(formId + "-error");
    if (el) {
      el.textContent = message;
      el.classList.remove("hidden");
    }
  }

  function hideError(formId) {
    const el = document.getElementById(formId + "-error");
    if (el) {
      el.textContent = "";
      el.classList.add("hidden");
    }
  }

  document.querySelectorAll(".tab").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const tab = this.getAttribute("data-tab");
      document.querySelectorAll(".tab").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-tab") === tab);
      });
      document.querySelectorAll(".form").forEach(function (f) {
        f.classList.toggle("active", f.id === tab + "-form");
      });
      hideError("login");
      hideError("register");
    });
  });

  document.getElementById("login-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    hideError("login");
    const form = e.target;
    const username = form.username.value.trim();
    const password = form.password.value;
    if (!username || !password) return;
    try {
      const res = await fetch(API_BASE + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        showError("login", data.detail || "Ошибка входа");
        return;
      }
      setToken(data.access_token);
      window.location.href = "chat.html";
    } catch (err) {
      showError("login", "Ошибка сети");
    }
  });

  document.getElementById("register-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    hideError("register");
    const form = e.target;
    const username = form.username.value.trim();
    const password = form.password.value;
    if (!username || !password) return;
    try {
      const res = await fetch(API_BASE + "/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        showError("register", data.detail || "Ошибка регистрации");
        return;
      }
      const loginRes = await fetch(API_BASE + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const loginData = await loginRes.json();
      if (!loginRes.ok) {
        showError("register", "Регистрация успешна, но вход не выполнен");
        return;
      }
      setToken(loginData.access_token);
      window.location.href = "chat.html";
    } catch (err) {
      showError("register", "Ошибка сети");
    }
  });
})();
