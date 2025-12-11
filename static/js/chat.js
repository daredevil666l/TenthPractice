
document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.querySelector(".chat-layout");
    if (!chatContainer) return;

    const roomId = chatContainer.getAttribute("data-room-id");
    const messagesEl = document.getElementById("chat-messages");

    // Optional: авто-прокрутка вниз
    if (messagesEl) {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
});
