window.addEventListener('load', () => {
  // Wait for the video element to be available
  const checkVideo = setInterval(() => {
    const video = document.querySelector('video');
    if (video) {
      clearInterval(checkVideo);
      initializeFrameCapture(video);
    }
  }, 500);
});

/**
 * Initializes frame capture and overlay logic.
 * @param {HTMLVideoElement} video - The video element on the page.
 */
function initializeFrameCapture(video) {
  console.log('Video element found. Initializing frame capture...');

  // Create an off-screen canvas for frame capture
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');

  // Adjust canvas dimensions once video metadata is loaded
  video.addEventListener('loadedmetadata', () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    console.log('Canvas size set to:', canvas.width, canvas.height);
    updateOverlayPosition();
  });

  // Create an overlay container for drawing purposes
  const overlayContainer = document.createElement('div');
  // Set the overlay container's ID for easy reference
  overlayContainer.id = 'card-overlay-container';
  // This setting makes the overlay container “positioned” independently of the normal document flow.
  overlayContainer.style.position = 'absolute';
  // This setting tells the browser that the overlay container should ignore mouse events such as clicks, hovers, and drags. (can interact with the overlay)
  overlayContainer.style.pointerEvents = 'none';
  // The z-index property controls the stacking order of elements that overlap. A higher value means the element appears on top of those with a lower value.
  overlayContainer.style.zIndex = 9999;

  // Add red border to the overlay container (if you prefer the border via the overlay)
  overlayContainer.style.border = '2px solid red';
  document.body.appendChild(overlayContainer);

  // Function to update the overlay container's position and size
  function updateOverlayPosition() {
    // Use getBoundingClientRect to account for padding and margins
    const rect = video.getBoundingClientRect();
    overlayContainer.style.top = rect.top + 'px';
    overlayContainer.style.left = rect.left + 'px';
    overlayContainer.style.width = rect.width + 'px';
    overlayContainer.style.height = rect.height + 'px';
  }

  // Listen for events that may change layout (fullscreen changes, window resize)
  document.addEventListener('fullscreenchange', updateOverlayPosition);

  // Start capturing frames periodically
  setInterval(() => {
    if (video.paused || video.ended) return;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // For demonstration, convert the frame to an image URL (using PNG for quality)
    const frameDataURL = canvas.toDataURL('image/jpeg', 0.8);
    console.log('Captured frame:', frameDataURL);

    // Simulate detection by drawing a dummy rectangle overlay
    // simulateOverlayDetection(overlayContainer);

  }, 1000); // Capture one frame every second
}
