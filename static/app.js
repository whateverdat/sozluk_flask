// Dark Mode https://www.youtube.com/watch?v=wodWDIdV9BY&ab_channel=KevinPowell
darkMode = localStorage.getItem("darkMode");
const darkModeToggle = document.querySelector("#dark-mode-toggle");
const navbar = document.getElementById("navbar")

const enableDarkMode = () => {

    // Alter style
    navbar.classList.add("navbar-dark");
    navbar.classList.add("bg-dark");
    document.body.classList.add("dark");

    // Store selection
    localStorage.setItem("darkMode", "enabled")
}
const disableDarkMode = () => {

    // Alter style
    navbar.classList.remove("navbar-dark");
    navbar.classList.remove("bg-dark");
    document.body.classList.remove("dark");
    
    // Store selection
    localStorage.removeItem("darkMode")
}

if (darkMode === "enabled") {
    enableDarkMode();
}

darkModeToggle.addEventListener("click", () => {
    darkMode = localStorage.getItem("darkMode");
    if (darkMode !== 'enabled') {
        enableDarkMode();
    } else {
        disableDarkMode();
    }
});
