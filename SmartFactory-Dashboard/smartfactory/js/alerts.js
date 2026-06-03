/* ================================================================
   SmartFactory Micro-Monitor — Alerts Module
   File: js/alerts.js

   Purpose:
   Manages the alert log panel. Handles adding new alert items
   to the list, updating the event count, and limiting the
   maximum number of visible alerts to keep the panel clean.

   Functions exported (used by sensors.js):
   - addAlert(type, message)

   Elements managed:
   - #alert-list   → the scrollable list of alert items
   - #alert-count  → event count shown in panel header
   ================================================================ */


/* Maximum number of alerts to show in the panel at once */
const MAX_ALERTS = 8;


/**
 * addAlert
 * Creates a new alert item and prepends it to the top of the
 * alert list. Removes the oldest item if the list exceeds
 * MAX_ALERTS. Updates the event count display.
 *
 * @param {string} type    - Alert severity: 'good' | 'warn' | 'bad'
 * @param {string} message - Human-readable alert description
 */
function addAlert(type, message) {
  const list = document.getElementById('alert-list');
  if (!list) return;

  /* Get current timestamp formatted as HH:MM:SS */
  const now = new Date().toLocaleTimeString('en-IE').toUpperCase();

  /* Build the alert item HTML element */
  const item = document.createElement('div');
  item.className = 'alert-item';
  item.innerHTML = `
    <div class="alert-dot ${type}"></div>
    <div class="alert-body">
      <div class="alert-msg">${message}</div>
      <div class="alert-time">TODAY ${now}</div>
    </div>
  `;

  /* Prepend to top of list so newest alerts appear first */
  list.insertBefore(item, list.firstChild);

  /* Remove oldest alert if we've exceeded the maximum */
  if (list.children.length > MAX_ALERTS) {
    list.removeChild(list.lastChild);
  }

  /* Update the event count badge in the panel header */
  updateAlertCount();
}


/**
 * updateAlertCount
 * Updates the alert count text displayed in the panel header.
 * Called after every addAlert() operation.
 */
function updateAlertCount() {
  const list = document.getElementById('alert-list');
  const countEl = document.getElementById('alert-count');

  if (list && countEl) {
    const count = list.children.length;
    countEl.textContent = count + (count === 1 ? ' EVENT' : ' EVENTS');
  }
}


/* Set the initial count based on pre-loaded HTML alerts */
updateAlertCount();
