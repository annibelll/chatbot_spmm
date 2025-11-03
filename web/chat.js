
const canvas = document.getElementById("network");
const ctx = canvas.getContext("2d");

let width, height, nodes = [];

function resize() {
  width = canvas.width = window.innerWidth;
  height = canvas.height = window.innerHeight;
  createNodes();
}

function createNodes() {
  const count = Math.floor((width * height) / 15000);
  nodes = [];
  for (let i = 0; i < count; i++) {
    nodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: Math.random() * 2 + 1
    });
  }
}

function draw() {
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#00bfff";
  for (let p of nodes) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > width) p.vx *= -1;
    if (p.y < 0 || p.y > height) p.vy *= -1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 250) {
        const alpha = 1 - dist / 250;
        ctx.strokeStyle = `rgba(0,191,255,${alpha * 0.5})`;
        ctx.beginPath();
        ctx.moveTo(nodes[i].x, nodes[i].y);
        ctx.lineTo(nodes[j].x, nodes[j].y);
        ctx.stroke();
      }
    }
  }

  requestAnimationFrame(draw);
}

window.addEventListener("resize", resize);
resize();
draw();


// === Навігація та логіка чату ===
window.addEventListener("DOMContentLoaded", () => {
  const homeBtn = document.getElementById("home-btn");
  if (homeBtn) homeBtn.onclick = () => window.location.href = "index.html";

  const studyBtn = document.getElementById("study-mode");
  const quizBtn = document.getElementById("quiz-mode");
  if (studyBtn && quizBtn) {
    studyBtn.onclick = () => switchMode("study");
    quizBtn.onclick = () => switchMode("quiz");
  }

  const sendBtn = document.getElementById("send-btn");
  const input = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");

  if (sendBtn) sendBtn.onclick = sendMessage;
  if (input) input.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });

  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    const userMsg = document.createElement("div");
    userMsg.classList.add("message", "user");
    userMsg.textContent = text;
    chatBox.appendChild(userMsg);
    input.value = "";

    const aiMsg = document.createElement("div");
    aiMsg.classList.add("message", "ai");
    aiMsg.textContent = "Thinking... 🤖";
    chatBox.appendChild(aiMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    setTimeout(() => {
      aiMsg.textContent = generateReply(text);
    }, 800);
  }

  function generateReply(text) {
    const t = text.toLowerCase();
    if (t.includes("quiz")) return "Let’s make a short quiz from your notes 🧩";
    if (t.includes("hello") || t.includes("hi")) return "Hi! Ready to study?";
    if (t.includes("explain")) return "Sure! Let me summarize that concept for you...";
    return "Hmm… I’ll analyze your uploaded materials for context.";
  }

  
  const fileInput = document.getElementById("file-upload");
  const sourcesList = document.getElementById("sources-list");

  if (fileInput && sourcesList) {
    fileInput.addEventListener("change", () => {
      Array.from(fileInput.files).forEach(file => {
        const li = document.createElement("li");
        li.textContent = file.name;
        sourcesList.appendChild(li);
      });
    });
  }

  function switchMode(mode) {
    document.querySelectorAll(".mode").forEach(b => b.classList.remove("active"));
    if (mode === "study") studyBtn.classList.add("active");
    else quizBtn.classList.add("active");

    const msg = document.createElement("div");
    msg.classList.add("message", "ai");
    msg.textContent = mode === "study"
      ? "Switched to Study mode 🧠 — ask me anything about your materials!"
      : "Switched to Quiz mode 🧩 — I’ll test your knowledge!";
    chatBox.appendChild(msg);
  }
});
