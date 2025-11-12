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

window.addEventListener("DOMContentLoaded", async () => {
  const homeBtn = document.getElementById("home-btn");
  if (homeBtn) homeBtn.onclick = () => window.location.href = "index.html";

  const studyBtn = document.getElementById("study-mode");
  const quizBtn = document.getElementById("quiz-mode");
  if (studyBtn && quizBtn) {
    studyBtn.onclick = () => switchMode("study");
    quizBtn.onclick = () => switchMode("quiz");
  }

 
  const profileBtn = document.getElementById("profile-btn");
  if (profileBtn) {
    profileBtn.addEventListener("click", () => {
      const userId = localStorage.getItem("user_id") || "guest";
      window.location.href = `profile.html?user_id=${encodeURIComponent(userId)}`;
    });
  }

  const sendBtn = document.getElementById("send-btn");
  const input = document.getElementById("user-input");
  const chatBox = document.getElementById("chat-box");
  const fileInput = document.getElementById("file-upload");
  const sourcesList = document.getElementById("sources-list");
  const deleteAllBtn = document.getElementById("delete-all");

  if (sendBtn) sendBtn.onclick = sendMessage;
  if (input) input.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });
  await loadExistingFiles();

  if (fileInput && sourcesList) {
    fileInput.addEventListener("change", async () => {
      const files = Array.from(fileInput.files);
      for (const file of files) {
        await uploadFile(file);
      }
      await loadExistingFiles();
      fileInput.value = "";
    });
  }

  if (deleteAllBtn) {
    deleteAllBtn.onclick = async () => {
      if (!confirm("Are you sure you want to delete all files?")) return;
      try {
        const res = await fetch("http://127.0.0.1:8000/chat/files/clear_all", {
          method: "DELETE"
        });
        if (!res.ok) throw new Error(`Error: ${res.status}`);
        sourcesList.innerHTML = "";
        alert("All files and embeddings deleted.");
      } catch (err) {
        console.error(err);
        alert("Failed to delete all files ❌");
      }
    };
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    const userMsg = document.createElement("div");
    userMsg.classList.add("message", "user");
    userMsg.textContent = text;
    chatBox.appendChild(userMsg);
    input.value = "";

    const aiMsg = document.createElement("div");
    aiMsg.classList.add("message", "ai");
    aiMsg.textContent = "Analyzing your materials... 🤖";
    chatBox.appendChild(aiMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const response = await fetch("http://127.0.0.1:8000/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          language: "en"
        })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(`Error: ${response.status}`);
      aiMsg.textContent = data.answer || "No response from AI.";
    } catch (error) {
      console.error(error);
      aiMsg.textContent = "Failed to connect to server ❌";
    }
  }

  async function loadExistingFiles() {
    try {
      const res = await fetch("http://127.0.0.1:8000/chat/files");
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      const data = await res.json();
      sourcesList.innerHTML = "";
      data.files.forEach(filename => {
        const li = document.createElement("li");
        const fileName = document.createElement("span");
        fileName.textContent = filename;
        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "✖";
        deleteBtn.classList.add("delete-btn");
        deleteBtn.onclick = async () => {
          li.remove();
          try {
            const resp = await fetch(
              `http://127.0.0.1:8000/chat/files/${encodeURIComponent(filename)}`,
              { method: "DELETE" }
            );
            if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
          } catch (err) {
            console.error("Failed to delete file:", err);
          }
        };
        li.appendChild(fileName);
        li.appendChild(deleteBtn);
        sourcesList.appendChild(li);
      });
    } catch (err) {
      console.error("Error loading files:", err);
    }
  }

  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://127.0.0.1:8000/chat/files/upload", {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    } catch (err) {
      console.error("File upload error:", err);
      alert(`Error uploading ${file.name}`);
    }
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
    if (mode === "quiz") startQuiz();
  }

  let activeQuizId = null;
  let currentQuestionId = null;

  async function startQuiz() {
    const msg = document.createElement("div");
    msg.classList.add("message", "ai");
    msg.textContent = "Creating a quiz... ⏳";
    chatBox.appendChild(msg);

    try {
      const res = await fetch("http://127.0.0.1:8000/quiz/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          num_questions: 5,
          language: "en"
        })
      });

      if (!res.ok) throw new Error(`Error: ${res.status}`);
      const data = await res.json();
      activeQuizId = data.quiz_id;
      msg.textContent = `🧩 Quiz created! Total questions: ${data.total_questions}.`;

      await loadFirstQuestion();
    } catch (err) {
      console.error(err);
      msg.textContent = "Failed to create quiz ❌";
    }
  }

  async function loadFirstQuestion() {
    const userId = localStorage.getItem("user_id") || "guest";

    try {
      const res = await fetch(`http://127.0.0.1:8000/quiz/${activeQuizId}/start?user_id=${encodeURIComponent(userId)}`);
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      const data = await res.json();

      showQuestion(data);
    } catch (err) {
      console.error(err);
      const msg = document.createElement("div");
      msg.classList.add("message", "ai");
      msg.textContent = "Could not load first question ❌";
      chatBox.appendChild(msg);
    }
  }

  function showQuestion(q) {
  currentQuestionId = q.id;
  const qBox = document.createElement("div");
  qBox.classList.add("message", "ai");
  qBox.innerHTML = `<strong>${q.question}</strong>`;


  if (q.options && q.options.length > 0) {
    const optionsContainer = document.createElement("div");
    q.options.forEach(opt => {
      const btn = document.createElement("button");
      btn.classList.add("quiz-option");
      btn.textContent = opt;
      btn.onclick = () => sendAnswer(opt);
      optionsContainer.appendChild(btn);
    });
    qBox.appendChild(optionsContainer);
  } else {
    
    const msg = document.createElement("div");
    msg.classList.add("message", "ai");
    msg.textContent = "Type your answer in the main chat input and press Enter ⌨️";
    chatBox.appendChild(msg);

  
    const oldHandler = input.onkeypress;
    input.onkeypress = async (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const userAnswer = input.value.trim();
        if (!userAnswer) return;
        input.value = "";
        input.onkeypress = oldHandler; 
        await sendAnswer(userAnswer);
      }
    };
  }

  chatBox.appendChild(qBox);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendAnswer(selectedOption) {
  try {
    const res = await fetch("http://127.0.0.1:8000/quiz/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: currentQuestionId,
        user_answer: selectedOption
      })
    });

    if (!res.ok) throw new Error(`Error: ${res.status}`);
    const data = await res.json();

    const feedback = document.createElement("div");
    feedback.classList.add("message", "ai");
    feedback.textContent = data.feedback || (data.correct ? "✅ Correct!" : "❌ Incorrect.");
    chatBox.appendChild(feedback);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (data.next_question) {
      showQuestion(data.next_question);
    } else if (data.summary) {
      const summary = document.createElement("div");
      summary.classList.add("message", "ai");
      summary.textContent = `🏁 Quiz complete! Your score: ${data.summary.score}/${data.summary.total}`;
      chatBox.appendChild(summary);
    }
  } catch (err) {
    console.error(err);
  }
}

});
