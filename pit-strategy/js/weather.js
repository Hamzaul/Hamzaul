/* weather.js
   Randomized weather system. Weather starts dry and has a small, rising
   chance of turning wet as the race goes on. Once wet, it has a chance to
   dry back out. */

(function () {
  const TOTAL_LAPS = 50;

  /**
   * Probability that rain starts THIS turn, given the current lap.
   * Rises through the middle of the race, tapers near the very end.
   */
  function rainStartProbability(currentLap) {
    const progress = currentLap / TOTAL_LAPS;
    if (progress < 0.15) return 0.02;
    if (progress > 0.9) return 0.03;
    return 0.06 + 0.05 * Math.sin(progress * Math.PI);
  }

  function dryOutProbability() {
    return 0.18;
  }

  /**
   * Rolls the weather forward by one turn. Returns the new weather state
   * plus a flag saying whether it changed this turn (for UI callouts).
   */
  function rollWeather(currentWeather, currentLap) {
    if (currentWeather === "dry") {
      if (Math.random() < rainStartProbability(currentLap)) {
        return { weather: "wet", changed: true };
      }
      return { weather: "dry", changed: false };
    } else {
      if (Math.random() < dryOutProbability()) {
        return { weather: "dry", changed: true };
      }
      return { weather: "wet", changed: false };
    }
  }

  /**
   * A rough "forecast" percentage shown on the HUD - chance of rain
   * within the next `lookahead` laps, purely informational/flavour.
   */
  function forecast(currentWeather, currentLap, lookahead) {
    if (currentWeather === "wet") return 100;
    let pNoRain = 1;
    for (let i = 0; i < lookahead; i++) {
      pNoRain *= 1 - rainStartProbability(currentLap + i);
    }
    return Math.round((1 - pNoRain) * 100);
  }

  window.Weather = { rollWeather, forecast, TOTAL_LAPS };
})();
