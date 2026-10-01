/* tools.js
   Pickaxe tiers and the tool-wear / dig-time model.
   Exposed on window.Tools so other scripts (plain <script> tags, no bundler)
   can use it.

   Tier trade-offs are relative to each other inside this simulation:
     gold    - fastest, wears out quickly
     iron    - balanced
     diamond - steadier, lasts longest
     aqua    - built for flooded tunnels */

(function () {
  const TOOLS = {
    gold:    { label: "GOLD",    short: "G", pace: 0.0, durability: 18, color: "#FAC846", blurb: "fast · brittle" },
    iron:    { label: "IRON",    short: "I", pace: 0.6, durability: 30, color: "#D8DBD8", blurb: "balanced" },
    diamond: { label: "DIAMOND", short: "D", pace: 1.2, durability: 45, color: "#5DECEC", blurb: "steady · long life" },
    aqua:    { label: "AQUA",    short: "A", pace: 0.3, durability: 35, color: "#3C8DFF", blurb: "for flooded tunnels" },
  };

  const BASE_TIME = 92.0;    // seconds to dig one block with a fresh tool (fictional reference)
  const CRAFT_LOSS = 22.0;   // seconds lost walking back to the crafting table
  const BREAK_WEAR_THRESHOLD = 0.95;

  /** Wear fraction (0 -> 1+) for a tool at a given use count. */
  function wearFraction(tool, uses) {
    const durability = TOOLS[tool].durability;
    return Math.pow(uses / durability, 2.2);
  }

  /**
   * Core dig-time model: wear grows with a power curve of use, plus a
   * "cracking" cliff once wear passes 90%, plus a flat penalty for digging
   * a flooded tunnel without the aqua pick.
   */
  function digTime(tool, uses, water) {
    const wear = wearFraction(tool, uses);
    const wearPenalty = wear * 4.0;
    const toolDelta = TOOLS[tool].pace;
    const waterPenalty = water === "flooded" && tool !== "aqua" ? 8.0 : 0;
    const cliffPenalty = wear > 0.9 ? (wear - 0.9) * 25 : 0;
    const variance = (Math.random() - 0.5) * 0.6; // so runs don't feel identical

    return BASE_TIME + toolDelta + wearPenalty + waterPenalty + cliffPenalty + variance;
  }

  /** Chance (0-1) the pickaxe cracks this block; rises sharply past the cliff. */
  function breakChance(tool, uses) {
    const wear = wearFraction(tool, uses);
    if (wear < BREAK_WEAR_THRESHOLD) return 0;
    return Math.min(0.5, (wear - BREAK_WEAR_THRESHOLD) * 3);
  }

  window.Tools = { TOOLS, BASE_TIME, CRAFT_LOSS, wearFraction, digTime, breakChance };
})();
