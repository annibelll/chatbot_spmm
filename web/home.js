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

document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("start");
  const usernameInput = document.getElementById("username");
  const clearBtn = document.getElementById("clear-btn"); // кнопка для очищення бази
  const fileList = document.getElementById("sources-list"); // список файлів (якщо є)

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      const username = usernameInput.value.trim();
      if (!username) {
        alert("Please enter your username.");
        return;
      }

      try {
        const response = await fetch("http://127.0.0.1:8000/users/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ name: username })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const data = await response.json();

        localStorage.setItem("username", data.name);
        localStorage.setItem("user_id", data.user_id);

        window.location.href = "chat.html";
      } catch (error) {
        console.error("Connection error:", error);
        alert("Failed to connect to the server");
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to clear all data?")) return;

      
      if (fileList) fileList.innerHTML = "";

      try {
        const response = await fetch("http://127.0.0.1:8000/clear_embeddings", {
          method: "DELETE"
        });
        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const data = await response.json();
        alert(data.message || "Embedding database cleared.");
      } catch (err) {
        console.error("Failed to clear embeddings:", err);
        alert("Error clearing database.");
      }
    });
  }
});

