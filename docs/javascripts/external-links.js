// Open all external links in a new window/tab
document.addEventListener("DOMContentLoaded", function () {
  document.addEventListener("click", function (e) {
    var link = e.target.closest("a");
    if (link && link.hostname && link.hostname !== window.location.hostname) {
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noopener noreferrer");
    }
  });
});
