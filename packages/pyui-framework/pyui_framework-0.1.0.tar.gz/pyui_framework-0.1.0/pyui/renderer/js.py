def base_js() -> str:
    return """
    function showAlert() {
        alert("Button clicked!");
    }

    function logMessage(msg) {
        console.log(msg);
    }
    
    function toggleTheme() {
        const body = document.body;
        const current = body.getAttribute("data-theme");

        if (current === "dark") {
            body.setAttribute("data-theme", "light");
        } else {
            body.setAttribute("data-theme", "dark");
        }
    }


   
    function toggleTheme() {
        const body = document.body;
        const current = body.getAttribute("data-theme");
        body.setAttribute("data-theme", current === "dark" ? "light" : "dark");
    }

    function pyuiTrigger(eventId) {
        console.log("PyUI event triggered:", eventId);
        alert("Event triggered: " + eventId + "\\n(Backend not connected yet)");
    }
"""


