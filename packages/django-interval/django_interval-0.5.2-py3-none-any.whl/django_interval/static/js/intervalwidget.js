document.querySelectorAll(".intervalwidget").forEach(function(element) {
    element.onkeyup = function(element) {
        if (element.target.dataset.intervaluri) {
            fetch(element.target.dataset.intervaluri + "?datestring=" + element.target.value)
                .then(response => response.text())
                .then(data => {
                    nesi = element.target.nextSibling;
                    if (nesi.classList && nesi.classList.contains("interval-help")) {
                        interval_help = nesi;
                    } else {
                        interval_help = document.createElement("div");
                        interval_help.classList.add("interval-help");
                        element.target.insertAdjacentElement("afterend", interval_help)
                    }
                    interval_help.innerHTML = data;
                });
        }
    };
});
