/* ================================================================
   SmartFactory Micro-Monitor — Modal Module
   File: js/modal.js

   Purpose:
   Controls the Report Generation modal popup.
   Handles opening, closing, and clicking outside to dismiss.

   When the Raspberry Pi is connected:
   Replace the showReportModal() function with a fetch() call
   to trigger real PDF generation on the Pi:

     fetch('http://<PI_IP>:5000/api/generate-report', { method: 'POST' })
       .then(res => res.blob())
       .then(blob => {
         const url = URL.createObjectURL(blob);
         const a = document.createElement('a');
         a.href = url;
         a.download = 'SmartFactory_Report.pdf';
         a.click();
       });

   Elements managed:
   - #modal  → the modal overlay div
   ================================================================ */


/**
 * showReportModal
 * Opens the report generation modal by adding the 'open' class.
 * Called by the Generate Report button in index.html.
 *
 * When Pi is connected, this function should trigger the
 * Flask /api/generate-report endpoint before showing the modal.
 */
function showReportModal() {
  const modal = document.getElementById('modal');
  if (modal) {
    modal.classList.add('open');
  }
}


/**
 * closeModal
 * Closes the modal by removing the 'open' class.
 * Called by the Close button inside the modal.
 */
function closeModal() {
  const modal = document.getElementById('modal');
  if (modal) {
    modal.classList.remove('open');
  }
}


/* ── CLICK OUTSIDE TO DISMISS ───────────────────────────────────
   If the user clicks the dark overlay (outside the modal card),
   the modal is dismissed. This checks that the click target
   is the overlay itself, not any element inside the modal.
   ─────────────────────────────────────────────────────────── */
const modalOverlay = document.getElementById('modal');
if (modalOverlay) {
  modalOverlay.addEventListener('click', function (event) {
    /* Only close if the click was directly on the overlay, not inside the modal card */
    if (event.target === this) {
      closeModal();
    }
  });
}


/* ── KEYBOARD DISMISS ───────────────────────────────────────────
   Allow pressing Escape to close the modal.
   ─────────────────────────────────────────────────────────── */
document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape') {
    closeModal();
  }
});
