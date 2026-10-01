/* flooding.js
   Randomized flood system for the tunnels. Tunnels start dry and have a
   small, rising chance of flooding as the descent goes on. Once flooded,
   there is a chance each turn that the water drains away again. */

(function () {
  const TOTAL_DEPTH = 50; // blocks from the surface to the Deep Vein

  /** Probability the tunnel floods THIS turn, given the current depth. */
  function floodStartProbability(currentDepth) {
    const progress = currentDepth / TOTAL_DEPTH;
    if (progress < 0.15) return 0.02;
    if (progress > 0.9) return 0.03;
    return 0.06 + 0.05 * Math.sin(progress * Math.PI);
  }

  function drainProbability() {
    return 0.18;
  }

  /**
   * Rolls the water level forward by one turn. Returns the new state plus a
   * flag saying whether it changed this turn (for UI callouts).
   */
  function rollWater(currentWater, currentDepth) {
    if (currentWater === "dry") {
      if (Math.random() < floodStartProbability(currentDepth)) {
        return { water: "flooded", changed: true };
      }
      return { water: "dry", changed: false };
    }
    if (Math.random() < drainProbability()) {
      return { water: "dry", changed: true };
    }
    return { water: "flooded", changed: false };
  }

  /** Rough flood-risk percentage over the next `lookahead` blocks (informational). */
  function forecast(currentWater, currentDepth, lookahead) {
    if (currentWater === "flooded") return 100;
    let pDry = 1;
    for (let i = 0; i < lookahead; i++) {
      pDry *= 1 - floodStartProbability(currentDepth + i);
    }
    return Math.round((1 - pDry) * 100);
  }

  window.Flooding = { rollWater, forecast, TOTAL_DEPTH };
})();
