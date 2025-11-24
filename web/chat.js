const canvas = document.getElementById("network");
const ctx = canvas.getContext("2d");

let width,
  height,
  nodes = [];

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
      radius: Math.random() * 2 + 1,
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

window.addEventListener("DOMContentLoaded", async () => {
  const input = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const chatBox = document.getElementById("chat-box");
  const fileInput = document.getElementById("file-upload");
  const sourcesList = document.getElementById("sources-list");
  const deleteAllBtn = document.getElementById("delete-all");

  const studyBtn = document.getElementById("study-mode");
  const quizBtn = document.getElementById("quiz-mode");

  const profileBtn = document.getElementById("profile-btn");
  if (profileBtn) {
    profileBtn.onclick = () => {
      const userId = localStorage.getItem("user_id") || "guest";
      window.location.href = `profile.html?user_id=${encodeURIComponent(userId)}`;
    };
  }

  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.onclick = sendMessage;

  await loadExistingFiles();

  if (fileInput) {
    fileInput.addEventListener("change", async () => {
      const files = Array.from(fileInput.files);
      for (const f of files) await uploadFile(f);
      await loadExistingFiles();
      fileInput.value = "";
    });
  }

  if (deleteAllBtn) {
    deleteAllBtn.onclick = async () => {
      if (!confirm("Delete ALL uploaded files + embeddings?")) return;

      await fetch("http://127.0.0.1:8000/chat/files/clear_all", {
        method: "DELETE",
      });

      sourcesList.innerHTML = "";
      alert("All files removed.");
    };
  }

  studyBtn.onclick = () => switchMode("study");
  quizBtn.onclick = () => switchMode("quiz");

  let quizActive = false;
  let quizStarting = false;
  let activeQuizId = null;
  let currentQuestionId = null;
  let currentQuestionOpen = false;

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    const userMsg = document.createElement("div");
    userMsg.classList.add("message", "user");
    userMsg.textContent = text;
    chatBox.appendChild(userMsg);
    input.value = "";

    if (quizActive && currentQuestionOpen) {
      await sendAnswer(text);
      return;
    }

    const aiMsg = document.createElement("div");
    aiMsg.classList.add("message", "ai");
    aiMsg.textContent = "Analyzing your materials...";
    chatBox.appendChild(aiMsg);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          language: "en",
        }),
      });

      const data = await res.json();
      aiMsg.textContent = data.answer || "No response.";
    } catch (err) {
      aiMsg.textContent = "Server error.";
    }

    chatBox.scrollTop = chatBox.scrollHeight;
  }

  async function loadExistingFiles() {
    try {
      const res = await fetch("http://127.0.0.1:8000/chat/files");
      const data = await res.json();
      sourcesList.innerHTML = "";

      data.files.forEach((f) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <span>${f}</span>
          <button class="delete-btn">✖</button>
        `;
        li.querySelector("button").onclick = () => deleteFile(f, li);
        sourcesList.appendChild(li);
      });
    } catch (err) {
      console.error("Could not load files", err);
    }
  }

  async function deleteFile(name, li) {
    li.remove();
    await fetch(
      `http://127.0.0.1:8000/chat/files/${encodeURIComponent(name)}`,
      { method: "DELETE" },
    );
  }

  async function uploadFile(file) {
    const form = new FormData();
    form.append("file", file);

    try {
      await fetch("http://127.0.0.1:8000/chat/files/upload", {
        method: "POST",
        body: form,
      });
    } catch (err) {
      alert(`Error uploading ${file.name}`);
    }
  }

  function switchMode(mode) {
    studyBtn.classList.remove("active");
    quizBtn.classList.remove("active");

    if (mode === "study") {
      studyBtn.classList.add("active");
      quizActive = false;

      addAI("Study mode enabled.");
    } else {
      quizBtn.classList.add("active");
      quizActive = true;

      addAI("Starting quiz...");
      startQuiz();
    }
  }

  function addAI(text) {
    const m = document.createElement("div");
    m.classList.add("message", "ai");
    m.textContent = text;
    chatBox.appendChild(m);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  async function startQuiz() {
    if (quizStarting) return;
    quizStarting = true;

    try {
      const res = await fetch("http://127.0.0.1:8000/quiz/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ num_questions: 2, language: "English" }),
      });
      const data = await res.json();

      activeQuizId = data.quiz_id;
      addAI(`Quiz created (${data.total_questions} questions).`);

      await loadFirstQuestion();
    } finally {
      quizStarting = false;
    }
  }

  async function loadFirstQuestion() {
    const userId = localStorage.getItem("user_id") || "guest";

    const res = await fetch(
      `http://127.0.0.1:8000/quiz/${activeQuizId}/start?user_id=${encodeURIComponent(userId)}`,
    );

    const data = await res.json();
    showQuestion(data);
  }

  function showQuestion(q) {
    currentQuestionId = q.id;

    addAI(q.question);
    currentQuestionOpen = !Array.isArray(q.options) || q.options.length === 0;

    if (!currentQuestionOpen) {
      const box = document.createElement("div");
      q.options.forEach((opt) => {
        const btn = document.createElement("button");
        btn.classList.add("quiz-option");
        btn.textContent = opt;
        btn.onclick = () => {
          addUser(opt);
          sendAnswer(opt);
        };
        box.appendChild(btn);
      });
      chatBox.appendChild(box);
    } else {
      addAI("Type your answer and press Enter.");
    }

    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function addUser(t) {
    const m = document.createElement("div");
    m.classList.add("message", "user");
    m.textContent = t;
    chatBox.appendChild(m);
  }

  async function sendAnswer(answer) {
    const res = await fetch("http://127.0.0.1:8000/quiz/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        quiz_id: activeQuizId,
        question_id: currentQuestionId,
        user_id: localStorage.getItem("user_id") || "guest",
        user_answer: answer,
      }),
    });

    const data = await res.json();

    addAI(data.feedback || (data.correct ? "Correct!" : "Incorrect."));

    if (data.next_question) {
      showQuestion(data.next_question);
    } else if (data.summary) {
      addAI(
        `Quiz finished! Score: ${data.summary.correct}/${data.summary.total}`,
      );
      quizActive = false;
    }
  }
});
