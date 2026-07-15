/* strategy.js
   Tyre compound definitions and lap-time / degradation model.
   Exposed on window.Strategy so other scripts (loaded as plain <script> tags,
   no bundler) can use it. */

(function () {
  const COMPOUNDS = {
    soft:   { label: "SOFT",   short: "S", pace: 0.0, durability: 18, color: "#E8121C" },
    medium: { label: "MEDIUM", short: "M", pace: 0.6, durability: 30, color: "#C6A15B" },
    hard:   { label: "HARD",   short: "H", pace: 1.2, durability: 45, color: "#848B9C" },
    wet:    { label: "WET",    short: "W", pace: 0.3, durability: 35, color: "#2FD3E0" },
  };

  const BASE_LAP = 92.0;      // seconds, a fictional reference lap time
  const PIT_LOSS = 22.0;      // seconds lost in the pit lane
  const PUNCTURE_WEAR_THRESHOLD = 0.95;

  /**
   * Returns the wear fraction (0 -> 1+) for a compound at a given tyre age.
   */
  function wearFraction(compound, tyreAge) {
    const durability = COMPOUNDS[compound].durability;
    return Math.pow(tyreAge / durability, 2.2);
  }

  /**
   * Core lap-time model, matches the degradation curve from the design doc:
   * wearPenalty grows with the square-ish power of age, plus a "tyre cliff"
   * once wear crosses 90%, plus a flat penalty for running slicks in the wet.
   */
  function calculateLapTime(compound, tyreAge, weather) {
    const wear = wearFraction(compound, tyreAge);
    const wearPenalty = wear * 4.0;
    const compoundDelta = COMPOUNDS[compound].pace;
    const weatherPenalty = weather === "wet" && compound !== "wet" ? 8.0 : 0;
    const cliffPenalty = wear > 0.9 ? (wear - 0.9) * 25 : 0;
    // small natural variance so races don't feel identical
    const variance = (Math.random() - 0.5) * 0.6;

    return BASE_LAP + compoundDelta + wearPenalty + weatherPenalty + cliffPenalty + variance;
  }

  /**
   * Chance (0-1) of a puncture this lap, rises sharply once past the cliff.
   */
  function punctureChance(compound, tyreAge) {
    const wear = wearFraction(compound, tyreAge);
    if (wear < PUNCTURE_WEAR_THRESHOLD) return 0;
    return Math.min(0.5, (wear - PUNCTURE_WEAR_THRESHOLD) * 3);
  }

  window.Strategy = {
    COMPOUNDS,
    BASE_LAP,
    PIT_LOSS,
    wearFraction,
    calculateLapTime,
    punctureChance,
  };
})();
