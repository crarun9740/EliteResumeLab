const temp = document.querySelectorAll(".img");
const choosetemp = document.querySelector(".last-btn1");
console.log(temp);
temp.forEach((e) => {
  e.addEventListener("click", (e) => {
    e.preventDefault();
    window.location = "";
  });
});
