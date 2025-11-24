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
  ctx.globalAlpha = 1.0;
  ctx.fillStyle = "rgba(0,191,255,1)";

  for (let p of nodes) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > width) p.vx *= -1;
    if (p.y < 0 || p.y > height) p.vy *= -1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let i = 0; i < nodes.length - 1; i++) {
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

window.addEventListener("DOMContentLoaded", async () => {
  window.addEventListener("resize", resize);
  resize();
  draw();

  const back = document.getElementById("home-btn");
  if (back) back.onclick = () => (window.location.href = "chat.html");

  const params = new URLSearchParams(window.location.search);
  const userId = params.get("user_id") || "guest";

  try {
    const res = await fetch(
      `http://127.0.0.1:8000/users/weak_topics/${encodeURIComponent(userId)}`,
    );

    if (!res.ok) throw new Error("Server error");

    const data = await res.json();

    const summary = data.summary || { attempts: 0, correct: 0, accuracy: 0 };
    const topics = data.user?.topics || [];
    const weakTopics = data.weak_topics || [];

    document.getElementById("avg-score").textContent =
      summary.accuracy.toFixed(1) + "%";

    document.getElementById("completed").textContent = summary.attempts;

    if (topics.length > 0) {
      const sorted = [...topics].sort((a, b) => b.accuracy - a.accuracy);

      document.getElementById("best-topic").textContent = sorted[0].topic;
      document.getElementById("weak-topic").textContent =
        sorted[sorted.length - 1].topic;
    }

    const recBox = document.createElement("div");
    recBox.classList.add("profile-card");
    recBox.innerHTML = `
      <h3>Recommended Focus</h3>
      ${
        weakTopics.length > 0
          ? `<p>You should spend more time on: <strong>${weakTopics.join(
              ", ",
            )}</strong>.</p>`
          : `<p>You are performing evenly across topics.</p>`
      }
    `;
    document.querySelector(".profile-container").appendChild(recBox);

    const tbody = document.getElementById("quiz-history");
    tbody.innerHTML = "";

    topics.forEach((t) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${data.user.joined.split(" ")[0]}</td>
        <td>${t.topic}</td>
        <td>${t.correct}/${t.attempts}</td>
        <td>${t.accuracy.toFixed(1)}%</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Error loading profile:", err);
  }
});
