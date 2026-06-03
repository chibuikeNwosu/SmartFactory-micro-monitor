/* ================================================================
   SmartFactory Micro-Monitor — Clock Module
   File: js/clock.js

   Purpose:
   Updates the real-time clock in the navigation bar and the
   "Last Updated" timestamp in the compliance banner every second.

   Elements updated:
   - #clock        → top navigation bar time display
   - #last-update  → compliance banner last updated field
   ================================================================ */


/**
 * updateClock
 * Gets the current time and updates both clock display elements.
 * Called immediately on load and then every 1000ms via setInterval.
 */
function updateClock() {
  const now = new Date();

  // Format as HH:MM:SS in Irish locale (24-hour format)
  const timeString = now.toLocaleTimeString('en-IE');

  // Update the navigation bar clock
  const clockEl = document.getElementById('clock');
  if (clockEl) {
    clockEl.textContent = timeString;
  }

  // Update the "Last Updated" field in the compliance banner
  const lastUpdateEl = document.getElementById('last-update');
  if (lastUpdateEl) {
    lastUpdateEl.textContent = timeString;
  }
}

// Run immediately so the clock shows on page load without delay
updateClock();

// Then update every second (1000 milliseconds)
setInterval(updateClock, 1000);
