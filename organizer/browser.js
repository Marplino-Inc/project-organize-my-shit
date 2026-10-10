// NiceGUI reconnects and reloads after a local server restart. Use the browser's
// native warning if that reload would discard an edited project/task form.
for (const eventName of ['input', 'change', 'click']) {
  document.addEventListener(eventName, event => {
    const editor = event.target.closest?.('.item-editor');
    if (editor) editor.dataset.unsaved = 'true';
  }, true);
}
window.addEventListener('beforeunload', event => {
  const editing = [...document.querySelectorAll('.item-editor[data-unsaved="true"]')]
    .some(editor => editor.getClientRects().length > 0);
  if (editing) {
    event.preventDefault();
    event.returnValue = '';
  }
});
