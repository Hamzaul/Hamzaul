/* ui.js
   All DOM reads/writes live here so game.js can stay focused on state. */

(function () {
  const el = (id) => document.getElementById(id);

  function fmtTime(seconds) {
    const sign = seconds < 0 ? "-" : "+";
    const abs = Math.abs(seconds);
    return `${sign}${abs.toFixed(1)}s`;
  }

  function setWear(pctEl, barEl, wearFraction) {
    const pct = Math.min(100, Math.round(wearFraction * 100));
    pctEl.textContent = `${pct}%`;
    barEl.style.width = `${pct}%`;
    barEl.classList.remove("wear-ok", "wear-warn", "wear-danger");
    if (pct < 55) barEl.classList.add("wear-ok");
    else if (pct < 90) barEl.classList.add("wear-warn");
    else barEl.classList.add("wear-danger");
  }

  function renderHUD(state, Strategy, Weather) {
    el("hud-lap").textContent = `${state.lap} / ${Weather.TOTAL_LAPS}`;
    el("hud-position").textContent = `P${state.player.position}`;

    const compound = Strategy.COMPOUNDS[state.player.compound];
    const badge = el("hud-tyre-badge");
    badge.textContent = compound.short;
    badge.style.borderColor = compound.color;
    badge.style.color = compound.color;
    el("hud-tyre-name").textContent = compound.label;

    const wear = Strategy.wearFraction(state.player.compound, state.player.tyreAge);
    setWear(el("hud-wear-pct"), el("hud-wear-bar"), wear);

    const leaderTime = state.field.length ? Math.min(...state.field.map((r) => r.totalTime)) : 0;
    const gap = state.player.totalTime - leaderTime;
    el("hud-gap").textContent = state.player.position === 1 ? "LEADER" : fmtTime(gap);

    const rainPct = Weather.forecast(state.weather, state.lap, 10);
    el("hud-weather").textContent =
      state.weather === "wet" ? "RAIN — TRACK WET" : `${rainPct}% rain risk (10 laps)`;
    el("hud-weather").classList.toggle("wet-active", state.weather === "wet");

    const rivalsInWindow = state.field.filter((r) => {
      const w = Strategy.wearFraction(r.compound, r.tyreAge);
      return w > 0.55 && w < 0.85 && !r.out;
    }).length;
    el("hud-rival-window").textContent = `${rivalsInWindow} of ${state.field.length} rivals in pit window`;

    el("hud-pitstops").textContent = state.player.pitStops;
  }

  function renderStandings(state, Strategy) {
    const rows = [
      { name: "YOU", totalTime: state.player.totalTime, isPlayer: true, compound: state.player.compound },
      ...state.field.map((r) => ({ name: r.name, totalTime: r.totalTime, isPlayer: false, compound: r.compound, out: r.out })),
    ].sort((a, b) => a.totalTime - b.totalTime);

    const leaderTime = rows[0].totalTime;
    const tbody = el("standings-body");
    tbody.innerHTML = "";
    rows.forEach((row, i) => {
      const tr = document.createElement("tr");
      if (row.isPlayer) tr.classList.add("standings-player");
      const compound = Strategy.COMPOUNDS[row.compound];
      const gap = i === 0 ? "—" : fmtTime(row.totalTime - leaderTime);
      tr.innerHTML = `
        <td>P${i + 1}</td>
        <td>${row.name}</td>
        <td><span class="tyre-chip" style="border-color:${compound.color};color:${compound.color}">${compound.short}</span></td>
        <td>${gap}</td>
      `;
      tbody.appendChild(tr);
    });

    return rows.findIndex((r) => r.isPlayer) + 1;
  }

  function log(message, cls) {
    const logEl = el("race-log");
    const line = document.createElement("div");
    line.className = `log-line${cls ? " " + cls : ""}`;
    line.textContent = message;
    logEl.prepend(line);
    while (logEl.children.length > 40) logEl.removeChild(logEl.lastChild);
  }

  function showCompoundModal(onPick, weather) {
    const modal = el("compound-modal");
    modal.classList.remove("hidden");
    const buttons = modal.querySelectorAll("[data-compound]");
    buttons.forEach((btn) => {
      btn.onclick = () => {
        modal.classList.add("hidden");
        onPick(btn.getAttribute("data-compound"));
      };
    });
    el("compound-cancel").onclick = () => modal.classList.add("hidden");
    el("wet-hint").classList.toggle("hidden", weather !== "wet");
  }

  function setActionsEnabled(enabled) {
    el("btn-pit").disabled = !enabled;
    el("btn-stay").disabled = !enabled;
  }

  function showResults(finalPosition, points, isNewHighScore, highScore) {
    const overlay = el("results-overlay");
    overlay.classList.remove("hidden");
    el("results-position").textContent = `P${finalPosition}`;
    el("results-points").textContent = `${points} PTS`;
    el("results-highscore").textContent = `BEST: P${highScore.position} · ${highScore.points} PTS`;
    el("results-badge").textContent = isNewHighScore ? "NEW BEST RESULT" : "";
  }

  function hideResults() {
    el("results-overlay").classList.add("hidden");
  }

  window.UI = {
    el,
    renderHUD,
    renderStandings,
    log,
    showCompoundModal,
    setActionsEnabled,
    showResults,
    hideResults,
  };
})();
