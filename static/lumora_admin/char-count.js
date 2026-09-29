/*
 * Lumora Admin — live character counter.
 *
 * Every text field with an editorial limit (`maxlength` below 250; larger
 * values are framework defaults such as Wagtail's 255-character page title)
 * gets a "used / limit" counter underneath, so editors can see how much room
 * the design leaves. Fields added later (new StreamField blocks, inline panel
 * rows) are picked up automatically.
 */
(() => {
  const MAX_SHOWN = 250;
  const SELECTOR = [
    'input[maxlength]:not([type="hidden"]):not([type="url"]):not([type="email"]):not([type="number"]):not([type="search"])',
    "textarea[maxlength]",
  ].join(",");
  let counterId = 0;

  function enhance(field) {
    if (field.dataset.charCount) return;
    const limit = Number(field.getAttribute("maxlength"));
    if (!limit || limit >= MAX_SHOWN) return;
    field.dataset.charCount = "on";

    const counter = document.createElement("div");
    counter.className = "lumora-char-count";
    counter.id = `lumora-char-count-${(counterId += 1)}`;
    field.setAttribute(
      "aria-describedby",
      [field.getAttribute("aria-describedby"), counter.id].filter(Boolean).join(" "),
    );
    field.insertAdjacentElement("afterend", counter);

    const update = () => {
      const used = field.value.length;
      counter.textContent = `${used} / ${limit} characters`;
      counter.dataset.state = used > limit ? "over" : used >= limit * 0.9 ? "near" : "";
    };
    field.addEventListener("input", update);
    update();
  }

  function scan(root) {
    if (root.matches?.(SELECTOR)) enhance(root);
    root.querySelectorAll?.(SELECTOR).forEach(enhance);
  }

  const start = () => {
    scan(document);
    new MutationObserver((mutations) => {
      mutations.forEach((mutation) =>
        mutation.addedNodes.forEach((node) => node.nodeType === Node.ELEMENT_NODE && scan(node)),
      );
    }).observe(document.body, { childList: true, subtree: true });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
