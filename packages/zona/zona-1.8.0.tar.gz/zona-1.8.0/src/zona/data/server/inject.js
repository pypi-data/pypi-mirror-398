(() => {
  // if user at the bottom before reload, scroll to new bottom
  if (localStorage.getItem("wasAtBottom") === "1") {
    localStorage.removeItem("wasAtBottom");
    window.addEventListener("load", () => {
      requestAnimationFrame(() => {
        window.scrollTo(0, document.body.scrollHeight);
      });
    });
  }

  const ws = new WebSocket("__SOCKET_ADDRESS__");
  const tol = __SCROLL_TOLERANCE__;
  ws.onmessage = event => {
    if (event.data === "reload") {
      // store flag if user currently at bottom
      const nearBottom = window.innerHeight + window.scrollY
        >= document.body.scrollHeight - tol;
      if (nearBottom) {
        localStorage.setItem("wasAtBottom", "1");
      }
      location.reload();
    }
  };
})();
