const btn = document.getElementById('button');
const heading = document.getElementById('event-type-desc');
btn.addEventListener('click', () => {
  setTimeout(() => {heading.scrollIntoView({behavior: "smooth"})}, 2000);
  setTimeout(() => heading.focus(), 1000);
});