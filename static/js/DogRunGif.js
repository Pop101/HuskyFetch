function toggleImage() {
    $('#image').toggleClass('hidden');
}

function toggleTimeout() {
    setTimeout(toggleImage, 2500);
}

function toggleButton() {
    toggleImage();
    toggleTimeout();
}

$('#button').click(toggleButton);

