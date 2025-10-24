function showLoader() {
    const loader = document.getElementById("loader-overlay");
    loader.style.display = "flex";

    // Force a repaint so the loader appears immediately
    loader.offsetHeight;
}

function hideLoader() {
    document.getElementById("loader-overlay").style.display = "none";
}

window.onload = function () {
    console.log("✅ DOM fully loaded!");

    const button = document.getElementById("getAnswerBtn");
    const speakBtn = document.getElementById("speakBtn");

    console.log("Speak button found?", speakBtn !== null);

    if (button) {
        button.addEventListener("click", get_answer_by_question);
    } else {
        console.error("❌ getAnswerBtn NOT found!");
    }

    if (speakBtn) {
        speakBtn.addEventListener("click", text_to_speech);
        console.log("🎯 Speak button listener attached!");
    } else {
        console.error("❌ Speak button NOT found in DOM!");
    }
};

function get_answer_by_question() {
    const question = document.getElementById("userInput").value;
    const data = { content: question };

    showLoader();

    fetch("/get-by-question", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const response_space = document.getElementById("output");
        response_space.innerText = data.content;
    })
    .catch(err => console.error("Fetch error:", err))
    .finally(() => hideLoader());
}

function text_to_speech() {
    console.log("🎤 Speak button clicked!");

    const text = document.getElementById("output").innerText.trim();
    if (!text) {
        console.warn("⚠️ No text found to speak!");
        return;
    }

    showLoader();

    const data = { content: text };

    fetch("/text-to-speech", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log("🎧 Received audio:", data);
        const audio = new Audio(data.filename);
        audio.play().then(() => {
            console.log("✅ Audio playback started");
        }).catch((error) => {
            console.error("❌ Error playing audio:", error);
        });
    })
    .catch(err => console.error("Fetch error:", err))
    .finally(() => hideLoader());
}
